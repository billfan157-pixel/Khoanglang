---
name: kl-unreal-mcp-ops
description: How to drive Epic's Unreal MCP (list_toolsets, describe_toolset, call_tool, BlueprintTools, AssetTools, LogsToolset, PIE control) safely in the Khoảng Lặng project, including which tools are known to work or fail and the low-RAM rules for this machine. Use this skill before ANY call to the unreal-mcp server, before saving or compiling assets, before starting Play-In-Editor, and whenever a tool call fails, hangs, returns null, or the editor seems frozen.
---

# Operating the Unreal MCP

The MCP server runs inside the Unreal Editor process on `127.0.0.1:8000/mcp`. Tool calls run one at a time on the editor's game thread, so the editor freezes while a call runs and a careless call can cost the developer unsaved work. The rules below exist because of that.

## Connectivity preflight: never call a missing tool "a broken MCP"

The server runs inside the editor process, so it exists only while an editor holds the project. An editor started without a `.uproject` sits in the Project Browser and never loads the plugin, so port 8000 stays closed and every call fails. Before diagnosing anything, run:

```
powershell -NoProfile -ExecutionPolicy Bypass -File tools/mcp_doctor.ps1
```

Exit 0 means the endpoint is usable. Exit 1 prints the cause: no editor with the project, an editor without the project, or a project editor whose server never started. `-Launch` starts the editor on the `.uproject` with `-ModelContextProtocolStartServer` and waits for the handshake; ask the developer before starting the editor, since this machine has limited RAM.

Two consequences that look like failures but are not:

- **The agent has no `unreal-mcp` tools.** OpenCode connects once at startup and never retries, so a server that came up later is invisible until OpenCode is restarted. Restarting OpenCode is the developer's action, not yours. Meanwhile `python tools/ue_mcp.py toolsets` and `... call <toolset> <tool> args.json` reach the same endpoint directly.
- **A commandlet run has no server by design.** `LogModelContextProtocol: Auto-start skipped when running as a commandlet` is informational: the generator and verify scripts must not compete with a live editor for the port.

## Discovery: never guess a tool or parameter name

The server exposes three meta-tools: `list_toolsets`, `describe_toolset`, `call_tool`.

1. `list_toolsets` to see the capability groups available in this project. Use the fully-qualified toolset names exactly as returned.
2. `describe_toolset` for the group you need, and read the real parameter schemas.
3. `call_tool` with the toolset name, the short tool name, and arguments that match the schema.

The live schema is the contract. If this skill, a README, or your memory disagrees with it, the schema wins. Cache what you learn for the session. If the toolset list looks stale after the developer enabled a plugin, ask them to run `ModelContextProtocol.RefreshTools` in the editor console (you cannot run console commands through this MCP).

## Call discipline

- One logical step per call, strictly sequential. Never issue overlapping MCP calls: parallel calls against the game thread can deadlock or fail.
- Read every result. Many tools report failure inside the response body rather than as an error. Treat anything that is not an explicit success as a stop-and-diagnose.
- `compile_blueprint` returns null on success and gives no error detail. After every compile, read the log with `LogsToolset.GetLogEntries` (filter by the Blueprint name) and call the compile clean only if no matching errors or warnings appear.
- After writing a property, read it back. Some write paths silently do nothing.
- If a call hangs, a modal dialog is probably open in the editor. Stop and ask the developer to check the editor window. Do not retry blindly.
- Record the exact error text of any failure in `docs/agent/STATE.md`. Retry at most twice with a changed approach, then stop and report.
- Large outputs (base64 images, long logs): write to `Saved/agent_artifacts/` and summarize. Never paste them into the chat; they flood your context.

## Saving and undo

Edits live in memory until saved, and BlueprintTools has no undo, transaction, or checkpoint. A crash loses everything since the last save, and a bad Blueprint edit cannot be rolled back through the MCP. So:

1. Commit to git before any Blueprint or map edit (see `kl-repo-hygiene`).
2. Before saving an asset or map, compare its on-disk modified time with the time it was loaded into the editor. If the file on disk is newer, reload it from disk instead of overwriting it.
3. Know which map is open before you save. Never save a map you were not asked to touch.
4. Save after each milestone, not only at the end.

## Destructive operations

- `BlueprintTools.write_graph_dsl` is reported by a community project to delete nodes that are not connected, and to misjudge this on a localized (non-English) editor, which removed event nodes. Treat it as replace-the-graph: read the graph first, keep a text copy, use it only on a new or throwaway graph unless the user approves, and diff afterwards. Prefer small `create_node` / `connect_pins` edits on existing graphs after proving them on a throwaway asset.
- `ProgrammaticToolset.execute_tool_script` is a sandbox for batching tool calls (json, copy, math, datetime, time, re only; no `unreal` module, no exec/eval). It is not a way to run arbitrary editor code.
- Do not delete, rename, or move assets without asking.

## Low-spec machine rules

The developer's laptop has integrated graphics and often under 2 GB of free RAM. Running the editor, an agent, and a browser together can make Windows unresponsive.

- Before heavy work, check free memory (read-only):
  `powershell -NoProfile -Command "[math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB,2)"` prints free GB.
- Under about 2 GB free: no second editor instance, no commandlet, no full rebuild, no shader-heavy captures. Tell the developer what you want to run and let them decide.
- Never call `take_high_res_screenshot` or `take_automation_high_res_screenshot`: on this machine both recurse until a stack overflow. If you need a screenshot, ask the developer for one.
- Do not change engine or project settings (scalability, Lumen, shadow methods, CVars) without approval. Propose them, with the exact setting names obtained from the editor's own tools, and wait.
- Enabling plugins, starting remote Python on loopback, or any change that needs an editor restart requires the developer's explicit go-ahead.

## Known tool status

What has been seen to work, fail, or be missing on this machine is in `references/tool-status.md`. Read it before relying on a tool you have not used yet, and update it (with the date and the exact error) whenever you learn something new. A tool marked "not yet proven" must be proven on a throwaway asset first.
