# D002 — Lvl_KL_School3_Primary is the G1 target map

Date: 2026-09-30. Decided by the project owner during G1 preflight.

## Decision

All G1 work targets `/Game/KhoangLang/Production/Maps/Lvl_KL_School3_Primary`.
`Lvl_KL_School3_Merged` is a dead intermediate and must not be saved.

## Evidence

All times are local (the engine log writes UTC, 7 h behind).

- `tools/g1_merge_school.py` (17:19) built the merged working world from
  `Lvl_KL_School3_Art` architecture + staged Blender furniture + production
  gameplay, and `g1_promote_school_map.py` (17:32) saved it under the final
  primary package name. Primary is therefore a save-as **descendant** of the
  merged world, not a rival.
- `Lvl_KL_School3_Merged.umap` was last written 17:32:13. Three separate save
  attempts on it in that window **failed** with a Windows sharing violation:
  `Error moving file ... Lvl_KL_School3_Merged.umap ... (Error Code 32)`
  followed by `LogSavePackage: Error: Error saving`. Its on-disk content is
  whatever survived, not the merged-and-repaired state.
- `Lvl_KL_School3_Primary.umap` was written 17:32:58 and then received every
  later repair: `g1_primary_collision_repair.py` (17:42),
  `g1_primary_entry_repair.py` (17:51), `g1_primary_visual_repair.py` (18:49),
  `g1_primary_chalkface_repair.py` (18:49), `g1_primary_chalk_palette.py`
  (18:50). Latest on-disk write 18:49:07.
- The agent-owned editor (PID 34324) last loaded a map at 18:51:02 and it was
  `Lvl_KL_School3_Primary`. `EditorAppToolset.GetVisibleActors` returns actors
  whose object paths are all under
  `...Lvl_KL_School3_Primary.Lvl_KL_School3_Primary:PersistentLevel`,
  including `PlayerStart_0`, `BP_KL_Prop_ART_AttBook_C_1` and
  `BP_KL_Prop_ART_Roster_C_1`. **Primary is already the loaded map.**
- Recorded PIE evidence agrees: `G1_merged_runtime_trial.json` and
  `G1_traversal_trial.json` both report world
  `UEDPIE_0_Lvl_KL_School3_Primary`.
- `BP_KL_Character:PollKeys` restarts the player into
  `Lvl_KL_School3_Primary` (read from the graph as text).

## Asset-version safety

`MI_ART_Chalk.uasset` has on-disk mtime 18:50:58. The editor saved that file
itself at 18:50:58, four seconds before it loaded Primary at 18:51:02, so the
disk copy is the version the editor authored.

MCP cannot report unsaved changes: `AssetTools.is_dirty` returns
`Asset does not exist` like the other broken asset tools, and
`AssetTools.save_assets` takes an array argument, which this MCP bridge cannot
convert. **No asset will be saved from this session until a save path is
agreed.** Confirm the editor's Unsaved Assets panel is empty before G1 work
continues — that part is `[HUMAN-NEEDED]`.

## Consequences

- No map load is required; the editor is already on the target.
- `Lvl_KL_School3_Merged.umap` is retained as history only. It is untracked in
  Git, so the G1 baseline commit will capture it as-is.
