# Production state

Current gate: G0 baseline evidence collected; G1 runtime foundation in progress.
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
- Production core components and copied character/HUD/game mode compiled
  BS_UP_TO_DATE in G1_core_build.json and G1_player_build.json. Subsequent source
  refinements are not yet rebuilt: corner guards, cached filter choice,
  production tape sync and measured beat timing need a fresh run.
- Production copies of four props saved. New school map was not saved before
  world duplication crashed. g1_copy_school.py now uses new_level_from_template;
  that recovery path is not yet executed.
- Restarted editor PID 16464 is confirmed live; CPU increases but MCP queries
  time out during startup. Latest log reached engine initialization, frame 0.
  Do not restart on observation timeout; inspect this handle/log first.
- Source audio measurements cover 12 WAVs: no clipped PCM samples; T2 16s,
  roll call 13s, reply 3.2s. RMS/spectrum are source engineering evidence only.

## Unqualified work
- Baseline bodies are bypassed. Production helper now preserves execution,
  branches use sequences, audio calls target AudioComponent explicitly, and
  copied template inputs reconnect Move/Aim/Jump. Runtime proof is still missing.
- No canonical sentence assembly, attention tiers, save/load, campaign ending,
  packaged Windows build or release verifier has been demonstrated.
- All G1-G5 gates remain incomplete. Full goal remains active.

## Next executable steps
1. Check live editor PID 16464 and startup log; restore loopback remote Python
   only when MCP responds. Do not launch a second editor under RAM pressure.
2. Rerun g1_build_runtime.py, then g1_build_player.py with PIE stopped. These
   touch only production asset copies; baseline files must remain unchanged.
3. Run g1_copy_school.py (safe template API), start production-school PIE, run
   g1_runtime_trial.py and inspect its terminal report plus actual screenshots.
   That trial uses debug methods/world timers, not keyboard or canonical endings.
4. Diagnose collision/placement on copied level and prove navigable school route.
5. Implement canonical sentence and attention loop for G1, then all seven
   chapters and six ending branches through G2-G5.

## Constraints
- Never create or edit user-owned HUMAN_SIGNOFF.md.
- Completion requires verify_release passing RC plus user signoff.
- No agent audio/scare acceptance; queue exact listening moments.
- DefaultEngine.ini excluded due to an existing token. Release needs sanitized
  configuration; never print the token.
- Remote Python enabled ephemerally on loopback; disable after work.
- Preserve concurrent SETUP.md/furniture changes; no bulk asset overwrites.
