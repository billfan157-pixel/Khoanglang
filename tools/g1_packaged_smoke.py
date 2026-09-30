"""Capture a stationary packaged school opening using Unreal's native frame clock.

No keyboard/mouse injection, UI automation, autoplay or editor access. Default
mode only records a launch plan. --execute is required to start the owned game.
CSV frames drive screenshots and graceful engine exit; wall time never stands
in for measured frame time. This cannot qualify the complete G1 or campaign.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import statistics
import struct
import subprocess
import time
import uuid

from verify_release import ROOT, package_digest, sha, write_json

EXPECTED_MAP = "/Game/KhoangLang/Production/G1Canon/Lvl_KL_SchoolSlice"
ENGINE = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Epic Games/UE_5.8"
SCALABILITY = [f"sg.{name}Quality 0" for name in
               ("ViewDistance", "AntiAliasing", "Shadow", "GlobalIllumination",
                "Reflection", "PostProcess", "Texture", "Effects", "Foliage")]
START_COMMANDS = SCALABILITY + ["r.ScreenPercentage 100", "r.VSync 0", "t.MaxFPS 0",
                                "csv.CompressionMode 0", "csv.ForceExit 0"]
# Native scheduling and actual checkpoint opening captures were inspected.
# A new machine/run still requires inspection of its original pixels.
# Everything below finishes before the 600-frame statistics warmup ends.
CAPTURE_SCHEDULE = "resize-before-slate-capture-v2"
FRAME_COMMANDS = [
    "240:r.SetRes 1280x720w",
    "280:Shot filename=g1_scene_1280x720.png -nosuffix",
    "300:Shot SHOWUI filename=g1_opening_1280x720.png -nosuffix",
    "360:r.SetRes 1920x1080w",
    "390:Shot SHOWUI filename=g1_opening_1920x1080.png -nosuffix",
    "450:r.SetRes 1280x720w",
]


class ArtifactRecheckFailed(RuntimeError):
    """A failed final invariant must override a previously computed exit code."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def native_sources(engine: Path) -> dict:
    sources = {
        "csv": ("Engine/Source/Runtime/Core/Private/ProfilingDebugging/CsvProfiler.cpp",
                ["csvCaptureFrames=", "-csvExecCmds=", "ExitAfterCsvProfiling",
                 "PhysicalUsedMB", "FrameTime", 'TEXT("csv.ForceExit")']),
        "frame_dispatch": ("Engine/Source/Runtime/Launch/Private/LaunchEngineLoop.cpp",
                           ["GetFrameExecCommands", "LocalPlayer->Exec"]),
        "screenshot": ("Engine/Source/Runtime/Engine/Private/GameViewportClient.cpp",
                       ["HandleScreenshotCommand", 'TEXT("SHOWUI")', 'TEXT("nosuffix")',
                        "FSlateApplication::Get().TakeScreenshot"]),
        "slate_capture": ("Engine/Source/Runtime/Slate/Private/Framework/Application/SlateApplication.cpp",
                          ["TakeScreenshotCommon", "Renderer->PrepareToTakeScreenshot", "PrivateDrawWindows(WidgetWindow)"]),
        "slate_readback": ("Engine/Source/Runtime/SlateRHIRenderer/Private/SlateRHIRenderer.cpp",
                           ["PrepareToTakeScreenshot", "ScreenshotState.ViewportToCapture", "RHICmdList.ReadSurfaceData"]),
        "resolution_sink": ("Engine/Source/Runtime/Engine/Private/UnrealEngine.cpp",
                            ['TEXT("r.SetRes")', "SystemResolutionSinkCallback", "Viewport->ResizeFrame(ResX, ResY, WindowMode)"]),
        "scene_resize": ("Engine/Source/Runtime/Engine/Private/Slate/SceneViewport.cpp",
                         ["void FSceneViewport::ResizeViewport", "UpdateViewportRHI(false, NewSizeX, NewSizeY", "Invalidate, then redraw immediately"]),
        "offscreen_d3d12": ("Engine/Source/Runtime/D3D12RHI/Private/Windows/WindowsD3D12Viewport.cpp",
                            ['bNeedSwapChain(!FParse::Param(FCommandLine::Get(), TEXT("RenderOffScreen")))', "Resize(SizeX, SizeY, bIsFullscreen, PixelFormat)"]),
        "saved_paths": ("Engine/Source/Runtime/Core/Private/Misc/Paths.cpp",
                        ['TEXT("UserDir=")', "FPaths::EngineUserDir()", "CustomUserDirArgument", "Profiling/"]),
        "bootstrap": ("Engine/Source/Programs/AutomationTool/Win/WinPlatform.Automation.cs",
                      ["BootstrapArguments", "SC.IsCodeBasedProject", "SC.ShortProjectName"]),
        "log_clock": ("Engine/Source/Runtime/Core/Private/Misc/OutputDeviceHelper.cpp",
                      ["GFrameCounter % 1000"]),
        "crash_exit_enum": ("Engine/Source/Runtime/Core/Public/GenericPlatform/GenericPlatformCrashContext.h",
                            ["CrashReporterCrashed = 777003"]),
        "crash_exit_thread": ("Engine/Source/Runtime/Core/Private/Windows/WindowsPlatformCrashContext.cpp",
                              ["ECrashExitCodes::CrashReporterCrashed"]),
    }
    evidence = {}
    for name, (relative, required) in sources.items():
        path = engine / relative
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        hits = {term: next((i for i, line in enumerate(lines, 1) if term in line), None)
                for term in required}
        if any(value is None for value in hits.values()):
            raise RuntimeError("Installed native support differs: " + relative)
        evidence[name] = {"path_relative_to_engine": relative, "sha256": sha(path), "lines": hits}
    return evidence


def native_argument(value: str) -> str:
    """Preserve UE key=\"value\" syntax; CreateProcess sees this without a shell."""
    if '"' in value or "\n" in value or "\r" in value:
        raise RuntimeError("Native argument contains unsupported quoting")
    if "=" in value and value.startswith("-"):
        key, content = value.split("=", 1)
        # Keep conventional unquoted numeric arguments. Native FString values
        # containing spaces require quotes around their value.
        return key + '="' + content + '"' if " " in content else value
    return '"' + value + '"' if " " in value else value


def capture_statistics(path: Path, warmup: int, frames: int) -> dict:
    # Native boot CSV's EVENTS cell contains the complete engine init trace.
    csv.field_size_limit(64 * 1024**2)
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.reader(stream))
    header = None
    frame_column = memory_column = None
    valid = []
    for row in rows:
        normalized = [cell.strip().casefold() for cell in row]
        candidates = [i for i, cell in enumerate(normalized)
                      if cell == "frametime" or cell.endswith("/frametime")]
        if candidates:
            header = row
            frame_column = candidates[0]
            memories = [i for i, cell in enumerate(normalized)
                        if cell == "physicalusedmb" or cell.endswith("/physicalusedmb")]
            memory_column = memories[0] if memories else None
            continue
        if frame_column is None:
            continue
        try:
            frame = float(row[frame_column])
            physical = float(row[memory_column]) if memory_column is not None else None
        except (IndexError, ValueError):
            continue
        if not math.isfinite(frame) or frame <= 0:
            continue
        if physical is not None and (not math.isfinite(physical) or physical <= 0):
            physical = None
        valid.append((frame, physical))
    if len(valid) < warmup + frames:
        raise RuntimeError(f"CSV lacks required real frames: {len(valid)} < {warmup + frames}")
    if memory_column is None or any(memory is None for _, memory in valid[warmup:warmup + frames]):
        raise RuntimeError("Native physical-memory measurements missing from CSV")
    measured = [frame for frame, _ in valid[warmup:warmup + frames]]
    p95 = sorted(measured)[math.ceil(len(measured) * .95) - 1]
    output = path.parent / "measured_frame_times_ms.txt"
    output.write_text("".join(f"{value:.9f}\n" for value in measured), encoding="utf-8")
    return {"source_csv": str(path), "source_csv_sha256": sha(path), "native_frame_column": header[frame_column],
            "native_memory_column": header[memory_column], "valid_csv_rows": len(valid),
            "warmup_rows_discarded": warmup, "measured_frames": len(measured),
            "measured_seconds": sum(measured) / 1000,
            "median_ms": statistics.median(measured), "p95_ms": p95, "max_ms": max(measured),
            "mean_fps": 1000 / statistics.mean(measured),
            "frame_sampled_peak_physical_bytes": int(max(memory for _, memory in valid) * 1024**2),
            "peak_memory_scope": "native PhysicalUsedMB samples; not OS lifetime high-water mark",
            "frame_times_file": str(output), "frame_times_sha256": sha(output),
            "provisional_33_3_ms_budget_pass": p95 <= 33.3}


def captures(user: Path) -> dict:
    result = {}
    for width, height in ((1280, 720), (1920, 1080)):
        name = f"g1_opening_{width}x{height}.png"
        # Existing native Shot output used an appended numeric suffix. Validate
        # the exact stem, native numeric suffix only, and actual PNG dimensions.
        pattern = re.compile(re.escape(name[:-4]) + r"\d*\.png")
        candidates = [p for p in user.rglob("*.png") if pattern.fullmatch(p.name)]
        if len(candidates) != 1:
            raise RuntimeError("Required native screenshot missing/ambiguous: " + name)
        path = candidates[0]
        header = path.read_bytes()[:24]
        if header[:8] != b"\x89PNG\r\n\x1a\n" or len(header) < 24:
            raise RuntimeError("Screenshot is not a PNG: " + name)
        dimensions = struct.unpack(">II", header[16:24])
        if dimensions != (width, height):
            raise RuntimeError(f"Screenshot resolution differs: {name}: {dimensions}")
        result[f"{width}x{height}"] = {"file": str(path), "sha256": sha(path),
                                     "dimensions": list(dimensions), "visually_reviewed": False}
    return result


def analyze_outputs(run: Path, report: dict) -> int:
    """Keep genuine captures even when the owned process later exits abnormally."""
    issues = []
    log = run / "runtime.log"
    text = log.read_text(encoding="utf-8-sig", errors="replace")
    report["runtime_log_sha256"] = sha(log)
    map_entered = EXPECTED_MAP in text and bool(re.search(r"Starting Game|Bringing World .* up for play", text))
    csv_completed = "Capture Starting" in text and "CsvProfiler.ExitAfterCsvProfiling" in text
    report["runtime_proof"] = {"canonical_map_entered_game": map_entered,
                               "native_csv_completion_requested_exit": csv_completed,
                               "native_exit_request_line": next((line for line in text.splitlines()
                                  if "RequestExitWithStatus" in line and "CsvProfiler.ExitAfterCsvProfiling" in line), None),
                               "native_capture_frames_line": next((line for line in text.splitlines()
                                  if "LogCsvProfiler" in line and "Frames :" in line), None),
                               "log_counter_display": "GFrameCounter modulo 1000; not total capture frame count"}
    if not map_entered or not csv_completed:
        issues.append("Canonical map/game entry or native CSV completion is unproven")
    if report.get("exit_code") != 0:
        issues.append("Owned process exit is nonzero: " + str(report.get("exit_code")))
    if report.get("exit_code") == 777003:
        report["native_exit_failure"] = {
            "code": 777003, "enum": "ECrashExitCodes::CrashReporterCrashed",
            "source": "WindowsPlatformCrashContext.cpp exception handler in crash-reporting thread",
            "interpretation": "Abnormal process failure after capture; not a CSV success code"}
    bad = [line for line in text.splitlines() if any(marker in line for marker in
           ("Fatal error:", "Accessed None", "Script Runtime Error", "Unknown console command", "LogMaterial: Error:"))]
    report["runtime_errors"] = bad
    if bad:
        issues.append("Actual runtime errors recorded")
    metadata = dict(re.findall(r'Metadata set\s*:\s*(\w+)="([^"]*)"', text))
    report["hardware_metadata"] = metadata
    if not metadata.get("gpu") or metadata.get("rhiname", "").casefold() in ("", "null"):
        issues.append("Real GPU/RHI not confirmed")
    files = list((run / "UserData").rglob("*.csv"))
    try:
        if len(files) != 1:
            raise RuntimeError("Expected one actual native CSV capture")
        report["performance"] = capture_statistics(files[0], report["process_plan"]["warmup_frames"],
                                                    report["process_plan"]["measured_frames"])
    except (OSError, ValueError, csv.Error, RuntimeError) as exc:
        issues.append(str(exc))
    try:
        report["screenshots"] = captures(run / "UserData")
    except (OSError, RuntimeError, struct.error) as exc:
        issues.append(str(exc))
    report["smoke_capture_complete"] = "performance" in report and "screenshots" in report and map_entered
    report["clean_process_exit"] = report.get("exit_code") == 0
    if issues:
        report.update(status="STATIC_CAPTURE_WITH_RUNTIME_FAILURE", error="; ".join(issues))
        return 1
    report.pop("error", None)
    passed = report["performance"]["provisional_33_3_ms_budget_pass"]
    report["status"] = "STATIC_SMOKE_CAPTURED_BUDGET_" + ("PASS" if passed else "FAIL")
    return 0 if passed else 2


def analyze_existing(run: Path, engine: Path) -> int:
    run = run.resolve()
    if not run.is_relative_to(ROOT / "_release_work"):
        raise RuntimeError("Existing analysis must refer to a project-owned release evidence directory")
    path = run / "result.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("schema") != "kl.g1-native-packaged-smoke.v1" or report.get("dry_run") or report.get("exit_code") is None:
        raise RuntimeError("Existing run must contain actual exited process evidence")
    preserved = run / "launch_result_original.json"
    if not preserved.exists():
        shutil.copy2(path, preserved)
    report["analysis"] = {"time_utc": utc_now(), "instrumentation_sha256": sha(Path(__file__)),
                          "new_process_started": False, "native_source_proof": native_sources(engine)}
    code = analyze_outputs(run, report)
    after = package_digest(run / "WindowsBuild")
    write_json(run / "artifact_post_analysis.json", after)
    report["artifact_unchanged"] = after["sha256"] == report["binding"]["artifact_sha256"]
    if not report["artifact_unchanged"]:
        report.update(status="FAIL_ARTIFACT_CHANGED", error="Tested candidate changed")
        code = 1
    write_json(path, report)
    print(json.dumps({"status": report["status"], "error": report.get("error"), "binding": report["binding"],
                      "performance": report.get("performance"), "screenshots": report.get("screenshots"),
                      "runtime_errors": report.get("runtime_errors"), "artifact_unchanged": report["artifact_unchanged"],
                      "analysis": str(path), "new_process_started": False}, indent=2, ensure_ascii=False))
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-run", type=Path, help="explicit verifier run directory for this exact candidate")
    parser.add_argument("--engine", type=Path, default=ENGINE)
    parser.add_argument("--execute", action="store_true", help="explicitly launch the owned native game")
    parser.add_argument("--analyze-run", type=Path, help="analyze an exited existing run; no copy or launch")
    parser.add_argument("--frames", type=int, default=1800, help="real measured frames after warmup")
    parser.add_argument("--warmup", type=int, default=600)
    parser.add_argument("--timeout", type=int, default=300, help="wall safety timeout; never used as FPS")
    args = parser.parse_args()
    if args.analyze_run:
        if args.execute:
            parser.error("Existing analysis cannot launch another process")
        return analyze_existing(args.analyze_run, args.engine)
    if args.build_run is None:
        parser.error("Supply --build-run for the exact candidate; no historical build is selected implicitly")
    run = ROOT / "_release_work" / ("g1_smoke_" + time.strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8])
    run.mkdir(parents=True)
    user = run / "UserData"
    user.mkdir()
    report = {"schema": "kl.g1-native-packaged-smoke.v1", "scope": "stationary opening at 1280x720 low",
              "runtime": "packaged-win64", "qualified": False, "release_complete": False,
              "autoplay": False, "input_injection": False, "dry_run": not args.execute,
              "run": str(run), "instrumentation_sha256": sha(Path(__file__)), "start_utc": utc_now()}
    owned = None
    archive = None
    started = time.monotonic()
    try:
        if os.name != "nt" or args.frames < 1800 or args.warmup < 600 or args.timeout < 60:
            raise RuntimeError("Requires Windows, >=1800 measured frames, >=600 warmup frames and >=60s timeout")
        build_run = args.build_run.resolve()
        original_archive = build_run / "WindowsBuild"
        archive = run / "WindowsBuild"
        source = json.loads((build_run / "source_manifest.json").read_text(encoding="utf-8"))
        source_fields = {key: value for key, value in source.items() if key != "sha256"}
        if hashlib.sha256(json.dumps(source_fields, sort_keys=True).encode()).hexdigest() != source["sha256"]:
            raise RuntimeError("Recorded source manifest digest differs")
        recorded = json.loads((build_run / "artifact_manifest.json").read_text(encoding="utf-8"))
        current = package_digest(original_archive)
        extras = sorted(current["files"].keys() - recorded["files"].keys())
        missing = sorted(recorded["files"].keys() - current["files"].keys())
        changed = [name for name in recorded["files"]
                   if name in current["files"] and recorded["files"][name] != current["files"][name]]
        allowed_extras = all(name.startswith(("Engine/Saved/", "KhoangLang0217/Saved/")) for name in extras)
        if missing or changed or not allowed_extras:
            raise RuntimeError("Candidate files differ or unexpected package files were added; cannot reconstruct exact artifact")
        report["original_archive_sha256"] = current["sha256"]
        report["preserved_original_runtime_generated_files"] = extras
        report["candidate_copy"] = str(archive)
        write_json(run / "original_archive_snapshot.json", current)
        # Exact-file copy removes old generated user settings from the tested
        # candidate without deleting or modifying any original crash evidence.
        for name in recorded["files"]:
            source_file = (original_archive / name).resolve()
            target_file = (archive / name).resolve()
            if not source_file.is_relative_to(original_archive.resolve()) or not target_file.is_relative_to(archive.resolve()):
                raise RuntimeError("Recorded artifact contains an unsafe relative file path")
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, target_file)
        before = package_digest(archive)
        if before != recorded:
            raise RuntimeError("Fresh benchmark copy does not match recorded candidate")
        write_json(run / "artifact_pre.json", before)
        report["binding"] = {"source_revision": source["revision"], "source_sha256": source["sha256"],
                             "artifact_sha256": before["sha256"], "nonce": uuid.uuid4().hex}
        report["native_support"] = native_sources(args.engine)
        executable = archive / "Engine/Binaries/Win64/UnrealGame.exe"
        if not executable.is_file():
            raise RuntimeError("Installed Blueprint game's direct native executable is missing")
        # Same relative project argument generated for Blueprint bootstrap by
        # installed WinPlatform.Automation.cs. Launch directly so the PID is the
        # actual owned game, rather than a transient bootstrap launcher.
        argv = [str(executable), "../../../KhoangLang0217/KhoangLang0217.uproject",
                "-RenderOffscreen", "-windowed", "-ResX=960", "-ResY=540", "-NoSplash",
                "-SaveToUserDir", f"-UserDir={user}",
                f"-abslog={run / 'runtime.log'}",
                "-unattended", "-stdout", "-FullStdOutLogOutput",
                f"-csvCaptureFrames={args.warmup + args.frames}", "-csvCompression=0",
                "-ExitAfterCsvProfiling", "-ExecCmds=" + ",".join(START_COMMANDS),
                "-csvExecCmds=" + ",".join(FRAME_COMMANDS)]
        command = " ".join(native_argument(value) for value in argv)
        report["process_plan"] = {"argv": argv, "native_command_line": command,
                                  "cwd": str(executable.parent), "executable_sha256": sha(executable),
                                  "exit_mechanism": "native ExitAfterCsvProfiling, csv.ForceExit=0",
                                  "capture_scheduling": "CSV capture frame clock; no input events",
                                  "capture_schedule_version": CAPTURE_SCHEDULE,
                                  "initial_resolution": [960, 540],
                                  "measured_resolution": [1280, 720],
                                  "visual_review_required": True,
                                  "resize_evidence": "Checkpoint opening images were inspected at both sizes using this schedule; inspect fresh captures independently",
                                  "diagnostic_scene_capture": "Frame 280 Shot without SHOWUI reads the scene viewport separately from Slate; inspect original pixels",
                                  "saved_paths": "Game data uses isolated UserDir; SaveToUserDir routes engine caches to stock user AppData",
                                  "warmup_frames": args.warmup, "measured_frames": args.frames,
                                  "wall_timeout_seconds": args.timeout}
        write_json(run / "launch_plan.json", report["process_plan"])
        if not args.execute:
            report["status"] = "READY_PLAN_ONLY_NO_PROCESS_STARTED"
            return 0
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
        with (run / "stdout.log").open("w", encoding="utf-8") as output:
            owned = subprocess.Popen(command, cwd=executable.parent, stdout=output,
                                     stderr=subprocess.STDOUT, shell=False, startupinfo=startup)
            report["pid"] = owned.pid
            report["launch_utc"] = utc_now()
            write_json(run / "process_binding.json", {"pid": owned.pid, "launch_utc": report["launch_utc"],
                       "binding": report["binding"], "executable_sha256": sha(executable), "command": command})
            report["exit_code"] = owned.wait(timeout=args.timeout)
        return analyze_outputs(run, report)
    except subprocess.TimeoutExpired:
        report.update(status="FAIL_TIMEOUT", error="Native capture did not exit inside the wall limit",
                      owned_process_still_running=owned is not None and owned.poll() is None,
                      cleanup="No force-stop or UI operation attempted; native CSV completion exit remains scheduled")
        return 1
    except (OSError, ValueError, KeyError, RuntimeError, TypeError, struct.error) as exc:
        report.update(status="FAIL", error=str(exc))
        return 1
    finally:
        final_failure = False
        report["end_utc"] = utc_now()
        report["wall_elapsed_seconds"] = time.monotonic() - started
        if archive and archive.is_dir():
            try:
                after = package_digest(archive)
                write_json(run / "artifact_post.json", after)
                report["artifact_unchanged"] = after.get("sha256") == report.get("binding", {}).get("artifact_sha256")
                if args.execute and not report["artifact_unchanged"]:
                    report.update(status="FAIL_ARTIFACT_CHANGED", smoke_capture_complete=False)
                    final_failure = True
            except OSError as exc:
                report.update(status="FAIL_ARTIFACT_RECHECK", error=str(exc))
                final_failure = True
        write_json(run / "result.json", report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if final_failure:
            raise ArtifactRecheckFailed("Artifact integrity failure recorded in result.json")


if __name__ == "__main__":
    try:
        code = main()
    except ArtifactRecheckFailed:
        code = 1
    raise SystemExit(code)
