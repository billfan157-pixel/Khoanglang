"""Make the copied procedural surfaces render and collide from both sides."""
import unreal
from editor_toolset.toolsets.material import MaterialTools
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(): raise RuntimeError('Stop PIE first')
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
if '/Production/Maps/Lvl_KL_School3_Primary' not in world.get_path_name(): raise RuntimeError('Primary map required')
mat=unreal.load_asset('/Game/KhoangLang/Production/Materials/M_KL_ART_Surface')
mat.set_editor_property('two_sided',True)
MaterialTools.recompile(mat)
if not unreal.EditorAssetLibrary.save_loaded_asset(mat,False): raise RuntimeError('Surface save failed')
count=0
for path in unreal.EditorAssetLibrary.list_assets('/Game/KhoangLang/Production/Meshes/School',True,False):
    mesh=unreal.load_asset(path)
    if not isinstance(mesh,unreal.StaticMesh): continue
    body=mesh.get_editor_property('body_setup')
    if body:
        body.set_editor_property('double_sided_geometry',True)
        if not unreal.EditorAssetLibrary.save_loaded_asset(mesh,False): raise RuntimeError('Collision sides save failed')
        count+=1
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        if c.get_collision_enabled()!=unreal.CollisionEnabled.NO_COLLISION:
            c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
world.modify()
if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level(): raise RuntimeError('Surface map save failed')
print('PRIMARY_SURFACE_SIDES_REPAIRED meshes=%d' % count)
