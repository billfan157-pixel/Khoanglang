"""Give copied static architecture exact collision instead of absent hulls."""
import json
from pathlib import Path
import unreal

def main():
    root=Path(unreal.Paths.project_dir())
    editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if editor.get_game_world(): raise RuntimeError('Stop PIE first')
    world=editor.get_editor_world()
    if '/Production/Maps/Lvl_KL_School3_Primary' not in world.get_path_name():
        raise RuntimeError('Primary map required')
    folder='/Game/KhoangLang/Production/Meshes/School'
    unreal.EditorAssetLibrary.make_directory(folder)
    copied={}
    report=dict(meshes=[],actors=[])
    world.modify()
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        for c in actor.get_components_by_class(unreal.StaticMeshComponent):
            mesh=c.get_editor_property('static_mesh')
            if not mesh or c.get_collision_enabled()==unreal.CollisionEnabled.NO_COLLISION: continue
            body=mesh.get_editor_property('body_setup')
            if not body or body.get_editor_property('collision_trace_flag')==unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE: continue
            original=mesh.get_path_name().split('.')[0]
            if not original.startswith('/Game/KhoangLang/Meshes/'): continue
            path=folder+'/'+mesh.get_name()
            if original not in copied:
                new=(unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path)
                    else unreal.EditorAssetLibrary.duplicate_asset(original,path))
                new.modify()
                setup=new.get_editor_property('body_setup')
                setup.modify()
                setup.set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
                if not unreal.EditorAssetLibrary.save_asset(path): raise RuntimeError('Collision mesh save failed: '+path)
                copied[original]=new
                report['meshes'].append(dict(source=original,copy=path))
            actor.modify(); c.modify()
            c.set_static_mesh(copied[original])
            report['actors'].append(actor.get_actor_label())
    if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level():
        raise RuntimeError('Primary collision map save failed')
    (root/'docs/agent/EVIDENCE/G1_primary_collision_repair.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(meshes=len(report['meshes']),actors=len(report['actors']))))

main()
