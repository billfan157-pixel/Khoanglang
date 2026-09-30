# Production state

Current gate: G0 audit, incomplete.
Latest brief: user attachment goal-objective.md supplied on 2026-09-30.
Read this state and that brief at session start and after compaction.

## Verified facts
- Project: KhoangLang0217.uproject, engine association 5.8.
- Branch: production/g0-audit; initial source checkpoint 3ea094b.
- Git LFS is installed locally; binary tracking rules are configured.
- Initial commit preserves scripts and story; binary assets are not yet committed.
- Full story source is docs/story/Khoang_Lang_02_17_Cot_truyen_v3.md.
- Source header says 29/09/2026; the new brief says updated 30/09/2026.
- Full source SHA256: 69F7B1C07BCAD1C14055171B685DE502BC0D1E5D735820861AD694F3E6D21921.
- Older truncated source was preserved separately.
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
