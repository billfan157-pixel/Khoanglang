# G0 baseline audit — 2026-09-30

Source checkpoint: `ffc85df`, branch `production/g0-audit`. Existing prototype
and art sources are preserved through Git LFS. This audits the baseline; it
does not accept a playable slice or a packaged game.

## Build and run

- Initial Blueprint audit failed: HUD component targets were disconnected.
- Duplicate rebuild proved the generated Blueprint class must be supplied to
  ComponentClass. After narrow canonical HUD repair, a fresh commandlet exited
  0; G0_2026-09-30_build40_after_hud.txt reports 0 failures, 38 connected HUD
  targets and 8 CompleteClearTape nodes. Asset-validator API was unavailable.
- Graybox PIE creates a possessed pawn, investigation/listening components,
  and all four interaction props. See G0_runtime_worlds.json and
  G0_graybox_initial_state.json.
- Game time advanced from 492.43 to 572.44 seconds, pause false; StartBeds stayed
  false. G0_graph_runtime_audit.json shows InitKL entry wired directly to Return,
  bypassing its body. ret() overwrites the entry execution link. Its InitRun
  execution and component targets are disconnected.
- IA_Move/IA_Look/IA_MouseLook/IA_Jump events have no execution links. The graph
  clear helper kept input events while deleting handlers.
- Art-map PIE failed to spawn a pawn, also at a raised test start. Exact blocking
  geometry is not proven. HUD then emitted Accessed None without a pawn.

## Screenshots inspected

- G0_graybox_pie_hud.png: real PIE Shot showui, 1280x720 including editor chrome.
  Corridor visible; HUD overlaps top-left. Normalized coordinates were supplied
  to pixel arguments of DrawText/DrawRect.
- G0_art_corridor.png: editor viewport, not a player screenshot. Large red
  obstruction, white clipping and near-black surroundings.
- G0_graybox_entry.png: editor viewport capture, not the pawn camera. Do not use
  as proof of first-person gameplay.

## Reuse inventory and provenance

| Material | Decision | Evidence / limits |
| --- | --- | --- |
| Full revised V3 | Keep authoritative | Exact supplied source; older versions preserved |
| Evidence definitions / Vietnamese text | Reuse with canon review | Loads; classroom clues are prototype echoes |
| Investigation/listening/interaction design | Rebuild wiring on copies | No-op returns and typed component failures |
| Movement functions and input actions | Reuse and restore handlers on copy | Installed Epic First Person template |
| Graybox school | Reuse measurable baseline | Pawn spawns; doorway/traversal unverified |
| Modular kit and materials | Retain source; qualify dimensions/collision | Original procedural scripts; visuals fail |
| Blender desk/bench | Retain for staging | Original modelling script and FBX; no visual acceptance |
| Synthetic WAVs | Engineering placeholders only | Original synthesis script; no final performances |
| Canvas HUD | Reuse text; repair copied layout | Current text unreadable |

No third-party asset was downloaded. Engine template content retains its
installed Epic distribution terms. No release-rights audit, Windows package,
save/load, ending playthrough, performance or audio acceptance is claimed.

Baseline build/run/capture/reuse evidence is collected. Proceed to G1 with a
production namespace and copied level. Repair execution, input and HUD before
authoring the canonical sentence and attention loop. Full goal remains active.
