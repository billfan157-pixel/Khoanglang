---
name: kl-verification
description: Verification and reporting protocol for the Khoảng Lặng project - the three evidence labels ([SCRIPTED], [PIE-SIMULATED], [HUMAN-NEEDED]), what an agent can and cannot verify here, how to write rule self-tests with a negative control, how to keep docs/agent/STATE.md honest, and how to produce a human playtest checklist. Use this skill whenever you are about to say that something works, is verified, is fixed, passes, or is done; when you write or update STATE.md or any evidence file; when you write tests; and when you finish a task or milestone gate.
---

# Verification protocol

The agent in this project cannot see the screen, hear audio, or press real keys. An earlier report said "17/17 checks passed" while real keyboard input had never worked (a key-literal bug was hiding in the generator). Scripted checks prove that code does what the code says; they say nothing about whether the game is playable, readable, or frightening. This protocol keeps the report honest about that gap, so the developer's limited attention goes where it is needed.

## The three labels

Attach exactly one to every claim about results.

| Label | Meaning | Examples |
| --- | --- | --- |
| `[SCRIPTED]` | An automated check passed and the developer can re-run it | Rule self-test output, validator exit code, file or asset census, compile log with no errors |
| `[PIE-SIMULATED]` | Exercised in Play-In-Editor through function calls or injected input, not through a real device | A scripted walk through the full loop |
| `[HUMAN-NEEDED]` | Only a person can judge it | Real keyboard and mouse, readability, lighting, sound, pacing, whether it is scary or fun |

Rules:

- Never write "verified", "works", or "fixed" without a label. Never put `[SCRIPTED]` on anything about real input, looks, sound, or feel; those are always `[HUMAN-NEEDED]`.
- A number like "17/17 checks" must say what the checks cover ("rule logic, scripted").
- "Compiles clean" means the log was read after compiling, not that the return value was null.
- Say what you did not verify. A short honest list beats a long confident one.

## Self-tests for rule logic

Rule logic is the part an agent can really verify. Put the tests in a separate non-shipping map or behind an explicit enable flag, never in the gameplay map's BeginPlay, so normal play does not run test code or write test lines to the log.

- Run through Play-In-Editor and read the results with `LogsToolset.GetLogEntries`.
- Output one JSON line per case: `{"case":"...","expected":"...","actual":"...","result":"PASS|FAIL"}`, then one summary line with total, passed, failed.
- Include one deliberate negative control: a case whose expected result is asserted to be a failure of the rules function. If the harness cannot report a FAIL, a column of PASS lines means nothing.
- Cover at least: the independent-source requirement, the wrong-seal outcome, every Attention transition, and that data assets load without errors.

## Evidence files

- Save evidence to `docs/agent/EVIDENCE/<id>_<what>.md` or `.json`: the tool or command, the date, the raw result, the label. Keep large artifacts in `Saved/agent_artifacts/` and link them.
- STATE.md has three sections, in this order: `[SCRIPTED]`, `[PIE-SIMULATED]`, `[HUMAN-NEEDED]`. Move an item to a higher-confidence section only when the evidence supports it.
- Run the linter on every status document before you finish:
  `python .agents/skills/kl-verification/scripts/lint_claims.py docs/agent/STATE.md`
  It flags unlabeled claims and human-only claims labeled as scripted. It is a review aid: fix each finding by adding the right label or by rewording the claim.

## Handing work to the human

At the end of a task, produce a playtest checklist the developer can follow in ten minutes. Use `references/human-playtest-template.md`, written in Vietnamese with technical IDs left in English. Tell the developer exactly which build or map to open and what to report back. Their observations of confusion and boredom are the most valuable data the project gets; ask for them specifically.

## Finishing a gate

A gate with a `[HUMAN-NEEDED]` item is not passed until the developer has done that item. Say "ready for human test" rather than "done". See `kl-project-context/references/milestones.md` for the criteria of each gate.
