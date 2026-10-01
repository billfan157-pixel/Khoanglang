# Milestones and gates

STATE.md records which gate is current. This file records what each gate means so every agent
session judges "done" the same way.

## G1 - one human-playable classroom loop

Goal: find out whether the core listening mechanic is engaging. It is not a content milestone.

Done only when all of these hold:

1. The project builds and compiles cleanly; compile results were checked in the log, not only the return value.
2. Rule tests pass: independent source required, wrong-seal outcome, every Attention transition, data loads without errors. Label: [SCRIPTED].
3. A full loop is possible in Play-In-Editor: collect clues -> compare recordings -> Try Listening -> Seal one sentence -> see the result and an Attention change. Label: [PIE-SIMULATED] until a human has played it.
4. The developer has played the loop with a real keyboard and mouse and reported what was confusing or dull. Label: [HUMAN-NEEDED] until then.
5. STATE.md separates scripted, simulated and human-needed items, and passes `lint_claims.py`.

Explicitly out of scope for G1: campaign structure, save/load, additional chapters, endings, packaging, multi-sentence set sealing and the "partially correct" result (these are deferred, not forgotten; list them in STATE.md).

## G2 - vertical slice (45-60 minutes)

- Replace every `prototype_only` scaffold with canon-correct content (or a recorded decision to keep it).
- At least one tape with real audio and a degraded-listening filter; the developer judges it by ear.
- Save/load, opening and ending screens, accessibility text readout of the waveform state.
- One Windows packaging trial early, when the machine has free RAM.
- Three to five outside playtesters; screen recordings kept outside the repo.

## G3 - Hồi 1-3 standalone episode (about 8-10 hours)

Only start after G2 passes and the playtest feedback is written down.

## Gate discipline

- Never mark a gate passed from scripted evidence alone when the gate has a human-needed item.
- When a gate fails, record why in STATE.md and fix the cause; do not lower the criteria.
