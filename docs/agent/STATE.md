# Production state

Current gate: G0 baseline collected; production prototype foundation verified;
G1 canonical school loop still incomplete.
Latest brief: user attachment goal-objective.md supplied on 2026-09-30.
Read this state and that brief at session start and after compaction.

## Verified facts
- Project KhoangLang0217.uproject, Unreal Engine 5.8.3, Blueprint-only.
- Branch production/g0-audit; source 3ea094b, LFS snapshot ffc85df, G0 f271991.
- Canonical story matches supplied 30/09 update exactly: 1,132 lines, SHA256
  80EEE1981BF2A155726DA34617300647C1A9813B3D93F60628856B2E5EEC7E44.
- Prior complete and truncated story versions are preserved separately.
- Fresh build_40 audit after narrow HUD repair exited 0, failures 0, 38 connected
  HUD targets. Asset-validator API unavailable. No packaged game demonstrated.
- Original editor PID 30292 completed the graybox baseline and later crashed
  during EditorAssetLibrary world duplication/load (confirmed process gone).
- Graybox pawn spawns with investigation/listening and four props.
- Time advances; StartBeds false. InitKL entry connects directly to Return,
  bypassing its body. Typed component targets are disconnected.
- EnhancedInput event execution handlers are disconnected.
- Inspected G0_graybox_pie_hud.png: real 1280x720 PIE capture with editor chrome;
  HUD overlap caused by normalized coordinates supplied as pixels.
- Art PIE fails pawn spawn and logs HUD Accessed None; exact geometry cause
  unproven. Inspected G0_art_corridor.png shows serious visual defects.
- EVIDENCE/G0_AUDIT.md records build/run/captures/reuse decisions.
- QUALITY_BAR.md proposed before G1 and added to REVIEW_QUEUE.md.
- Unattended commandlet rebuilt the production core/player/HUD/game mode and
  saved Production/Maps/Lvl_KL_School3_G1 through new_level_from_template.
  Exit 0 and G1_BUILD_AND_STAGE_COMPLETE. Four copied production props placed.
- Offscreen editor PID 16464 waited for an autosave recovery modal before map
  load. Engine source confirms unattended bypass. Saved/Autosaves backed up
  under ignored _g1_recovery_20260930 before stopping only that owned process.
- Replacement unattended editor PID 4812 loaded the production map and responds
  to MCP. Unrelated editor PID 38944 was left alone. Recheck both before action.
- Runtime uncovered automatic restart on bEnded, promoted math pin errors in
  the ray/HUD, reversed consumed prompt and an opening on the wrong hall wall.
  Those defects are repaired in production assets. Generator guards scalar
  types; Enter is required to restart, using the production map.
- G1_runtime_trial.json passed 17 checks in real PIE: initialization, prompt
  states, collection idempotence, tape interruption/completion, corroboration
  gating and measured beat timers. Debug method calls, not physical key input.
- G1_traversal_trial.json passed six waypoints with actual Move Blueprint /
  CharacterMovement collision, then focused the reachable attendance book.
- Inspected actual gameplay Shots: HUD positions separate after the double
  fraction repair; corrected light RGB removes the red/magenta cast. Scene
  remains graybox, text small, journal unwrapped: quality bar not achieved.
- G1_RUNTIME_REPAIR.md records scoped evidence and remaining requirements.
- Source audio measurements cover 12 WAVs: no clipped PCM samples; T2 16s,
  roll call 13s, reply 3.2s. RMS/spectrum are source engineering evidence only.

## Unqualified work
- Production runtime proof covers the repaired prototype foundation only.
  Physical keyboard, Enhanced Input injection and remapping remain unverified.
- No canonical sentence assembly, attention tiers, save/load, campaign ending,
  packaged Windows build or release verifier has been demonstrated.
- All G1-G5 gates remain incomplete. Full goal remains active.

## Next executable steps
1. Check owned editor PID 4812. Do not restart solely on an observation timeout;
   enable remote Python ephemerally on loopback only after MCP responds.
2. Implement the canonical school loop from revised V3 §§8, 9 and 13:
   dual listening, whole-sentence preview/seal, four consequential attention
   tiers, teacher/child loop and thầy Lâm. Existing beat is only a fixture.
3. Build readable wrapping Vietnamese UI; qualify actual controls and school
   progression through play and screenshots against QUALITY_BAR.md.
4. Proceed through G2-G5: all seven chapters, six ending branches, save/load,
   release verifier, packaged Windows RC and user signoff.

## Constraints
- Never create or edit user-owned HUMAN_SIGNOFF.md.
- Completion requires verify_release passing RC plus user signoff.
- No agent audio/scare acceptance; queue exact listening moments.
- DefaultEngine.ini excluded due to an existing token. Release needs sanitized
  configuration; never print the token.
- Remote Python enabled ephemerally on loopback; disable after work.
- Preserve concurrent SETUP.md/furniture changes; no bulk asset overwrites.
