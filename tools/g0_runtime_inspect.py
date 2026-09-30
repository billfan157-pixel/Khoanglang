"""Inspect the active editor and PIE worlds without changing assets."""

import json
from pathlib import Path
import unreal


root = Path(unreal.Paths.project_dir())
report = {"worlds": [], "game_mode_defaults": {}}
gm_asset = unreal.load_asset("/Game/KhoangLang/Blueprints/Player/BP_KL_GameMode")
gm_default = unreal.get_default_object(gm_asset.generated_class())
for prop in ("default_pawn_class", "player_controller_class", "hud_class",
             "start_players_as_spectators"):
    value = gm_default.get_editor_property(prop)
    report["game_mode_defaults"][prop] = (
        value.get_path_name() if hasattr(value, "get_path_name") else str(value))
sub = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
for label, world in (("editor", sub.get_editor_world()),
                     ("game", sub.get_game_world())):
    if world is None:
        report["worlds"].append({"kind": label, "world": None})
        continue
    actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
    controller = unreal.GameplayStatics.get_player_controller(world, 0)
    settings = world.get_world_settings()
    game_mode = settings.get_editor_property("default_game_mode")
    entry = {
        "kind": label, "world": world.get_path_name(), "actors": len(actors),
        "pawn": pawn.get_path_name() if pawn else None,
        "controller": controller.get_path_name() if controller else None,
        "default_game_mode": game_mode.get_path_name() if game_mode else None,
        "player_related_actors": [],
    }
    for actor in actors:
        name = actor.get_class().get_name()
        if any(s in name for s in ("PlayerStart", "Character", "Controller", "HUD")):
            loc = actor.get_actor_location()
            entry["player_related_actors"].append({
                "class": name, "path": actor.get_path_name(),
                "location": [loc.x, loc.y, loc.z],
            })
    if pawn:
        entry["components"] = [c.get_class().get_name() for c in
                               pawn.get_components_by_class(unreal.ActorComponent)]
    report["worlds"].append(entry)
target = root / "docs/agent/EVIDENCE/G0_runtime_worlds.json"
target.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
