"""Record production PIE state and request an actual game-viewport screenshot."""
import json
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
world = subsystem.get_game_world()
if world is None or '/Production/' not in world.get_path_name():
    raise RuntimeError('Production PIE required')
pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
controller = unreal.GameplayStatics.get_player_controller(world, 0)
def vector(value):
    return [value.x, value.y, value.z]
report = {'world': world.get_path_name(),
          'game_time': unreal.GameplayStatics.get_time_seconds(world),
          'paused': unreal.GameplayStatics.is_game_paused(world),
          'pawn': pawn.get_path_name() if pawn else None,
          'controller': controller.get_path_name() if controller else None,
          'pawn_location': vector(pawn.get_actor_location()) if pawn else None,
          'components': [c.get_class().get_path_name() for c in
                         pawn.get_components_by_class(unreal.ActorComponent)] if pawn else [],
          'props': []}
for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
    if 'BP_KL_Prop_' in actor.get_class().get_name():
        report['props'].append({'class': actor.get_class().get_path_name(),
                                'location': vector(actor.get_actor_location())})
target = root / 'docs/agent/EVIDENCE/G1_runtime_worlds.json'
target.write_text(json.dumps(report, indent=2), encoding='utf-8')
unreal.SystemLibrary.execute_console_command(world, 'Shot')
print(json.dumps(report))
