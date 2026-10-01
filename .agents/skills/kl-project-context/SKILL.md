---
name: kl-project-context
description: Orientation for the Khoảng Lặng 02:17 Unreal Engine horror-game repository. Load this FIRST at the start of any task in this repo, and again whenever you are unsure what the game is, where story canon lives, which milestone gate is current, what a Vietnamese term means, or whether a change might contradict the story. Use it before touching story data, levels, Blueprints, HUD text, audio, or docs, even for small edits.
---

# Khoảng Lặng 02:17 - project context

## What this project is

A first-person psychological horror / mystery game made by one developer working with AI agents.

- Engine: Unreal Engine 5.8.3, project `KhoangLang0217.uproject`. Blueprint-first. Add C++ only for a concrete requirement Blueprint cannot meet cleanly, and only after the user confirms.
- Player-facing text is Vietnamese. Identifiers, asset names, file names and code are English and ASCII.
- Pillars: environmental audio, evidence collection, and the "Nghe cho hết câu" listening mechanic. There is no combat system. Keep every slice small.
- Tooling: OpenCode driving Epic's experimental Unreal MCP (loopback only). The developer's machine is a low-spec Windows laptop with integrated graphics and little free RAM, so heavy operations need care (see `kl-unreal-mcp-ops`).
- You cannot see the screen, hear audio, or press real keys. Anything that depends on those is the human's to judge (see `kl-verification`).

## Where things live

| Need | Location |
| --- | --- |
| Story canon (READ-ONLY) | `docs/story/Khoang_Lang_02_17_Cot_truyen_v3.md`, `docs/story/OPEN_QUESTIONS_V3.md` |
| Current status and what is verified | `docs/agent/STATE.md` |
| Evidence files | `docs/agent/EVIDENCE/` |
| Decision records | `docs/decisions/D###-short-name.md` |
| Technical notes | `docs/tech/` |
| Story as data | `data/story/` (see `kl-story-data`) |
| Generator and verifier scripts | `tools/`, `Content/Python/KhoangLang/` (see `kl-repo-hygiene`) |

If a path above does not exist yet, say so and ask before inventing a new location.

## Starting any task

1. Read `AGENTS.md`, then `docs/agent/STATE.md`. If STATE.md contradicts this skill, STATE.md wins; mention the contradiction.
2. Load the skill that matches the work: MCP calls -> `kl-unreal-mcp-ops`; Blueprints and level logic -> `kl-blueprint-architecture`; any claim about results -> `kl-verification`; clues, sources, NPC knowledge -> `kl-story-data`; commits and generators -> `kl-repo-hygiene`; any Vietnamese text -> `kl-vietnamese-text`.
3. Read only the canon sections the task needs. The canon is long; quote section numbers (for example "V3 section 8.2") instead of re-reading all of it each time.
4. State your plan in a few lines before editing, including which files or assets you will touch.

## Canon rules

The canon exists so the story stays consistent across hundreds of small agent edits. Contradictions are expensive because they surface chapters later.

- Never edit canon files.
- Do not silently rewrite or contradict facts, the timeline, character motives, entity rules, or endings.
- If an implementation needs something the canon does not say, do not invent it. Pick the smallest reversible choice, mark it `prototype_only`, and record it in `docs/decisions/` with the canon section it deviates from and what must be revisited.
- Ask the user first (one focused question) before: changing the timeline or fixed facts, adding named characters or lore, changing an entity's rules, enabling plugins, changing engine or project settings, deleting files, pushing to a remote.
- Keep gaps visible: add new unanswered questions to `docs/agent/OPEN_QUESTIONS.md` rather than answering them yourself.

## Milestones (the current gate is recorded in STATE.md)

- G1: one complete, human-playable loop in the primary-school classroom: collect clues -> compare recordings -> Try Listening -> Seal one sentence -> see the result and an Attention change.
- G2: vertical slice of 45-60 minutes with real audio, save/load, a Windows packaging trial, and outside playtesters.
- G3: Hồi 1-3 as a standalone episode. Only after G2 passes.

Do not start work that belongs to a later gate. Details and acceptance criteria: `references/milestones.md`.

## Glossary (confirm exact wording against V3 before using in player-facing text)

| Term | Meaning |
| --- | --- |
| Nghe cho hết câu | Core listening mechanic: listen to the whole sentence before judging it |
| Thử nghe | Try Listening: free preview of a reading of a cut sentence |
| Niêm phong | Seal: commit a reading; costs time and raises Attention |
| Sự chú ý | Attention; four tiers (G1 data names: Yên, Nghe thấy, Nhận ra, Tìm đến) |
| Kênh hiện tại / Kênh hồi âm | Present channel / echo channel of the listening device |
| Độc lập / Có liên quan / Có lợi ích | Source labels: independent / related / interested (ids `independent`, `related`, `interested`) |
| Hồi | Chapter or act; V3 has seven |
| T1, T2, T3 | The recordings; per V3 section 3, T3 is the only independent recording |

Extend this table from the canon when a new term appears; do not guess meanings.
