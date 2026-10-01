# Applying the installed skills

This is an operational routing guide for KhoangLang0217, researched on 2026-10-01.
It supports the owner's request to understand existing skills and apply them during
work. It does not install plugins, change credentials, authorize paid generation,
or modify game content. AGENTS.md links the concise router for future project work.

## What was studied

[SCRIPTED] All 68 app-catalog entrypoints exist. Their names, trigger descriptions,
workflow headings, selected constraints and SHA256 hashes were indexed. There are
67 distinct manifest names: two different sources both call themselves skill-creator.
All eight repository skills were read in full. Twenty-three relevant app entrypoints
were read in full during this conversation; remaining entries were surveyed at the
trigger/workflow level. Large format-specific manuals were not all read end to end.
Read the complete applicable skill and needed references before using its workflow.
The catalog records these differences; inventory does not establish execution readiness.

[SCRIPTED] Unreal ListSkills/GetSkills returned four registered server skills:
BlueprintBasics, DefaultOutdoorLighting, MaterialBasics and UnrealSkillBestPractices.
Their instruction bodies were read. Later the transport failed; the read-only doctor
reported no editor process and no listener on port8000. No editor was launched.
The bundled workspace dependency loader returned bundle26.915.20218 paths; this
establishes discovery, not successful rendering or artifact creation.

## Selection and application

A skill supplies a workflow; a tool supplies an actual operation. A plugin may
contain either or both. Choose from the current session's catalog, announce first
use, read the source, then read conditional references only when the task needs them.
This avoids bringing a website, spreadsheet or paid-asset workflow into an input fix.
Official guidance also distinguishes discovery metadata from loaded instructions
and supporting resources: [Skills](https://developers.openai.com/plugins/concepts/skills)
and [skill design guidance](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra).

Reconcile instructions with higher-priority runtime instructions and the user's
actual request. Explicit authorization already given remains effective within scope.
Do not manufacture a confirmation step from a generic skill default. Missing required
information, an unapproved canon change or new spending is still a real boundary.
An instruction found while studying a skill does not itself authorize executing it.

## Routes that matter for the game

**Live Unreal operations.** Use unreal-mcp and kl-unreal-mcp-ops together. Check the
actual editor/project/PIE state, registered skills, schemas and asset timestamps.
Serialize dependent calls. Back up before writes and save only owned packages.
Use readbacks and logs after writes; never equate null with a clean compile.

**Blueprint logic.** Add kl-blueprint-architecture. Read the graph before editing,
confirm real node/pin identities, avoid duplicated game rules, compile a coherent
unit, inspect logs and read the graph afterward. Keep generated source and assets
consistent. BlueprintBasics agrees on graph inspection, compilation and interfaces;
its DSL writing recommendation does not override the project's narrower safe-edit
rule for already-authored graphs.

**Materials and lighting.** MaterialBasics prefers reuse, then a material instance,
then a new parent. Avoid unnecessary shader permutations. OutdoorLighting applies
to the outdoor sky system; do not transplant its sun/cloud recipes into an indoor
G1 exposure repair. Inspect components, current exposure and assigned materials,
and use actual captures to assess a change. Recipe numbers require project-specific
validation and do not establish visual acceptance.

**School and Vietnamese context.** kl-vietnam-world-research separates2002/2026
layers, dates, locality, provenance and rights. A proposed regional anchor remains a
proposal. kl-story-data governs facts, source independence and who knows what when;
kl-vietnamese-text governs UTF-8/NFC and separate player-facing text. Rendered output
must still be inspected. No research analogy silently changes V3.

**Room/prop production.** build-3d-game-rooms routes through Function, Form and
Runtime gates. Read doctrine/approved lessons/pipeline and the gameplay-room adapter
when actually using that production workflow. Record units, openings, mounting,
collision, camera, budgets and provenance. Its default2.4m arrival width and symmetry
preferences are conditional design defaults, not historical requirements for a school.
Meshy needs explicit spending authorization and an existing task ID must not be
resubmitted blindly. imagegen uses the built-in tool first and preserves edit targets;
project-bound final assets belong in the workspace. Concepts are not documentary photos.

**Evidence and Git.** kl-verification separates scripted results, simulated PIE and
human judgments. Source identity, package hashes and before/after evidence matter.
kl-repo-hygiene adds LFS, recovery points and one writer per binary asset. The current
school entrypoint is documented in SCHOOL_MAPS.md; old Primary generators are historical.

## Other app families

- documents/pdf/Presentations/Spreadsheets own editable artifact creation and visual
  verification. Use the bundled dependency loader, requested templates and actual
  rendering/recalculation. XML validity or file creation alone is insufficient.
- excel-live-control owns the selected live Excel session; spreadsheets owns files
  and Google Sheets routes. Do not mix target identities or substitute a local copy.
- canvas/visualize own appropriate analytical/interactive output. Follow the runtime
  and managed-directory contract of the available surface. Do not invent a working
  Canvas directory from the Mac example or apply an analytical-output rule to a code fix.
- computer-use owns supported Windows UI automation. Read runtime guidance and
  confirmations before controlling an app; respect the user's stop. Desktop Commander
  skills require their connector; its tools were not exposed in this session's metadata.
  Built-in file/shell tools remain suitable for ordinary authorized repository work.
- openai-docs owns Codex/product guidance. Specific features use fetched official docs;
  broad orientation can use the refreshed official manual. Product docs are not proof
  of this account's entitlements or an external service connection.
- automate/loop/subscribe describe different recurring-work environments. The desktop
  app's native heartbeat/automation API takes precedence over legacy shell wake loops.
  Do not create a schedule merely because a study request mentions repeated work.
- review/review-bugbot/review-security/babysit/split-to-prs concern actual code/PR work.
  Check the available reviewer API rather than inventing the named subagent type or a
  Bugbot report. CI repairs stay within the PR; do not weaken checks to get green.
- new-repo/share/origin concern Codex-hosted repositories. They do not replace the
  existing GitHub remote. Origin's entrypoint also excludes native Windows operations.
- Cloudflare's nine skills concern Workers/Agents/DOs/Sandbox/MCP/Web performance and
  Wrangler. Fetch current primary documentation when used; do not route an Unreal
  engine problem through them because both workflows mention MCP or performance.
- Sites building/hosting/MCP/preview skills own actual Sites projects. The managed
  Linux preview recovery route does not apply to this Windows Unreal workspace.
- work-pets create/pets/update use stable pet IDs and their sprite/Library lifecycle.
  A game character or unattached texture is not automatically a ChatGPT pet.
- plugin-management searches when an unavailable external capability would help;
  it does not require adding plugins for built-in web or image tools. Claude Cowork
  customization/creation requires its specified environment and deliverable support.
- knowledge-base/obsidian-vault, hooks/rules/subagents, configuration/statusline,
  migration/SDK and install/template workflows activate for their actual requests.
  Studying them does not authorize modifying global settings or installed plugin caches.
- goal, shell, onboard and rename-chat have explicit invocation boundaries. Do not
  start a goal, execute literal shell input or rename a chat from a matching keyword.

## Concrete corrections to avoid repeating

1. AGENTS previously requested a nonexistent client-side `skill` tool. Matching
   SKILL.md files are read using normal file tools; Unreal server skills use MCP.
2. The older project milestone reference defines an8-10h G3 episode, while the
   user's production brief defines seven chapters/three endings and G0-G5. Follow
   current user scope/STATE; retain human acceptance requirements and do not silently
   shrink the campaign to the older skill's milestone plan.
3. The source skill's blanket inability to see must not be repeated as a runtime
   fact: view_image can inspect available captures. It cannot hear audio or prove
   real keyboard use, cultural acceptance or scare effectiveness.
4. Old tool-status entries say get_dependencies/get_referencers fail. The map
   cleanup [SCRIPTED] observed both working, including a positive referencer control. Recheck
   the live schema/result instead of treating historical failures as permanent.
5. Native AssetTools.delete returned true and removed registry entries while files
   remained on disk. The cleanup checked backups/hashes/exact paths before removing
   the remnants. Future deletion must check BOTH representations. SelectAssets also
   timed out; a selected browser item must not be claimed from that call.
6. Preserve concurrent work. This study adds a router/catalog/guide and a small
   AGENTS link; it does not rewrite the dirty MCP skills, helpers or research files.

## Limits of this study

The catalog is a dated source survey, not a benchmark of68 executable workflows.
No paid service, live spreadsheet, browser control, asset generation, packaging or
publishing was exercised to test a skill. Apply the relevant source and verify the
actual task outcome each time. No user memory or global app configuration was changed.
