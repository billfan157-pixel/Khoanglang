# Production state

Current work: G1 repair/test atomic checkpoint; no next feature authorized.
G1 art/audio acceptance and G2-G5/full release remain unmet.
After compaction read this file and the original user brief:
attachment 00a0dcee-7741-4032-a8f1-9968f060c815/pasted-text-1.txt.
The newer user goal requires finishing this checkpoint, not campaign expansion.

## Verified facts (2026-10-01)

- Project KhoangLang0217.uproject, Unreal 5.8.3, Blueprint-only.
- Branch production/g1-canonical-loop; scoped repair checkpoint 8220edf.
  Its follow-up makes the test client/options reproducible from tracked files.
  Preserve unrelated concurrent work listed in G1_CHECKPOINT_SCOPE.json.
- V3 Bible: 1,132 lines, updated 30/09, SHA256
  80EEE1981BF2A155726DA34617300647C1A9813B3D93F60628856B2E5EEC7E44.
  Original story/source art packages remain immutable.
- G1 map: /Game/KhoangLang/Production/G1Canon/Lvl_KL_SchoolSlice.
  Native SchoolPlayer/GameMode/core Blueprints compiled and saved; no template
  FirstPerson/animation dependencies in the independent native player.
- Saved lighting: 12 authored lights + 3 bounce points Movable, no precomputed
  lighting, neutral -1.5 EV, saved torch90 lumens. Actual PIE readback passed
  in G1_runtime_scene_audit.json; fixtures did not establish those defaults.
- Mesh repairs: fresh regular builds, exact wall/door triangle corners and UVs;
  corrected cassette Y-cylinder cap centres and supported authored shelf.
  Mesh default materials bound to copied G1 master. Original meshes preserved.
- Reloaded saved map: 51 unique meshes pass finite bounds/buffer/material audit.
  G1_mesh_binding_audit.json records actual readbacks,50 source origins/package
  hashes, original degeneracy and adopted triangle counts. All nonzero source
  triangle counts preserved. The shelf is new. Strict checks were not relaxed.
- Zero-area faces and degenerate UV projection exist in some source props.
  Owned copies remove only zero-area faces; native non-Mikk recomputation fixes
  tiny desk tangents. Collision structs/component modes retained.
- 11 unused newly authored attempts preserved intact outside Content under
  _release_work/g1_checkpoint_recovery/, with moved_unused_meshes.json.
- G1_navigation_trial.json passed26 native movement waypoints, real collision
  and camera-ray Lam/deck/notebook/ledger/exit interactions, no teleport.
  Four failed candidate routes preserved. Before/after disk hashes stable.
- G1_trial_suite.json: all8 fresh-PIE cases passed after final map/player writes:
  held, names, wrong, tier1, decay, contact, avoidance, interactions.
- Tracked MCP client/generated PIE options: fresh eight-case suite passed again;
  actual native error propagates CLI exit1. Project-root discovery is scoped.
  G1_runner_reproducibility.json pins helper/report hashes and records the prior
  overlapped-RPC timeout without claiming an exclusive cause. Calls serialized.
- G1_attention_trial.json: tier2 draft loss/false geometry, tier3 native pursuit
  and automatic contact, raw retention, cooldown, quiet recovery passed;
  before/after source/player/map hashes stable. Explicit fixtures recorded.
- G1_input_pin_audit.json: all16 declared keys read correctly from native saved
  graphs. Concurrent bare FKey source fixes integrated; no physical-input claim.
- G1_lighting_checkpoint_final.json: 12 actual PIE captures. Front/side deck and
  classroom images inspected: support/cap spikes improved; deep unlit shadows,
  bright torch response, coarse source art and pale-surface HUD contrast remain.
- Windows Development package: UAT0, no error/NaN/ShaderMap/degenerate lines in
  final cook log. G1_CHECKPOINT_BUILD.json; archive
  _release_work/20260930_235642_f042e94a/WindowsBuild, retain entire directory.
  Source SHA439582a23e69c3a9bd4a8a3d90eb98595849c377676feb10a1feb2e03e3c34c3.
  Artifact SHAbed93a176461c2af81f81f64e7ff5cee8c7a3541fe7863ed0cc49c3535743538.
- G1_CHECKPOINT_RUNTIME.json: real Intel Arc/D3D12 opening,2400CSV frames,
  discard600 ->1800/25.04s, median13.66ms,p95 16.97ms,max79.89ms, mean71.88fps,
  sampled peak physical1.60GiB. Stationary720p low only; no campaign performance.
  720p/1080p screenshots inspected: actual school/Vietnamese HUD present,
  no lighting rebuild warning; HUD contrast/source art still unaccepted.
  Runtime shader/NaN errors absent, archive unchanged. Exit777003 still FAIL.
- Shutdown control loaded actual /Engine/Maps/Entry with GameModeBase,
  NullRHI/no sound and60CSV frames, also exited777003. Thus failure does not
  depend on G1 world content/RHI/audio. Binary/environment cause unresolved;
  no forced-exit workaround, crash suppression or runtime acceptance.
- Prior package baseline preserved: p95 44.78ms, shader/NaN warnings,
  blank720p capture and same777003 exit; G1_PACKAGED_BASELINE.json.
- G1_CHECKPOINT.md lists implementation, important files and assumptions.
  Python authoring/test only; native Blueprint Tick/Character runtime remains.
- Original/legacy Character edits, diagnostic scripts and tracked baseline logs
  predate these scoped changes. Preserve them outside this repair commit.

## Constraints and review

- Bống is the back-row child; Nhi is separate. Lam describes current observation,
  not invented2002 eyewitness history. Names/ledger are isolated G1 fixtures.
- Temporary numbers/inventory exhaustion defaults are engineering assumptions.
  Giữ needs two-person acknowledgment + seal; single-child reply only pauses.
- HUMAN_SIGNOFF.md is user-owned: never create/edit. Original full release would
  require tools/verify_release passing and user signoff; checkpoint is not RC.
- No new Vietnamese performances. Editor engineering used -nosound; agent does
  not qualify listening/scare effectiveness. Exact reviews in REVIEW_QUEUE.md.
- User stopped Computer Use with Escape; no physical-input automation resumed.
- Original DefaultEngine.ini has local token: never print/package. Packaging uses
  sanitized isolated config and excludes editor/MCP/Python runtime modules.
- Remote Python is ephemeral/loopback only. Final test editor closed with no
  dirty packages. Read-only provenance editor also closed with no dirty packages.
- Clean detached review checkout: sibling KhoangLang0217-g1-review-8220edf;
  updated to the final scoped follow-up commit. Primary concurrent work retained.
- No paid/third-party assets added; no Blender MCP simulated.

## Stop boundary

Implementation/evidence are ready for review. No campaign/next-system work.
Keep runtime qualification withheld for777003 and human visual/audio/input
acceptance outstanding. Preserve the concurrent checkout changes.
