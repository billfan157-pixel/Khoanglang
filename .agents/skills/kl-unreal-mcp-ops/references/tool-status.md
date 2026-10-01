# Unreal MCP tool status (project-observed)

Source: Step 0 preflight audit and SETUP.md notes, engine 5.8.3, 2026-09-30 to 2026-10-01.
Update this file whenever you learn something new: add the date and the exact error text.
Re-verify on a throwaway asset after any engine, plugin, or MCP configuration change.

## Reliable (exercised and worked)

| Tool | Notes |
| --- | --- |
| `BlueprintTools.read_graph_dsl` | Returns a text (S-expression) form of a graph. Use before and after every edit. |
| `BlueprintTools.list_graphs` | Lists the graphs of a Blueprint. |
| `BlueprintTools.find_nodes` | Finds nodes by type, for example `WasInputKeyJustPressed`. |
| `BlueprintTools.compile_blueprint` | Returns null on success. No error detail: read the log afterwards. |
| `AssetTools.load_asset` | Resolves an asset to an object reference. Use the returned `refPath`. |
| `AssetTools.find_assets` | Search under `/Game`. Prefer it over `exists` and `list_folders`. |
| `LogsToolset.GetLogEntries(Category, Pattern, MaxEntries)` | The way to read compile errors and test output. |
| `EditorAppToolset.StartPIE / StopPIE / IsPIERunning` | PIE control. |
| `ProgrammaticToolset.execute_tool_script` | Batching sandbox only (see SKILL.md). |

## Available but not yet proven

Prove each on a throwaway asset before relying on it.

`create_node`, `connect_pins`, `break_pins`, `delete_node`, `set_pin_value`, `get_pin_value`, `add_variable`, `add_object_variable`, `add_function_graph`, `add_function_param`, `add_event`, `add_event_dispatcher`, `arrange_nodes`, `write_graph_dsl` (and `get_graph_dsl_docs`), `DataTableTools.*`, `DataAssetTools.create`, `ObjectTools.list_properties / get_properties / set_properties / reset_properties / search_subclasses`.

## Flaky (verified broken) and workarounds

| Tool | Failure | Workaround |
| --- | --- | --- |
| `AssetTools.get_asset_class` | "Asset does not exist" for every path form, even for assets `find_assets` returns | `load_asset`, then use the returned `refPath` |
| `AssetTools.exists` | Returns false for assets that `find_assets` returns | `find_assets` or `load_asset` |
| `AssetTools.get_dependencies`, `get_referencers` | Same "Asset does not exist" failure | Not used |
| `BlueprintTools.get_node_infos` | JSON could not be converted to a UStruct (reproduced twice) | `find_nodes` + `get_pin_value` + `read_graph_dsl` |
| `AssetTools.list_folders` with `recursive:false` | Returned `[]` for `/Game` although folders exist | `find_assets` |

## Unavailable

- Undo, transaction, checkpoint, snapshot: none anywhere in BlueprintTools. Mitigation: git commit before edits, text copy of the graph before and after.
- Creating a Blueprint struct (UserDefinedStruct) or enum: no tool; `BlueprintTools.create` only accepts UObject-derived classes. The only row structs available are engine-internal ones. Use one DataAsset per record (see `kl-blueprint-architecture`) or ask the developer to create the struct by hand.
- Console command execution: none. So no `Automation RunTests`, no `stat fps`, no CVar changes. `SearchCVars` is read-only.
- Calling an arbitrary function on a live PIE object: no tool.
- `import unreal` inside the MCP script sandbox: not possible.
- Input injection through the MCP: not available.

## Other machine observations

- Both Unreal screenshot entry points (`take_high_res_screenshot`, `take_automation_high_res_screenshot`) recurse until a stack overflow. Do not call them.
- `add_simple_collisions` returns -1 on an FBX import with no `UCX_` bodies. That is not a failure, but it also means no simple collision exists; meshes then use complex-as-simple.
- `UnrealEditor-Cmd.exe <project> <map> -game` exits immediately with "Running engine without a game" on this build, and a commandlet has no tick loop, so PIE cannot be driven headlessly here.
- Starting the full editor GUI can fail with 1.4-3.5 GB free RAM. Check free memory first.
- Two unattributed `LogAutomationTest: Error: Condition failed` lines appear at editor startup; their source is unconfirmed and they did not block anything.
