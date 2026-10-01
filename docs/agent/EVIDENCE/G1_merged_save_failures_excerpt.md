# G1_merged_editor_runtime.log — save-failure excerpt

Extracted so the evidence behind `docs/decisions/D002` survives after the raw
log is untracked (see `docs/decisions/D003-lfs-coverage-no-history-rewrite.md`).
Machine-specific paths are removed; package names, error codes and log line
numbers are verbatim.

Source log: `docs/agent/EVIDENCE/G1_merged_editor_runtime.log`
Source size: 58032015 bytes, 219693 lines
Source SHA256: `86B3CB3C1AA364ADC2B18F7D817351AADB2DE2C1522A7D8FE293597B4A85A65B`
Git blob: `6e97a66e353f92be6d4095d0715521c68819182d`, added in commit `1eaede4`.

Save attempts in the log: 142. Failed: 6.

## Summary

| # | Package | Windows error code | Source line |
| --- | --- | --- | --- |
| 1 | `/Game/KhoangLang/Production/Maps/Lvl_KL_School3_Merged` | 32 | 2500 |
| 2 | `/Game/KhoangLang/Production/Maps/Lvl_KL_School3_Merged` | 32 | 2582 |
| 3 | `/Game/KhoangLang/Production/Maps/Lvl_KL_School3_Merged` | 32 | 2673 |
| 4 | `/Game/KhoangLang/Production/Blueprints/Player/BP_KL_Character` | 32 | 2769 |
| 5 | `/Game/KhoangLang/Production/Blueprints/Player/BP_KL_Character` | 32 | 2796 |
| 6 | `/Game/KhoangLang/Production/Maps/Lvl_KL_School3_Primary` | 32 | 2847 |

## Attempt 1 — `/Game/KhoangLang/Production/Maps/Lvl_KL_School3_Merged`

- L2488 `LogFileManager: Warning: MoveFile was unable to move 'Content/KhoangLang/Production/Maps/Lvl_KL_School3_Merged.umap' to 'Saved/Lvl_KL_School3_MergedEC60506E44A0F53645986799B9BEA9C1.tmp' (Error Code 32), retrying in .5s...`
- L2498 `LogFileManager: Error: Error moving file 'Content/KhoangLang/Production/Maps/Lvl_KL_School3_Merged.umap' to 'Saved/Lvl_KL_School3_MergedEC60506E44A0F53645986799B9BEA9C1.tmp'.`
- L2499 `LogSavePackage: Warning: Failed to move 'Content/KhoangLang/Production/Maps/Lvl_KL_School3_Merged.umap' to temp directory.`
- L2500 `LogSavePackage: Error: Error saving 'Content/KhoangLang/Production/Maps/Lvl_KL_School3_Merged.umap'.`

## Attempt 2 — `/Game/KhoangLang/Production/Maps/Lvl_KL_School3_Merged`

- L2570 `LogFileManager: Warning: MoveFile was unable to move 'Content/KhoangLang/Production/Maps/Lvl_KL_School3_Merged.umap' to 'Saved/Lvl_KL_School3_Merged8DC88C804C61A493C79434B5CC86A0FA.tmp' (Error Code 32), retrying in .5s...`
- L2580 `LogFileManager: Error: Error moving file 'Content/KhoangLang/Production/Maps/Lvl_KL_School3_Merged.umap' to 'Saved/Lvl_KL_School3_Merged8DC88C804C61A493C79434B5CC86A0FA.tmp'.`
- L2581 `LogSavePackage: Warning: Failed to move 'Content/KhoangLang/Production/Maps/Lvl_KL_School3_Merged.umap' to temp directory.`
- L2582 `LogSavePackage: Error: Error saving 'Content/KhoangLang/Production/Maps/Lvl_KL_School3_Merged.umap'.`

## Attempt 3 — `/Game/KhoangLang/Production/Maps/Lvl_KL_School3_Merged`

- L2661 `LogFileManager: Warning: MoveFile was unable to move 'Content/KhoangLang/Production/Maps/Lvl_KL_School3_Merged.umap' to 'Saved/Lvl_KL_School3_Merged0318239743DEC5CC718E4383EC15A891.tmp' (Error Code 32), retrying in .5s...`
- L2671 `LogFileManager: Error: Error moving file 'Content/KhoangLang/Production/Maps/Lvl_KL_School3_Merged.umap' to 'Saved/Lvl_KL_School3_Merged0318239743DEC5CC718E4383EC15A891.tmp'.`
- L2672 `LogSavePackage: Warning: Failed to move 'Content/KhoangLang/Production/Maps/Lvl_KL_School3_Merged.umap' to temp directory.`
- L2673 `LogSavePackage: Error: Error saving 'Content/KhoangLang/Production/Maps/Lvl_KL_School3_Merged.umap'.`

## Attempt 4 — `/Game/KhoangLang/Production/Blueprints/Player/BP_KL_Character`

- L2757 `LogFileManager: Warning: MoveFile was unable to move 'Content/KhoangLang/Production/Blueprints/Player/BP_KL_Character.uasset' to 'Saved/BP_KL_Character58CC397F4B4A7E980ACAAC95B79905FC.tmp' (Error Code 32), retrying in .5s...`
- L2767 `LogFileManager: Error: Error moving file 'Content/KhoangLang/Production/Blueprints/Player/BP_KL_Character.uasset' to 'Saved/BP_KL_Character58CC397F4B4A7E980ACAAC95B79905FC.tmp'.`
- L2768 `LogSavePackage: Warning: Failed to move 'Content/KhoangLang/Production/Blueprints/Player/BP_KL_Character.uasset' to temp directory.`
- L2769 `LogSavePackage: Error: Error saving 'Content/KhoangLang/Production/Blueprints/Player/BP_KL_Character.uasset'.`

## Attempt 5 — `/Game/KhoangLang/Production/Blueprints/Player/BP_KL_Character`

- L2784 `LogFileManager: Warning: MoveFile was unable to move 'Content/KhoangLang/Production/Blueprints/Player/BP_KL_Character.uasset' to 'Saved/BP_KL_Character47A4786646A58EC0F79603A3A3231E31.tmp' (Error Code 32), retrying in .5s...`
- L2794 `LogFileManager: Error: Error moving file 'Content/KhoangLang/Production/Blueprints/Player/BP_KL_Character.uasset' to 'Saved/BP_KL_Character47A4786646A58EC0F79603A3A3231E31.tmp'.`
- L2795 `LogSavePackage: Warning: Failed to move 'Content/KhoangLang/Production/Blueprints/Player/BP_KL_Character.uasset' to temp directory.`
- L2796 `LogSavePackage: Error: Error saving 'Content/KhoangLang/Production/Blueprints/Player/BP_KL_Character.uasset'.`

## Attempt 6 — `/Game/KhoangLang/Production/Maps/Lvl_KL_School3_Primary`

- L2835 `LogFileManager: Warning: MoveFile was unable to move 'Content/KhoangLang/Production/Maps/Lvl_KL_School3_Primary.umap' to 'Saved/Lvl_KL_School3_Primary8AADB1D7470798DE1AD55AB334A8964F.tmp' (Error Code 32), retrying in .5s...`
- L2845 `LogFileManager: Error: Error moving file 'Content/KhoangLang/Production/Maps/Lvl_KL_School3_Primary.umap' to 'Saved/Lvl_KL_School3_Primary8AADB1D7470798DE1AD55AB334A8964F.tmp'.`
- L2846 `LogSavePackage: Warning: Failed to move 'Content/KhoangLang/Production/Maps/Lvl_KL_School3_Primary.umap' to temp directory.`
- L2847 `LogSavePackage: Error: Error saving 'Content/KhoangLang/Production/Maps/Lvl_KL_School3_Primary.umap'.`

## Note on the D002 count

`D002` cites three failed saves on `Lvl_KL_School3_Merged`. The log contains
exactly 3 failed attempts on that package, matching the decision
record. The remaining failures are on `BP_KL_Character` and
`Lvl_KL_School3_Primary`.
