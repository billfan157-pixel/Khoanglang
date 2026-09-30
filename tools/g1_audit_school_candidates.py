"""Read-only inventory of all four candidates and the merged result."""
import gc
import json
from pathlib import Path
import unreal

def main():
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if editor.get_game_world():
        raise RuntimeError('Stop PIE before inspecting levels')
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    maps = ['/Game/KhoangLang/Maps/Lvl_KL_School3',
        '/Game/KhoangLang/Maps/Lvl_KL_School3_Art',
        '/Game/KhoangLang/Maps/Lvl_KL_School3_ArtTest',
        '/Game/KhoangLang/Production/Maps/Lvl_KL_School3_G1',
        '/Game/KhoangLang/Production/Maps/Lvl_KL_School3_Primary']
    reports = []
    for path in maps:
        gc.collect()
        if not unreal.EditorAssetLibrary.does_asset_exist(path):
            reports.append(dict(map=path, status='retired'))
            continue
        if not level.load_level(path):
            raise RuntimeError('Map load failed: ' + path)
        world = editor.get_editor_world()
        report = dict(map=path, game_mode=world.get_world_settings().get_editor_property('default_game_mode').get_path_name(), actors=[])
        for a in subsystem.get_all_level_actors():
            mesh = a.get_component_by_class(unreal.StaticMeshComponent)
            asset = mesh.get_editor_property('static_mesh') if mesh else None
            loc, rot = a.get_actor_location(), a.get_actor_rotation()
            row = dict(label=a.get_actor_label(), actor_class=a.get_class().get_path_name(),
                location=[loc.x,loc.y,loc.z], rotation=[rot.pitch,rot.yaw,rot.roll],
                mesh=asset.get_path_name() if asset else None)
            if mesh:
                row['collision'] = str(mesh.get_collision_enabled())
            light = a.get_component_by_class(unreal.LightComponent)
            if light:
                row['color'] = str(light.get_editor_property('light_color'))
                row['intensity'] = light.get_editor_property('intensity')
            report['actors'].append(row)
        reports.append(report)
        a = mesh = asset = world = light = None
        gc.collect()
    target = Path(unreal.Paths.project_dir()) / 'docs/agent/EVIDENCE/G1_school_candidates_audit.json'
    target.write_text(json.dumps(reports,indent=2),encoding='utf-8')
    print(json.dumps([dict(map=r['map'],actors=len(r['actors']),
        unique_meshes=len({a['mesh'] for a in r['actors'] if a['mesh']}),
        school_furniture=sum('/SchoolFurniture/' in (a['mesh'] or '') for a in r['actors'])) for r in reports]))

main()
