# AGENTS.md — Khoảng Lặng 02:17

## Project intent
Build a first-person 3D psychological horror game in Unreal Engine. The narrative reference is `docs/story/Khoang_Lang_02_17_Cot_truyen_v3.md` (V3, originally dated 2026-09-29, updated 2026-09-30).

## Narrative and scope
- Treat V3 as source material. Do not silently rewrite or contradict its facts, timeline, character motives, rules, or endings.
- Keep the first playable slice small: first-person exploration, environmental audio, evidence collection, and the “Nghe cho hết câu” mechanic before expanding levels or enemy systems.
- Start with Blueprint. Add C++ only for a concrete requirement that Blueprint cannot handle cleanly.
- Preserve Vietnamese names, diacritics, and terminology in player-facing text and source documents.
- Ask for a focused design decision if an implementation would change established story canon; otherwise make reversible choices and document them.

## OpenCode and Unreal MCP
- Keep Unreal MCP configuration project-local; do not edit the user's global OpenCode config or provider credentials.
- The project enables Epic's built-in `ModelContextProtocol` and `EditorToolset` plugins. Keep the MCP endpoint on loopback (`127.0.0.1`) and never expose it to the network.
- These engine plugins are experimental. Do not add third-party Unreal plugins or MCP servers without reviewing source, license, engine-version support, and install steps first.
- Keep generated assets out of narrative source files. Do not commit credentials, account data, or machine-specific absolute paths.

## Current setup
The project uses Unreal Engine 5.8.3 and the engine's First Person Blueprint template. Project-local OpenCode MCP settings are in `opencode.jsonc`. Read `SETUP.md` for machine constraints and verification status.

## Skills

Project skills live in `.agents/skills/<name>/SKILL.md`. Read the matching SKILL.md with normal file tools before starting the work; there is no separate client-side skill-loading tool in this session. Read Unreal server AgentSkills through their native MCP registry.

Before selecting app or project skills, read [.agents/skill-router.md](.agents/skill-router.md). It maps task scope to the relevant sources and records current tool/schema caveats; load conditional references only when needed.

| When you are about to... | Load |
| --- | --- |
| start any task, or are unsure about canon, gates, terms | `kl-project-context` |
| call the Unreal MCP, compile, save, or start PIE | `kl-unreal-mcp-ops` |
| create or edit a Blueprint, widget, GameMode, or data asset | `kl-blueprint-architecture` |
| say that something works, is verified, fixed, or done; write STATE.md or tests | `kl-verification` |
| add or change clues, sources, puzzles, NPC knowledge, or revealed facts | `kl-story-data` |
| commit, tag, run a generator, edit a map, or add files to the repo | `kl-repo-hygiene` |
| write or display any Vietnamese text | `kl-vietnamese-text` |
| art-direct a location or prop and need real Vietnamese regional evidence | `kl-vietnam-world-research` |

Precedence: canon (`docs/story/`) and the user's decisions say WHAT to build; `docs/agent/STATE.md` says where the project is; skills say HOW to work. If a skill contradicts the live MCP schema, the schema wins. If a skill is wrong or out of date, tell the developer and propose the fix; do not silently ignore it.
