"""Stage the isolated school scenario on a new copy, preserving original art."""
import json
from pathlib import Path
import sys
import unreal

ROOT=Path(unreal.Paths.project_dir())
sys.path.insert(0,str(ROOT/'Content/Python/KhoangLang'))
import kl_core as K

BASE='/Game/KhoangLang/Production/G1Canon'
MAP=BASE+'/Lvl_KL_SchoolSlice'
SOURCE='/Game/KhoangLang/Production/Maps/Lvl_KL_School3_Primary'

def main():
    editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if editor.get_game_world():
        raise RuntimeError('Stop PIE before staging')
    for path in (BASE+'/BP_KL_SchoolLoop',BASE+'/BP_KL_SchoolGameMode'):
        if not unreal.EditorAssetLibrary.does_asset_exist(path):
            raise RuntimeError('Missing dependency: '+path)
    level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    unreal.EditorAssetLibrary.make_directory(BASE)
    if unreal.EditorAssetLibrary.does_asset_exist(MAP):
        if not level.load_level(MAP):
            raise RuntimeError('School slice load failed')
    elif not level.new_level_from_template(MAP,SOURCE):
        raise RuntimeError('School template copy failed')
    world=editor.get_editor_world()
    if MAP not in world.get_path_name():
        raise RuntimeError('Refusing to stage outside new slice')
    world.modify()
    report={'map':MAP,'source':SOURCE,'interaction_actors':[],
            'scope':'Isolated G1 later-evidence fixture; character art not accepted'}
    # Remove prior prototype behavior only from the copied map. No source
    # Blueprint or source level is removed or overwritten.
    for a in list(actors.get_all_level_actors()):
        if 'BP_KL_Prop_' in a.get_class().get_name():
            if not actors.destroy_actor(a):
                raise RuntimeError('Copied prototype actor replacement failed')
    labels={a.get_actor_label():a for a in actors.get_all_level_actors()}

    def mesh_copy(name,source_folder='/Game/KhoangLang/Meshes/Props'):
        source=source_folder+'/'+name
        target=BASE+'/Meshes/'+name
        unreal.EditorAssetLibrary.make_directory(BASE+'/Meshes')
        mesh=(unreal.load_asset(target) if unreal.EditorAssetLibrary.does_asset_exist(target)
              else unreal.EditorAssetLibrary.duplicate_asset(source,target))
        if mesh is None:
            raise RuntimeError('Mesh copy failed: '+source)
        mesh.modify()
        body=mesh.get_editor_property('body_setup')
        body.modify()
        body.set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        body.set_editor_property('double_sided_geometry',True)
        if not unreal.EditorAssetLibrary.save_loaded_asset(mesh,False):
            raise RuntimeError('Mesh collision save failed')
        return mesh

    book_mesh=mesh_copy('SM_KL_Prop_AttBook')
    figure_mesh=mesh_copy('SM_KL_Prop_Figure')
    tape_mesh=mesh_copy('SM_KL_Prop_TapeDeck')
    # The teacher desk's single convex hull covers the air above its worktop
    # up to the raised rear lid. Use triangles in an owned copy so a ray can
    # genuinely reach the book on the visible worktop.
    desk_mesh=mesh_copy('SM_KL_Desk_Teacher','/Game/KhoangLang/Production/Meshes/School')
    desk=labels.get('ART_Teacher_Desk')
    if desk is None:
        raise RuntimeError('Teacher desk missing from school template')
    desk.modify()
    desk.get_component_by_class(unreal.StaticMeshComponent).set_static_mesh(desk_mesh)

    def put(label,tag,mesh,position,yaw=0,scale=(1,1,1),collision=True,hidden=False):
        actor=labels.get(label)
        if actor is None:
            actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*position))
            actor.set_actor_label(label)
            labels[label]=actor
        actor.modify()
        actor.set_actor_location(unreal.Vector(*position),False,False)
        actor.set_actor_rotation(unreal.Rotator(pitch=0,yaw=yaw,roll=0),False)
        actor.set_actor_scale3d(unreal.Vector(*scale))
        actor.set_editor_property('tags',[unreal.Name(tag)])
        actor.set_actor_hidden_in_game(hidden)
        component=actor.get_component_by_class(unreal.StaticMeshComponent)
        component.modify()
        component.set_static_mesh(mesh)
        component.set_mobility(unreal.ComponentMobility.MOVABLE)
        component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS
                                        if collision else unreal.CollisionEnabled.NO_COLLISION)
        if collision:
            component.set_collision_response_to_channel(unreal.CollisionChannel.ECC_VISIBILITY,
                                                         unreal.CollisionResponseType.ECR_BLOCK)
        report['interaction_actors'].append({'label':label,'tag':tag,'position':position,
                                            'mesh':mesh.get_path_name()})
        return actor

    # Teacher desktop top is at Z=90. Raise book base above that plane so
    # the visible cover has a distinct and genuine collision surface.
    put('G1_VanNotebook','KL_Notebook',book_mesh,(1050,790,91),yaw=6)
    # A separate ledger is confined to this scenario; later campaign evidence
    # is not granted by entering the Hồi 1 school scene.
    put('G1_RiceLedger','KL_Ledger',book_mesh,(570,570,126),yaw=90)
    put('G1_ListeningDeck','KL_Listen',tape_mesh,(1930,0,122))
    put('G1_Lam','KL_Lam',figure_mesh,(560,-120,0),yaw=0,scale=(1,1,1.1))
    put('G1_Van','KL_Teacher',figure_mesh,(1180,845,14),yaw=-90)
    put('G1_BackRowChild','KL_Child',figure_mesh,(680,285,0),yaw=90,
        scale=(.6,.6,.66),collision=False,hidden=True)
    # This door has no opening behind it and appears only in false silence.
    door=unreal.load_asset('/Game/KhoangLang/Meshes/Arch/SM_KL_Door_Leaf')
    put('G1_ImpossibleDoor','KL_FalseGeometry',door,(1440,202,0),yaw=0,
        collision=False,hidden=True)
    exit_mesh=mesh_copy('SM_KL_Door_Leaf','/Game/KhoangLang/Meshes/Arch')
    put('G1_Exit','KL_Exit',exit_mesh,(-975,-70,0),yaw=90)
    loop=labels.get('G1_SchoolLoop')
    if loop is None:
        loop=actors.spawn_actor_from_class(K.bp_class(BASE+'/BP_KL_SchoolLoop'),unreal.Vector())
        loop.set_actor_label('G1_SchoolLoop')
    loop.set_editor_property('bG1Fixture',True)
    native_gm=BASE+'/BP_KL_SchoolNativeGameMode'
    gm=native_gm if unreal.EditorAssetLibrary.does_asset_exist(native_gm) else BASE+'/BP_KL_SchoolGameMode'
    world.get_world_settings().set_editor_property('default_game_mode',K.bp_class(gm))
    report['game_mode']=gm
    # This is a functional staging pass; keep inherited lighting for comparison.
    if not unreal.EditorLoadingAndSavingUtils.save_map(world,MAP):
        raise RuntimeError('Canonical map save failed')
    (ROOT/'docs/agent/EVIDENCE/G1_canonical_staging.json').write_text(
        json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'map':MAP,'interactions':len(report['interaction_actors'])}))

if __name__=='__main__':
    main()
