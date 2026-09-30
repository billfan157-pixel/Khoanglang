"""Remove the solid panel incorrectly authored across the door-frame opening."""
import ast
from pathlib import Path
import sys
import unreal

root=Path(unreal.Paths.project_dir())
sys.path.insert(0,str(root/'Content/Python/KhoangLang'))
import kl_mesh as M
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(): raise RuntimeError('Stop PIE first')
if '/Production/Maps/Lvl_KL_School3_Primary' not in world.get_path_name(): raise RuntimeError('Primary map required')
tree=ast.parse((root/'Content/Python/KhoangLang/art_70_kit.py').read_text(encoding='utf-8'))
function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='door_frame')
class RemoveBacking(ast.NodeTransformer):
    def visit_Expr(self,node):
        if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute) and node.value.func.attr=='box':
            if node.value.args and isinstance(node.value.args[0],ast.Subscript):
                if ast.unparse(node.value.args[0])=='s[WOOD_DK]': return None
        return node
function=RemoveBacking().visit(function)
folder='/Game/KhoangLang/Production/Materials/'
namespace=dict(DOOR_W=140.,DOOR_H=220.,T=20.,WOOD=folder+'MI_ART_Wood',
    WOOD_DK=folder+'MI_ART_WoodDark',STONE=folder+'MI_ART_Stone')
exec(compile(ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[])), 'primary_frame', 'exec'),namespace)
mesh,tris=M.make_mesh('SM_KL_Door_Frame','/Game/KhoangLang/Production/Meshes/School',
    [namespace['WOOD'],namespace['WOOD_DK'],namespace['STONE']],namespace['door_frame']())
mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
if not unreal.EditorAssetLibrary.save_loaded_asset(mesh,False): raise RuntimeError('Frame mesh save failed')
def doorway_header(builder, slots):
    builder.box(slots[folder+'MI_ART_WallOchre'],-70,0,220,70,20,320,.45)
header,_=M.make_mesh('SM_KL_WallDoor_140','/Game/KhoangLang/Production/Meshes/School',
    [folder+'MI_ART_WallOchre',folder+'MI_ART_WallWainscot',folder+'MI_ART_WoodDark'],doorway_header)
header.get_editor_property('body_setup').set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
if not unreal.EditorAssetLibrary.save_loaded_asset(header,False): raise RuntimeError('Doorway header save failed')
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    c=a.get_component_by_class(unreal.StaticMeshComponent)
    if c and c.get_editor_property('static_mesh') in (mesh,header):
        c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
world.modify()
if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level(): raise RuntimeError('Primary frame save failed')
print('PRIMARY_FRAME_OPENING_REPAIRED triangles=%d' % tris)
