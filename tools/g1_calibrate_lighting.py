"""Apply an isolated dynamic-light candidate; preserve all source assets.

GI is disabled for this integrated-GPU project. Low-intensity unshadowed fill
approximates bounce from authored practical lamps; it is not a GI claim.
Execution requires stopped PIE and the isolated G1 map. Capture/inspect next.
"""
import hashlib
import json
from pathlib import Path
import sys
import unreal

ROOT = Path(unreal.Paths.project_dir())
sys.path.insert(0, str(ROOT / 'tools'))
import g1_refine_school_art as art

FILL = {
    'G1_Bounce_Entry': ((-560, 0, 105), 380., 1050., (.84, .89, 1.)),
    'G1_Bounce_Hall': ((620, 0, 105), 460., 1250., (1., .92, .81)),
    'G1_Bounce_Room': ((1070, 580, 105), 520., 1250., (1., .93, .83)),
}


def main():
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = editor.get_editor_world()
    if editor.get_game_world() or world.get_path_name().split('.')[0] != art.MAP:
        raise RuntimeError('Stopped PIE and canonical G1 map required')
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    labels = {a.get_actor_label(): a for a in actors.get_all_level_actors()}
    report = {'visual_accepted': False, 'map': art.MAP,
              'source_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'lights': [], 'exposure_ev': art.EXPOSURE_BIAS_EV,
              'method': 'Movable practical lights plus restrained bounce proxies; no baked lighting'}
    if set(art.LIGHTS) - set(labels):
        raise RuntimeError('Required authored lights absent')
    world.modify()
    for label in list(art.LIGHTS) + ['ART_Moon']:
        a = labels[label]
        c = a.get_component_by_class(unreal.LightComponent)
        a.modify()
        c.modify()
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
        if c.get_editor_property('mobility') != unreal.ComponentMobility.MOVABLE:
            raise RuntimeError('Mobility readback failed: ' + label)
        report['lights'].append({'label': label, 'mobility': 'Movable'})
    for label, (position, lumens, radius, rgb) in FILL.items():
        a = labels.get(label)
        if a is None:
            a = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(*position))
            a.set_actor_label(label)
        a.modify()
        a.set_actor_location(unreal.Vector(*position), False, True)
        c = a.get_component_by_class(unreal.PointLightComponent)
        c.modify()
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
        c.set_editor_property('intensity_units', unreal.LightUnits.LUMENS)
        c.set_editor_property('intensity', lumens)
        c.set_editor_property('attenuation_radius', radius)
        c.set_editor_property('use_inverse_squared_falloff', True)
        c.set_editor_property('cast_shadows', False)
        c.set_editor_property('source_radius', 25.)
        c.set_editor_property('light_color', unreal.Color(
            round(rgb[0]*255), round(rgb[1]*255), round(rgb[2]*255), 255))
        report['lights'].append({'label': label, 'position': position,
                                'lumens': lumens, 'radius_cm': radius, 'shadows': False})
    grade = labels.get('G1_ArtGrade')
    if grade is None:
        raise RuntimeError('Refined postprocess missing')
    grade.modify()
    settings = grade.get_editor_property('settings')
    settings.set_editor_property('override_auto_exposure_bias', True)
    settings.set_editor_property('auto_exposure_bias', art.EXPOSURE_BIAS_EV)
    grade.set_editor_property('settings', settings)
    ws = world.get_world_settings()
    ws.modify()
    ws.set_editor_property('force_no_precomputed_lighting', True)
    report['force_no_precomputed_lighting'] = ws.get_editor_property('force_no_precomputed_lighting')
    if not unreal.EditorLoadingAndSavingUtils.save_map(world, art.MAP):
        raise RuntimeError('Map save failed')
    target = ROOT / 'Content/KhoangLang/Production/G1Canon/Lvl_KL_SchoolSlice.umap'
    report['map_sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
    (ROOT / 'docs/agent/EVIDENCE/G1_dynamic_lighting.json').write_text(
        json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
