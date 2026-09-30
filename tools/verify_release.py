"""Isolated Windows package builder and fail-closed qualification coordinator.

Default release verification requires a real campaign runtime driver. G1 packaging
alone is deliberately not a gameplay or release pass. No user signoff is modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
G1_MAP = "/Game/KhoangLang/Production/G1Canon/Lvl_KL_SchoolSlice"
ENGINE_DEFAULT = Path(r"C:\Program Files\Epic Games\UE_5.8")
FORBIDDEN_PLUGINS = {"EditorToolset", "ModelContextProtocol", "PythonScriptPlugin",
                     "EditorScriptingUtilities", "ModelingToolsEditorMode"}
UNUSED_OPTIONAL_PLUGINS = {"GameplayStateTree", "Landmass"}
ENDING_CASES = {f"{ending}_{truth}" for ending in "ABC" for truth in ("public", "private")}
G1_CASES = {"dual_listening", "whole_sentence_preview", "whole_sentence_seal",
            "attention_0", "attention_1", "attention_2", "attention_3",
            "teacher_child_loop", "lam_corroboration", "physical_controls"}


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def git(*args: str) -> str:
    result = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True,
                            text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        raise RuntimeError("Cannot identify source revision; real Git checkout required")
    return result.stdout.strip()


def package_digest(folder: Path) -> dict:
    files = {p.relative_to(folder).as_posix(): sha(p)
             for p in sorted(folder.rglob("*")) if p.is_file()}
    if not files:
        raise RuntimeError("Packaged artifact contains no files")
    digest = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    return {"sha256": digest, "files": files}


def project_descriptor() -> dict:
    value = json.loads((ROOT / "KhoangLang0217.uproject").read_text(encoding="utf-8-sig"))
    if value.get("Modules") or (ROOT / "Source").exists():
        raise RuntimeError("Pipeline currently supports the installed Blueprint-only target")
    value["Plugins"] = [p for p in value.get("Plugins", [])
                        if p["Name"] not in FORBIDDEN_PLUGINS | UNUSED_OPTIONAL_PLUGINS
                        and "Editor" not in p.get("TargetAllowList", [])]
    # Enabled GameplayStateTree requires a freshly compiled project target in
    # this installed engine. The current Blueprint school has no module imports.
    # A dependency scan below rejects this route if future assets require it.
    for name in sorted(UNUSED_OPTIONAL_PLUGINS):
        value["Plugins"].append({"Name": name, "Enabled": False})
    return value


def audit_optional_plugin(content: Path) -> dict:
    markers = ["GameplayStateTree", "/Script/StateTreeModule", "/Script/GameplayStateTreeModule",
               "/Landmass/", "/Script/Landmass"]
    checked = 0
    for path in content.rglob("*"):
        if path.suffix.lower() not in (".uasset", ".umap", ".uexp"):
            continue
        checked += 1
        data = path.read_bytes()
        if any(marker.encode() in data or marker.encode("utf-16-le") in data for marker in markers):
            raise RuntimeError("Optional plugin import needs a supported packaging route; cannot disable plugin: "
                               + path.relative_to(content).as_posix())
    return {"plugins": sorted(UNUSED_OPTIONAL_PLUGINS), "enabled_in_isolated_descriptor": False,
            "scanned_asset_files": checked, "serialized_import_markers": markers, "hits": [],
            "limitation": "Static import scan; actual cook remains authoritative"}


def map_file(package: str) -> Path:
    if not re.fullmatch(r"/Game/[A-Za-z0-9_/]+", package):
        raise RuntimeError("Cook map must be a single canonical /Game package path")
    return ROOT / "Content" / (package[6:] + ".umap")


def read_plan(path: Path, gate: str) -> dict:
    if not path.is_file():
        raise RuntimeError("Campaign/runtime verification plan absent: " + str(path.relative_to(ROOT))
                           if path.is_relative_to(ROOT) else "Runtime verification plan absent")
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if value.get("schema") != "kl.runtime-plan.v1" or value.get("gate") != gate:
        raise RuntimeError("Runtime plan has wrong schema or gate; earlier engineering JSON is insufficient")
    driver = (ROOT / value["driver"]).resolve()
    if not driver.is_relative_to(ROOT / "tools") or driver.suffix != ".py" or not driver.is_file():
        raise RuntimeError("A checked-in project tools/*.py runtime driver is required")
    if not value.get("maps") or not value.get("key_locations"):
        raise RuntimeError("Runtime plan must identify cook maps and screenshot locations")
    for package in value["maps"]:
        if not map_file(package).is_file():
            raise RuntimeError("Required campaign map is missing: " + package)
    expected = ENDING_CASES if gate == "release" else G1_CASES
    cases = value.get("cases", {})
    if set(cases) != expected or any(not cases[c].get("debug_commands") for c in expected):
        raise RuntimeError("Runtime plan must cover every required case with executable debug commands")
    if gate == "release" and set(value.get("chapters", [])) != set(range(1, 8)):
        raise RuntimeError("Release requires all seven chapters; no implicit scope reduction")
    return value


def preflight(engine: Path, gate: str, maps: list[str]) -> dict:
    required = [engine / "Engine/Build/BatchFiles/RunUAT.bat",
                engine / "Engine/Binaries/Win64/UnrealEditor-Cmd.exe",
                engine / "Engine/Binaries/Win64/UnrealGame.exe",
                engine / "Engine/Binaries/Win64/UnrealGame.target",
                engine / "Engine/Extras/Redist/en-us/vc_redist.x64.exe",
                engine / "Engine/Extras/Redist/en-us/vc_redist.arm64.exe",
                engine / "Engine/Build/InstalledBuild.txt"]
    missing = [str(p) for p in required if not p.is_file()]
    missing += [str(map_file(m)) for m in maps if not map_file(m).is_file()]
    total_content = sum(p.stat().st_size for p in (ROOT / "Content").rglob("*") if p.is_file())
    space = shutil.disk_usage(ROOT)
    if space.free < max(4 * 1024**3, total_content * 5):
        missing.append("Insufficient staging disk headroom (4 GiB minimum)")
    descriptor = project_descriptor()
    plugin_audit = audit_optional_plugin(ROOT / "Content")
    version_path = engine / "Engine/Build/Build.version"
    return {"schema": "kl.package-preflight.v1", "gate": gate, "qualified": False,
            "source_revision": git("rev-parse", "HEAD"),
            "source_status": git("status", "--short"), "maps": maps,
            "engine_version": json.loads(version_path.read_text()) if version_path.exists() else None,
            "engine": str(engine), "content_bytes": total_content, "disk_free_bytes": space.free,
            "prerequisite_failures": missing,
            "shipping_descriptor_plugins": [p["Name"] for p in descriptor["Plugins"] if p.get("Enabled")],
            "optional_plugin_audit": plugin_audit,
            "build_strategy": "installed UnrealGame Development; skip native compilation",
            "provenance": {"engine_and_template": "Epic Games installed UE 5.8.3",
                           "license_review_complete": False},
            "limitations": ["Preflight is not cook/build or runtime proof",
                            "No Windows SDK/compiler suitability claim",
                            "No human audio, visual quality or scare acceptance"]}


def stage_source(run: Path, maps: list[str], plan: dict | None) -> tuple[Path, dict]:
    project = run / "Source/KhoangLang0217"
    project.mkdir(parents=True)
    # Copy rather than junction: editor saves during cook cannot alter originals.
    # Never copy or read the original DefaultEngine.ini: it contains a token.
    before = {p.relative_to(ROOT / "Content").as_posix(): sha(p)
              for p in sorted((ROOT / "Content").rglob("*")) if p.is_file()}
    shutil.copytree(ROOT / "Content", project / "Content")
    plugin_audit = audit_optional_plugin(project / "Content")
    write_json(run / "optional_plugin_audit.json", plugin_audit)
    config = project / "Config"
    config.mkdir()
    for name in ("DefaultGame.ini", "DefaultInput.ini"):
        path = ROOT / "Config" / name
        if path.is_file():
            raw = path.read_text(encoding="utf-8-sig")
            # Refuse unexpected secret-bearing keys without echoing any value.
            for line in raw.splitlines():
                key = line.split("=", 1)[0].casefold()
                if "=" in line and any(word in key for word in ("token", "secret", "password", "apikey")):
                    raise RuntimeError("Allowed config contains a secret-bearing key; values withheld")
            (config / name).write_text(raw, encoding="utf-8")
    # UProjectPackagingSettings is declared UCLASS(config=Game) in the
    # installed DeveloperToolSettings header. Engine.ini silently misses it.
    packaging_section = "[/Script/UnrealEd.ProjectPackagingSettings]"
    game_path = config / "DefaultGame.ini"
    game_lines = game_path.read_text(encoding="utf-8").splitlines() if game_path.exists() else []
    kept = []
    skipping = False
    for line in game_lines:
        if line.strip().startswith("["):
            skipping = line.strip().casefold() == packaging_section.casefold()
        if not skipping:
            kept.append(line)
    game_path.write_text("\n".join(kept) + "\n\n" + packaging_section + "\n"
                        "BuildConfiguration=PPBC_Development\nbCookAll=False\nbSkipEditorContent=True\n"
                        # Installed editor modules load Landmass brush resources
                        # as startup packages even with its descriptor disabled.
                        # audit_optional_plugin rejected any game import of it.
                        '+DirectoriesToNeverCook=(Path="/Landmass")\n'
                        "InternationalizationPreset=All\n!CulturesToStage=ClearArray\n"
                        "+CulturesToStage=vi\n+CulturesToStage=en\n!MapsToCook=ClearArray\n"
                        + "".join(f'+MapsToCook=(FilePath="{m}")\n' for m in maps), encoding="utf-8")
    (config / "DefaultEngine.ini").write_text(
        "[/Script/EngineSettings.GameMapsSettings]\n"
        f"GameDefaultMap={maps[0]}\nEditorStartupMap={maps[0]}\n", encoding="utf-8")
    descriptor = project / "KhoangLang0217.uproject"
    write_json(descriptor, project_descriptor())
    after = {p.relative_to(project / "Content").as_posix(): sha(p)
             for p in sorted((project / "Content").rglob("*")) if p.is_file()}
    if before != after:
        raise RuntimeError("Content changed while copying; stop editor writers and retry")
    source = {"revision": git("rev-parse", "HEAD"), "content": after,
              "sanitized_config": {p.name: sha(p) for p in sorted(config.iterdir())},
              "descriptor_sha256": sha(descriptor), "verifier_sha256": sha(Path(__file__))}
    source["optional_plugin_audit"] = plugin_audit
    if plan:
        source["runtime_driver_sha256"] = sha(ROOT / plan["driver"])
        source["runtime_plan_sha256"] = hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest()
    source["sha256"] = hashlib.sha256(json.dumps(source, sort_keys=True).encode()).hexdigest()
    write_json(run / "source_manifest.json", source)
    return descriptor, source


def build(engine: Path, descriptor: Path, maps: list[str], run: Path, timeout: int) -> Path:
    archive = run / "WindowsBuild"
    args = [str(engine / "Engine/Build/BatchFiles/RunUAT.bat"), "BuildCookRun",
            f"-project={descriptor}", "-nop4", "-unattended", "-utf8output",
            "-nocompileuat", "-nocompile", "-skipbuild", "-cook", "-stage", "-pak",
            "-archive", "-package", "-prereqs", "-targetplatform=Win64", "-clientconfig=Development",
            f"-map={'+'.join(maps)}", f"-archivedirectory={archive}", "-i18npreset=All",
            "-cookcultures=vi+en", "-SkipCookingEditorContent"]
    # CMD does not understand CRT backslash-escaped quotes. Passing /c's whole
    # command as a list element double-encodes its nested quotes on Windows.
    # Build one native command string with /s's required outer enclosing pair.
    comspec = os.environ.get("COMSPEC", "cmd.exe")
    command = f'"{comspec}" /d /s /c "' + subprocess.list2cmdline(args) + '"'
    write_json(run / "uat_command.json", {"argv": args, "timeout_seconds": timeout})
    with (run / "uat.log").open("w", encoding="utf-8") as log:
        completed = subprocess.run(command, cwd=descriptor.parent, stdout=log,
                                   stderr=subprocess.STDOUT, timeout=timeout)
    if completed.returncode:
        raise RuntimeError(f"UAT failed (exit {completed.returncode}); inspect isolated uat.log")
    if not any(archive.rglob("*.exe")) or not any(archive.rglob("*.pak")):
        raise RuntimeError("UAT returned success but runnable executable/pak artifacts are missing")
    return archive


def evidence_file(base: Path, name: str, digest: str) -> Path:
    path = (base / name).resolve()
    if not path.is_relative_to(base.resolve()) or not path.is_file() or sha(path) != digest:
        raise RuntimeError("Runtime evidence artifact missing, outside run directory or digest mismatch")
    return path


def validate_runtime(report: dict, plan: dict, run: Path, binding: dict) -> None:
    if report.get("schema") != "kl.packaged-runtime.v1" or report.get("binding") != binding:
        raise RuntimeError("Packaged runtime report is not bound to this candidate/source/run")
    if report.get("runtime") != "packaged-win64" or report.get("gate") != plan["gate"]:
        raise RuntimeError("Editor engineering checks cannot qualify the packaged candidate")
    expected = ENDING_CASES if plan["gate"] == "release" else G1_CASES
    for name in expected:
        case = report.get("cases", {}).get(name, {})
        if case.get("passed") is not True or case.get("executed_debug_commands") != plan["cases"][name]["debug_commands"]:
            raise RuntimeError("Runtime case failed/missing: " + name)
        trace = evidence_file(run, case["trace"], case["trace_sha256"])
        if trace.stat().st_size < 64 or not case.get("observed_states"):
            raise RuntimeError("Runtime case lacks an observed gameplay trace: " + name)
        if plan["gate"] == "release":
            ending, truth = name.split("_", 1)
            if case.get("opened_from_new_game") is not True or case.get("chapter_sequence") != list(range(1, 8)):
                raise RuntimeError("Ending case lacks complete new-game-to-ending traversal: " + name)
            if case.get("reached_ending") != ending or case.get("truth_branch") != truth:
                raise RuntimeError("Observed ending/truth branch differs from requested case: " + name)
    if plan["gate"] == "release":
        saves = report.get("boundary_saves", {})
        for chapter in range(1, 8):
            item = saves.get(str(chapter), {})
            if item.get("passed") is not True or not item.get("restarted_process"):
                raise RuntimeError("Chapter-boundary save/load restart proof missing")
            if not item.get("before_state_sha256") or item["before_state_sha256"] != item.get("loaded_state_sha256"):
                raise RuntimeError("Chapter-boundary loaded state differs")
            evidence_file(run, item["save_file"], item["save_sha256"])
            evidence_file(run, item["trace"], item["trace_sha256"])
    captures = report.get("screenshots", {})
    for location in plan["key_locations"]:
        for resolution in ("1280x720", "1920x1080"):
            item = captures.get(location + "@" + resolution, {})
            png = evidence_file(run, item["file"], item["sha256"])
            header = png.read_bytes()[:24]
            width, height = map(int, resolution.split("x"))
            if header[:8] != b"\x89PNG\r\n\x1a\n" or struct.unpack(">II", header[16:24]) != (width, height):
                raise RuntimeError("Screenshot is not the required gameplay PNG resolution")
    render = report.get("vietnamese_rendering", {})
    if render.get("missing_glyphs") != 0 or not render.get("rendered_text") or render.get("passed") is not True:
        raise RuntimeError("Vietnamese glyph/layout runtime check missing or failed")
    evidence_file(run, render["trace"], render["trace_sha256"])
    perf = report.get("performance", {})
    data = evidence_file(run, perf["frame_times_ms"], perf["sha256"])
    samples = [float(v) for v in data.read_text().splitlines() if v.strip()]
    if (len(samples) < 1800 or any(not math.isfinite(v) or v <= 0 for v in samples)
            or not perf.get("hardware") or not perf.get("peak_memory_bytes")):
        raise RuntimeError("Performance lacks 1800 measured frames, hardware or peak memory")
    p95 = sorted(samples)[int((len(samples) - 1) * .95)]
    if p95 > 33.3:
        raise RuntimeError(f"Provisional 30 fps budget failed: p95 {p95:.2f} ms")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", choices=("release", "g1"), default="release")
    parser.add_argument("--preflight", action="store_true", help="read-only prerequisite inspection; never qualifies")
    parser.add_argument("--package-only", action="store_true", help="G1 only; creates package but returns unqualified exit 2")
    parser.add_argument("--engine", type=Path, default=ENGINE_DEFAULT)
    parser.add_argument("--runtime-plan", type=Path)
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()
    run = ROOT / "_release_work" / (time.strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8])
    run.mkdir(parents=True)
    result = {"schema": "kl.verification-result.v1", "gate": args.gate, "qualified": False,
              "release_complete": False, "run_directory": str(run)}
    try:
        if os.name != "nt":
            raise RuntimeError("Windows packaging pipeline requires Windows")
        if args.timeout < 60:
            raise RuntimeError("Timeout must be at least 60 seconds")
        if args.package_only and args.gate != "g1":
            raise RuntimeError("Release cannot bypass runtime qualification")
        plan = None
        if not args.package_only:
            plan = read_plan(args.runtime_plan or ROOT / f"tools/{args.gate}_runtime_plan.json", args.gate)
        maps = plan["maps"] if plan else [G1_MAP]
        check = preflight(args.engine, args.gate, maps)
        write_json(run / "preflight.json", check)
        if check["prerequisite_failures"]:
            raise RuntimeError("Packaging prerequisites missing: " + "; ".join(check["prerequisite_failures"]))
        if args.preflight:
            result["status"] = "PREFLIGHT_ONLY_UNQUALIFIED"
            return 0
        descriptor, source = stage_source(run, maps, plan)
        result.update(source_revision=source["revision"], source_sha256=source["sha256"],
                      source_manifest="source_manifest.json")
        archive = build(args.engine, descriptor, maps, run, args.timeout)
        artifact = package_digest(archive)
        write_json(run / "artifact_manifest.json", artifact)
        result["package"] = str(archive)
        result["artifact_sha256"] = artifact["sha256"]
        if args.package_only:
            result["status"] = "G1_PACKAGE_BUILT_RUNTIME_UNQUALIFIED"
            return 2
        binding = {"nonce": uuid.uuid4().hex, "source_sha256": source["sha256"],
                   "artifact_sha256": artifact["sha256"], "source_revision": source["revision"]}
        request = {"schema": "kl.runtime-request.v1", "binding": binding, "plan": plan,
                   "package_directory": str(archive), "report": str(run / "runtime.json")}
        write_json(run / "runtime_request.json", request)
        driver = ROOT / plan["driver"]
        with (run / "runtime_driver.log").open("w", encoding="utf-8") as log:
            process = subprocess.run([sys.executable, str(driver), "--request", str(run / "runtime_request.json")],
                                     cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=args.timeout)
        if process.returncode:
            raise RuntimeError("Packaged runtime driver failed")
        validate_runtime(json.loads((run / "runtime.json").read_text(encoding="utf-8")), plan, run, binding)
        if package_digest(archive)["sha256"] != artifact["sha256"]:
            raise RuntimeError("Candidate artifact changed during verification; runtime data must live outside package")
        result.update(qualified=True, status=args.gate.upper() + "_AUTOMATED_CHECKS_PASS")
        # Human acceptance is deliberately separate, including audio and visual quality.
        return 0
    except (OSError, ValueError, KeyError, TypeError, AttributeError, struct.error,
            RuntimeError, subprocess.TimeoutExpired) as exc:
        result.update(status="FAIL", error=str(exc))
        return 1
    finally:
        if (run / "uat.log").is_file():
            result["uat_log_sha256"] = sha(run / "uat.log")
        write_json(run / "result.json", result)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.exit(main())
