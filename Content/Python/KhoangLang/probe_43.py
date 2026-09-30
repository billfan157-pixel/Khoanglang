import os
import unreal
from editor_toolset.toolsets import blueprint as BP

R = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p43'
os.makedirs(R, exist_ok=True)


def p(m):
    unreal.log('P43: ' + str(m))
    with open(os.path.join(R, 'r.txt'), 'a', encoding='utf-8') as f:
        f.write(str(m) + '\n')


eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
eas.make_directory('/Game/KhoangLang/Data')
if unreal.load_asset('/Game/KhoangLang/Data/TMP43'):
    unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP43')
bp = BP.BlueprintTools.create('/Game/KhoangLang/Data', 'TMP43',
                              unreal.ActorComponent.static_class())
BP.BlueprintTools.compile_blueprint(bp)
g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(g)

a = ed.create_node_from_name('Actor|GetComponentbyClass', unreal.Vector2D(0, 0), [], None)
b = ed.create_node_from_name('Actor|GetComponentbyClass', unreal.Vector2D(0, 0), [], None)
p('node a = %s' % a.get_name())
p('node b = %s' % b.get_name())
p('same object? %s' % (a == b))
p('same name?   %s' % (a.get_name() == b.get_name()))
pinfo = BP.BlueprintTools.get_node_infos([a])[0]
p('PinInfo attrs: %s' % [x for x in dir(pinfo.input_pins[0]) if not x.startswith('_')])
for x in pinfo.input_pins:
    p('  in  %-18s type=%-40s extra=%s' % (x.name, x.type_id,
                                           {k: getattr(x, k) for k in
                                            ('linked_to', 'default_value', 'default_object',
                                             'default_text_value', 'default_name_value')
                                            if hasattr(x, k)}))
for x in pinfo.output_pins:
    p('  out %-18s type=%-40s extra=%s' % (x.name, x.type_id,
                                           {k: getattr(x, k) for k in
                                            ('linked_to', 'default_value')
                                            if hasattr(x, k)}))
# set different classes and see if the pins stay independent
BP.BlueprintTools.set_pin_value(pinfo.input_pins[1].pin_id, '/Script/Engine.StaticMeshComponent')
BP.BlueprintTools.set_pin_value(
    BP.BlueprintTools.get_node_infos([b])[0].input_pins[1].pin_id,
    '/Script/Engine.PointLightComponent')
p('a out: %s' % [(x.name, x.type_id)
                  for x in BP.BlueprintTools.get_node_infos([a])[0].output_pins])
p('b out: %s' % [(x.name, x.type_id)
                  for x in BP.BlueprintTools.get_node_infos([b])[0].output_pins])
unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP43')
p('DONE')
