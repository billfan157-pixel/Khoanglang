# School map entry point

The active G1 school is `/Game/KhoangLang/Production/G1Canon/Lvl_KL_SchoolSlice`.
Open `Content/KhoangLang/Production/G1Canon/Lvl_KL_SchoolSlice.umap`.
Both `EditorStartupMap` and `GameDefaultMap` select this map.

## Retired staging maps (2026-10-01)

The user requested removal of redundant school maps. These three assets have
been removed from `Content/KhoangLang/Production/Maps`:

- `Lvl_KL_School3_G1`: initial production copy.
- `Lvl_KL_School3_Merged`: intermediate merged classroom.
- `Lvl_KL_School3_Primary`: promoted prototype used as the source for G1Canon.

Primary was a source template, not the current school. G1Canon contains the
later native player, listening loop, mesh repairs and lighting checkpoint.
The original `Content/KhoangLang/Maps` assets remain source/reference material.

[SCRIPTED] Live registry queries returned no incoming asset references for the
three retired maps. A positive control returned SchoolHUD and SchoolSlice as
referencers of SchoolLoop. The active map loaded with zero MapCheck errors and
warnings; its bytes and default routing were unchanged by cleanup.
Evidence: `docs/agent/EVIDENCE/G1_MAP_CLEANUP_20261001.json`.

## Historical tools and recovery

Old copy/merge/promote/Primary repair tools and old G0 reports document an
earlier prototype. Do not run them as current authoring or verification tools.
In particular, `g1_set_primary_map_defaults.py` selects a retired map;
`g1_stage_school.py` needs the retired Primary source and can rebuild G1Canon;
`g1_retire_school_copies.py` describes an earlier, different deletion set.
Legacy name-based restart paths are also historical prototype behavior.
Restore the historical maps first if deliberately reproducing that prototype.

Recovery tag: `g1-before-map-cleanup-20261001t044238z`.
Verified raw backups: `_release_work/g1_map_cleanup_20261001T044238Z/` (ignored).
Restore only the desired map files from the tag or backup, with PIE stopped
and a different map loaded. Reload the asset registry afterward.
Do not reset the whole working tree; unrelated concurrent work is present.
