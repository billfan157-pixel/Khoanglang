# Production state

Current gate: G0 audit, incomplete.
Latest brief: user attachment goal-objective.md supplied on 2026-09-30.
Read this state and that brief at session start and after compaction.

## Verified facts
- Project: KhoangLang0217.uproject, engine association 5.8.
- Branch: production/g0-audit; initial source checkpoint 3ea094b.
- Git LFS is installed locally; binary tracking rules are configured.
- Initial commit preserves scripts and story; binary assets are not yet committed.
- Authoritative story source is docs/story/Khoang_Lang_02_17_Cot_truyen_v3.md, copied byte-for-byte from the user's 30/09/2026 update (1,132 lines).
- Source SHA256: 80EEE1981BF2A155726DA34617300647C1A9813B3D93F60628856B2E5EEC7E44.
- The previous complete 29/09 source and the older truncated source are preserved separately in docs/story/.
- Default map was changed to Lvl_KL_School3_Art and confirmed by live MCP.
- A viewport capture showed severe geometry/lighting issues; no visual pass claimed.
- Prior build_20 run returned exit 1 despite its own FAILURES: 0 report.
- Its engine log contains HUD Target connection errors and asset save failures.
- No successful end-to-end PIE path or packaged build has been demonstrated.
- No Unreal editor process was present at this continuation's initial inspection.

## Current changes awaiting verification
- Prior generator edits: pure getters, 16-second clear tape timer, journal gate.
- These changes are not runtime-qualified and must not be reported as working.
- kl_core.save now checks Unreal's result and avoids saving sibling assets.
- kl_core.compile now rejects BS_ERROR even if node error enumeration is empty.

## Next executable steps
1. Snapshot binary assets through LFS before further asset edits; exclude credentials.
2. Run isolated read-only asset load/compile audit with a unique log and report path.
3. Repair HUD Target links and execution wiring on duplicated assets.
4. Build and run G0 baseline, export and inspect screenshots in EVIDENCE.
5. Establish quality bar and review queue before G1; build verify_release honestly.

## Constraints
- HUMAN_SIGNOFF.md is user-owned: never create or edit it.
- Completion requires release verification plus user signoff.
- No audio quality or scare-effectiveness claim; provide measurements and review cues.
- DefaultEngine.ini is currently excluded from Git because it contains an existing token.
- Other production work was observed writing art files; avoid bulk asset overwrites.
