"""Correct reversed red/blue light channels in the production school copy."""
import json
from pathlib import Path
import unreal
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
if world is None or '/Production/Maps/Lvl_KL_School3_G1.' not in world.get_path_name():
    raise RuntimeError('Production school required')
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    raise RuntimeError('Stop PIE before correcting editor lights')
colors = {
    'KL_HallLight0': (1.0, .88, .70), 'KL_HallLight1': (1.0, .86, .68),
    'KL_HallLight2': (1.0, .86, .68), 'KL_HallLight3': (1.0, .84, .66),
    'KL_CorrLight': (.95, .92, .86), 'KL_RoomLight': (1.0, .90, .74),
    'KL_WindowShaft0': (.62, .74, 1.0), 'KL_WindowShaft1': (.62, .74, 1.0),
    'KL_Moon': (.55, .66, .95),
}
report = []
for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    label = actor.get_actor_label()
    if label not in colors:
        continue
    component = actor.get_component_by_class(unreal.LightComponent)
    if component is None:
        raise RuntimeError('Missing light component: ' + label)
    before = component.get_editor_property('light_color')
    channels = tuple(round(c * 255) for c in colors[label])
    component.set_editor_property('light_color', unreal.Color(r=channels[0], g=channels[1], b=channels[2], a=255))
    after = component.get_editor_property('light_color')
    actual = [after.r, after.g, after.b]
    if actual != list(channels):
        raise RuntimeError('Light channel mismatch: ' + label)
    report.append({'actor': label, 'before': [before.r, before.g, before.b], 'after': actual})
if len(report) != len(colors):
    raise RuntimeError('Not all expected production lights were found')
if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level():
    raise RuntimeError('Could not save corrected production lights')
target = Path(unreal.Paths.project_dir()) / 'docs/agent/EVIDENCE/G1_light_color_repair.json'
target.write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report))
