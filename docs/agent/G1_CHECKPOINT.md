# G1 repair and verification checkpoint

Scope: finish the existing G1 lighting, mesh, material and verification work.
Do not begin the campaign, a new enemy system, voice production or another
architectural expansion. This checkpoint is not G1 art acceptance or a release.

The school map now uses Movable practical lights, three authored bounce points,
manual exposure -1.5 EV and a saved 90-lumen flashlight. Wood instances use a
muted detail response. The cassette has corrected cylinder cap centres, a
project-authored timber/metal shelf and a front-facing hall orientation.

Fresh regular static meshes replace invalid fast-built derived data. Wall and
door copies preserve oriented triangle positions, UVs and material groups while
isolating triangle vertices to prevent tangent/normal cancellation. Material
defaults on the adopted copies reference the G1 master, removing the broken
original master from those mesh dependencies. Source art packages are preserved.
Zero-area source faces in other copied props were removed; UV projection changes
are recorded separately. The native builder and actual render buffers determine
qualification. Tiny desk details use native non-Mikk recomputation when Mikk
returns zero tangents; the strict finite/nonzero checks remain unchanged.

The saved map was reloaded and 51 unique school meshes passed the geometry and
default-material audit. Native movement reached all 26 route points, acquired
Lam, the deck, notebook and ledger through real camera rays, and reached the
exit. Four earlier blocked routes are retained as evidence. Eight fresh-PIE
mechanic cases and the tier2/tier3 attention trial passed with current assets.
Attention and navigation bind source/map/player hashes before and after their
runs. Graph inspection checks 16 declared keys; physical keyboard/mouse behavior
remains unqualified. These editor runs used -nosound and do not qualify playback.

Twelve final PIE images were captured. Front, side and classroom images were
inspected: the cassette rests on its shelf and cap spikes are absent; the source
art still has coarse construction, bright flashlight response, deep unlit
shadows and weak HUD contrast over pale surfaces. These are explicit quality
limits, not visual acceptance. Packaged checks and their measured results belong
in G1_CHECKPOINT_BUILD.json and G1_CHECKPOINT_RUNTIME.json after actual execution.

Final Windows cook returned UAT0 with no error/NaN/ShaderMap/degenerate lines.
The real packaged opening produced valid inspected720p/1080p images and1800
measured frames after600 warmup: p95 16.97ms, median13.66ms on Intel Arc/D3D12
at720p low. This is a stationary opening measurement only. The archive remained
unchanged. Normal process exit is still FAIL777003, also reproduced by actually
loading the empty Engine Entry/GameModeBase with NullRHI/no sound. This isolates
the failure from G1 world content; underlying binary/environment cause remains
unresolved. The checkpoint repairs pass their gates; packaged runtime/release
qualification remains withheld. No suppression or forced-exit workaround is used.

## Architectural assumptions

- Blueprint native Tick/Character movement remains the runtime authority;
  Python is editor authoring and test orchestration only.
- GI remains disabled for the existing integrated-GPU target. Bounce points are
  authored approximations, not measured indirect illumination.
- Triangle isolation favors stable hard edges over original welded smoothing.
  Zero-area faces have no rendered or collision surface; no nonzero geometry
  is intentionally removed. Degenerate UVs receive dominant-plane projection
  at the existing 0.0045-per-cm texel scale in owned copies only.
- Aggregate simple collision is copied as a native struct when present; complex
  triangle collision, component modes and actor material overrides are retained.
- The shelf and cassette placement are reversible set dressing, not story facts.
  G1 names/ledger remain isolated fixtures; Lam is a present-day observer.
- Attention thresholds, inventory exhaustion behavior and automatic steering
  fixtures remain engineering defaults. No canon, narrative acceptance or
  physical-input qualification follows from these tests.

## Important changed files

- `tools/g1_calibrate_lighting.py`, `g1_save_torch_calibration.py` and
  `g1_refine_school_art.py`: saved lighting, material and flashlight authoring.
- `tools/g1_repair_school_meshes.py`, `g1_mount_deck.py` and
  `g1_isolate_mesh_materials.py`: guarded geometry and material integration.
- `tools/g1_audit_mesh_bindings.py`, `g1_audit_runtime_scene.py` and
  `g1_audit_input_pins.py`: actual persisted/native readbacks.
- `tools/g1_navigation_trial.py`, `g1_attention_trial.py`, `g1_run_trials.py`,
  `g1_lighting_trial.py` and `g1_packaged_smoke.py`: bounded reproducible checks.
- `tools/ue_mcp.py` and `ue_live.py`: tracked native MCP client and project-root
  scoped Python discovery; the runner generates its own ignored PIE options.
- `Content/KhoangLang/Production/G1Canon/`: map, native player/core assets,
  copied materials and only adopted new mesh packages (Git LFS).
- `Content/Python/KhoangLang/kl_core.py`, `build_20_blueprints.py` and
  `tools/g1_build_native_player.py`: concurrent bare FKey corrections integrated
  and inspected in the saved runtime graphs; torch default synchronized.
- `docs/agent/EVIDENCE/G1_*`: reports, preserved route failures and final images.
  `STATE.md`, `DECISIONS.md`, `OPEN_QUESTIONS.md` and `REVIEW_QUEUE.md` record the
  checkpoint and remaining human review. HUMAN_SIGNOFF.md remains untouched.

Unused new mesh attempts were moved intact to
`_release_work/g1_checkpoint_recovery/` with a moved-files manifest. No source
asset was deleted. Unrelated original/legacy Character changes, diagnostics and
preexisting runtime logs remain outside the scoped checkpoint; preserve them.

To repeat the eight editor cases, open this project's G1 school map, keep PIE
stopped, and enable Python remote execution on127.0.0.1 only for the test session.
The project's native editor MCP must listen on127.0.0.1:8000/mcp (see SETUP.md).
Run `python tools/ue_mcp.py init`, then `python tools/g1_run_trials.py`.
Keep editor RPC calls serialized while a suite owns the editor; the client also
uses distinct request IDs and propagates native tool errors as a nonzero exit.
Close the editor/disable remote execution afterward. No untracked client or PIE
options file is required. Source-default input/fixture/physical-audio limitations
remain as described above. For packaged capture, pass an explicit build directory:
`python tools/g1_packaged_smoke.py --build-run <verifier-run> --execute`.
