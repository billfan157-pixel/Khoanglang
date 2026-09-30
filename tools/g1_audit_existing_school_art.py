"""Read existing art levels and record placed architecture/furniture; never save."""
import gc
import json
from pathlib import Path
import unreal

def main():
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
        raise RuntimeError('Stop PIE before inspecting existing levels')
    gc.collect()
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    reports = []
    for map_name in ('Lvl_KL_School3_Art', 'Lvl_KL_School3_ArtTest'):
        if not level.load_level('/Game/KhoangLang/Maps/' + map_name):
            raise RuntimeError('Could not inspect ' + map_name)
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        report = {'map': map_name, 'actors': [], 'game_mode': str(world.get_world_settings().get_editor_property('default_game_mode'))}
        for actor in actor_subsystem.get_all_level_actors():
            location = actor.get_actor_location()
            mesh = actor.get_component_by_class(unreal.StaticMeshComponent)
            asset = mesh.get_editor_property('static_mesh') if mesh else None
            report['actors'].append({'label': actor.get_actor_label(),
                'class': actor.get_class().get_path_name(),
                'location': [location.x, location.y, location.z],
                'rotation': str(actor.get_actor_rotation()),
                'mesh': asset.get_path_name() if asset else None,
                'bounds': str(actor.get_actor_bounds(False)),
                'components': [c.get_class().get_path_name() for c in actor.get_components_by_class(unreal.ActorComponent)]})
        reports.append(report)
        # Release reflected objects before switching worlds.
        actor = mesh = asset = world = None
        gc.collect()
    target = Path(unreal.Paths.project_dir()) / 'docs/agent/EVIDENCE/G1_existing_school_art_audit.json'
    target.write_text(json.dumps(reports, indent=2), encoding='utf-8')
    print(json.dumps([{'map': r['map'], 'actors': len(r['actors']),
        'school_furniture': sum('/SchoolFurniture/' in (a['mesh'] or '') for a in r['actors']),
        'art_meshes': sum('/Meshes/' in (a['mesh'] or '') for a in r['actors'])} for r in reports]))

main()
