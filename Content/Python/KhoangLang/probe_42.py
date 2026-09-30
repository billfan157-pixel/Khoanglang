import os
import unreal
from editor_toolset.toolsets import blueprint as BP

R = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p42'
os.makedirs(R, exist_ok=True)


def p(m):
    unreal.log('P42: ' + str(m))
    with open(os.path.join(R, 'r.txt'), 'a', encoding='utf-8') as f:
        f.write(str(m) + '\n')


def info(n):
    ni = BP.BlueprintTools.get_node_infos([n])[0]
    ins = ', '.join('%s:%s' % (x.name, x.type_id) for x in ni.input_pins)
    outs = ', '.join('%s:%s' % (x.name, x.type_id) for x in ni.output_pins)
    return 'IN [%s] OUT [%s]' % (ins, outs)


eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
eas.make_directory('/Game/KhoangLang/Data')
for n in ('TMP42_Comp', 'TMP42_Act'):
    if unreal.load_asset('/Game/KhoangLang/Data/' + n):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/' + n)

bp = BP.BlueprintTools.create('/Game/KhoangLang/Data', 'TMP42_Comp',
                              unreal.ActorComponent.static_class())
BP.BlueprintTools.compile_blueprint(bp)
g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(g)

p('=== in a COMPONENT blueprint ===')
own = ed.add_call_function_node('/Script/Engine.ActorComponent:GetOwner')
p('  GetOwner: %s' % info(own))
gc = ed.create_node_from_name('Actor|GetComponentbyClass', unreal.Vector2D(0, 0), [], None)
p('  GetComp(before class): %s' % info(gc))
for v in ('/Script/Engine.StaticMeshComponent',
          'StaticMeshComponent',
          "Class'/Script/Engine.StaticMeshComponent'"):
    try:
        BP.BlueprintTools.set_pin_value(
            BP.BlueprintTools.get_node_infos([gc])[0].input_pins[1].pin_id, v)
        p('    class %-42s -> %r ; now %s' % (
            v, BP.BlueprintTools.get_pin_value(
                BP.BlueprintTools.get_node_infos([gc])[0].input_pins[1].pin_id),
            info(gc)))
    except Exception as exc:
        p('    class %-42s raised %r' % (v, exc))
hid = ed.create_node_from_name('Development|SetHiddeninGame', unreal.Vector2D(0, 0), [], None)
p('  SetHidden: %s' % info(hid))
try:
    BP.BlueprintTools.connect_pins(
        BP.BlueprintTools.get_node_infos([own])[0].output_pins[0].pin_id,
        BP.BlueprintTools.get_node_infos([gc])[0].input_pins[0].pin_id)
    p('  connected GetOwner->GetComp.self')
except Exception as exc:
    p('  connect own->comp raised %r' % (exc,))
try:
    BP.BlueprintTools.connect_pins(
        BP.BlueprintTools.get_node_infos([gc])[0].output_pins[0].pin_id,
        BP.BlueprintTools.get_node_infos([hid])[0].input_pins[1].pin_id)
    p('  connected GetComp->SetHidden.self')
except Exception as exc:
    p('  connect comp->hidden raised %r' % (exc,))
try:
    BP.BlueprintTools.compile_blueprint(bp, warnings_as_errors=False)
    p('  status=%s' % bp.get_editor_property('status'))
except Exception as exc:
    p('  compile raised %r' % (exc,))

p('')
p('=== same in an ACTOR blueprint (control) ===')
act = BP.BlueprintTools.create('/Game/KhoangLang/Data', 'TMP42_Act',
                               unreal.Actor.static_class())
BP.BlueprintTools.compile_blueprint(act)
g2 = unreal.BlueprintEditorLibrary.find_event_graph(act)
ed2 = unreal.BlueprintGraphEditor.get_graph_editor(g2)
gc2 = ed2.create_node_from_name('Actor|GetComponentbyClass', unreal.Vector2D(0, 0), [], None)
BP.BlueprintTools.set_pin_value(
    BP.BlueprintTools.get_node_infos([gc2])[0].input_pins[1].pin_id,
    '/Script/Engine.StaticMeshComponent')
p('  GetComp: %s' % info(gc2))
hid2 = ed2.create_node_from_name('Development|SetHiddeninGame', unreal.Vector2D(0, 0), [], None)
p('  SetHidden: %s' % info(hid2))
try:
    BP.BlueprintTools.connect_pins(
        BP.BlueprintTools.get_node_infos([gc2])[0].output_pins[0].pin_id,
        BP.BlueprintTools.get_node_infos([hid2])[0].input_pins[1].pin_id)
    p('  connected')
except Exception as exc:
    p('  connect raised %r' % (exc,))
try:
    BP.BlueprintTools.compile_blueprint(act, warnings_as_errors=False)
    p('  status=%s' % act.get_editor_property('status'))
except Exception as exc:
    p('  compile raised %r' % (exc,))

p('')
p('=== an object variable of component type, assigned to the CDO component ===')
cdo = BP.BlueprintTools.get_default_object(act)
comps = unreal.ActorTools.get_components(cdo)
from editor_toolset.toolsets import actor as ACT
sm = ACT.ActorTools.add_component(act, unreal.StaticMeshComponent.static_class(), 'KL_TestMesh')
BP.BlueprintTools.compile_blueprint(act)
BP.BlueprintTools.add_object_variable(act, 'MeshRef', unreal.StaticMeshComponent)
BP.BlueprintTools.compile_blueprint(act)
cdo = BP.BlueprintTools.get_default_object(act)
for c in ACT.ActorTools.get_components(cdo):
    if c.get_class().get_name() == 'StaticMeshComponent':
        try:
            cdo.set_editor_property('MeshRef', c)
            p('  set MeshRef -> %r' % (cdo.get_editor_property('MeshRef'),))
        except Exception as exc:
            p('  set MeshRef raised %r' % (exc,))
g3 = unreal.BlueprintEditorLibrary.find_event_graph(act)
ed3 = unreal.BlueprintGraphEditor.get_graph_editor(g3)
gv = ed3.add_get_member_variable_node(unreal.Name('MeshRef'))
p('  MeshRef getter: %s' % info(gv))
hid3 = ed3.create_node_from_name('Development|SetHiddeninGame', unreal.Vector2D(0, 0), [], None)
try:
    BP.BlueprintTools.connect_pins(
        BP.BlueprintTools.get_node_infos([gv])[0].output_pins[0].pin_id,
        BP.BlueprintTools.get_node_infos([hid3])[0].input_pins[1].pin_id)
    p('  connected MeshRef->SetHidden.self')
except Exception as exc:
    p('  connect raised %r' % (exc,))
try:
    BP.BlueprintTools.compile_blueprint(act, warnings_as_errors=False)
    p('  status=%s' % act.get_editor_property('status'))
except Exception as exc:
    p('  compile raised %r' % (exc,))

p('')
p('=== cleanup ===')
for n in ('TMP42_Comp', 'TMP42_Act'):
    unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/' + n)
p('DONE')
