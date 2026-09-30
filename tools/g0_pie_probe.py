"""Read live Blueprint state and request a real PIE screenshot."""

import json
from pathlib import Path
import unreal

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
if world is None:
    raise RuntimeError("No PIE world")
pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
if pawn is None:
    raise RuntimeError("No player pawn")
report = {"world": world.get_path_name(), "components": [], "props": []}
for comp in pawn.get_components_by_class(unreal.ActorComponent):
    name = comp.get_class().get_name()
    if name.startswith("BP_KL_"):
        entry = {"class": name, "state": {}}
        for prop in ("bHasDoc", "bHasTape", "bTapeHeard", "bCorroborated",
                     "bRevealed", "bBeatDone", "bEnded", "JournalOpen",
                     "ObjectiveText", "SubtitleText", "bFilterOn", "bStarted"):
            try:
                entry["state"][prop] = str(comp.get_editor_property(prop))
            except Exception:
                pass
        report["components"].append(entry)
for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
    if "BP_KL_Prop" in actor.get_class().get_name():
        loc = actor.get_actor_location()
        report["props"].append({"class": actor.get_class().get_name(),
                                "location": [loc.x, loc.y, loc.z]})
unreal.SystemLibrary.execute_console_command(world, "Shot showui")
target = Path(unreal.Paths.project_dir()) / "docs/agent/EVIDENCE/G0_graybox_initial_state.json"
target.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(report, indent=2, ensure_ascii=False))
