"""Repair primary-map material slots and reduce excessive illumination."""
import json
from pathlib import Path
import unreal

def main():
    root = Path(unreal.Paths.project_dir())
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if '/Production/Maps/Lvl_KL_School3_Primary' not in world.get_path_name():
        raise RuntimeError('Primary editor map required')
    world.modify()
    intents = json.loads((root / 'docs/agent/EVIDENCE/G1_school_placement_intents.json').read_text())
    light_settings = {s['label']:s for s in intents['lights']}
    report = dict(map=world.get_path_name(), actors=[], lights=[])
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        label = a.get_actor_label()
        # Kit thickness must extend outside the room. The source south/east
        # orientations enclosed the chalkboard and window fittings in plaster.
        yaw = (0 if label=='ART_Wall_RoomS' else -90 if label.startswith('ART_Wall_RoomE_')
            else 180 if label=='ART_Wall_HallS' else 0 if label=='ART_NoticeBoard' else None)
        if yaw is not None:
            a.modify()
            a.set_actor_rotation(unreal.Rotator(pitch=0,yaw=yaw,roll=0),False)
        if isinstance(a,unreal.PostProcessVolume):
            a.modify()
            settings=a.get_editor_property('settings')
            settings.set_editor_property('bOverride_AutoExposureBias',True)
            settings.set_editor_property('auto_exposure_bias',-2.0)
            a.set_editor_property('settings',settings)
        if label in light_settings:
            s = light_settings[label]
            c = a.get_component_by_class(unreal.LightComponent)
            scale = .12 if s['kind'] == 'Point' else .08 if s['kind'] == 'Spot' else 1
            a.modify(); c.modify()
            c.set_editor_property('intensity', s['intensity']*scale)
            report['lights'].append(dict(label=label,intensity=s['intensity']*scale))
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            materials = [c.get_material(i).get_path_name() if c.get_material(i) else None for i in range(c.get_num_materials())]
            report['actors'].append(dict(label=label,materials=materials,mesh=c.get_editor_property('static_mesh').get_path_name() if c.get_editor_property('static_mesh') else None))
    if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level():
        raise RuntimeError('Primary visual save failed')
    (root / 'docs/agent/EVIDENCE/G1_primary_visual_repair.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(map=world.get_path_name(),lights=len(report['lights']))))

main()
