"""Put the classroom opening on its actual side of the production hallway."""
import json
from pathlib import Path
import unreal

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
if world is None or '/Production/Maps/Lvl_KL_School3_G1.' not in world.get_path_name():
    raise RuntimeError('Only the copied production school may be edited')
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    raise RuntimeError('Stop PIE before changing the doorway')
expected = {
    'KL_HallWallN': -210, 'KL_HallWainN': -198,
    'KL_HallWallS1': 210, 'KL_HallWallS2': 210,
    'KL_HallWallSDoor': 210, 'KL_HallWainS1': 198, 'KL_HallWainS2': 198,
    'KL_DoorJambW': 205, 'KL_DoorJambE': 205, 'KL_DoorLintel': 210,
}
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
found = {}
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if label in expected:
        if label in found:
            raise RuntimeError('Ambiguous slab label: ' + label)
        found[label] = actor
if set(found) != set(expected):
    raise RuntimeError('Missing doorway slabs: ' + str(set(expected) - set(found)))
report = {'world': world.get_path_name(), 'changes': []}
for label, actor in found.items():
    loc = actor.get_actor_location()
    before = loc.y
    if not actor.set_actor_location(unreal.Vector(loc.x, expected[label], loc.z), False, True):
        raise RuntimeError('Could not position ' + label)
    report['changes'].append({'actor': label, 'before_y': before, 'after_y': actor.get_actor_location().y})
if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level():
    raise RuntimeError('Could not save copied school')
target = Path(unreal.Paths.project_dir()) / 'docs/agent/EVIDENCE/G1_doorway_repair.json'
target.write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report))
