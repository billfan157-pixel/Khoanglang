import os
import unreal
from editor_toolset.toolsets import blueprint as BP
from editor_toolset.toolsets import actor as ACT

R = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p39'
os.makedirs(R, exist_ok=True)


def p(m):
    unreal.log('P39: ' + str(m))
    with open(os.path.join(R, 'r.txt'), 'a', encoding='utf-8') as f:
        f.write(str(m) + '\n')


def pins(node):
    ni = BP.BlueprintTools.get_node_infos([node])[0]
    return ('IN [%s] OUT [%s]' % (
        ', '.join('%s:%s' % (x.name, x.type_id) for x in ni.input_pins),
        ', '.join('%s:%s' % (x.name, x.type_id) for x in ni.output_pins)))


eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
eas.make_directory('/Game/KhoangLang/Data')
bp = BP.BlueprintTools.create('/Game/KhoangLang/Data', 'TMP39', unreal.Actor.static_class())
BP.BlueprintTools.compile_blueprint(bp)
g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(g)

p('=== sound spawn / play node signatures ===')
for nid in ('Audio|PlaySound2D', '/Script/Engine.GameplayStatics:PlaySoundAtLocation',
            '/Script/Engine.GameplayStatics:SpawnSound2D',
            '/Script/Engine.GameplayStatics:SpawnSoundAtLocation',
            '/Script/Engine.AudioComponent:SetPitchModulation',
            '/Script/Engine.AudioComponent:SetSubmixSend',
            '/Script/Engine.AudioComponent:AdjustVolume'):
    n = ed.create_node_from_name(nid, unreal.Vector2D(0, 0), [], None) \
        if '|' in nid else ed.add_call_function_node(nid)
    if n is None:
        p('  MISS %s' % nid)
        continue
    p('  OK   %-56s %s' % (nid, pins(n)))
    ed.remove_nodes([n])

p('=== blueprint subclasses of audio-ish components ===')
for name, native in (('TMP39_Amb', 'AudioComponent'),
                     ('TMP39_Mask', 'AudioComponent'),
                     ('TMP39_Scene', 'SceneComponent')):
    cls = unreal.load_class(None, '/Script/Engine.' + native)
    b = BP.BlueprintTools.create('/Game/KhoangLang/Data', name, cls)
    p('  %-12s parent=%-18s -> %s' % (name, native, b.get_name() if b else 'None'))
    if b:
        BP.BlueprintTools.compile_blueprint(b)
        p('     status %s' % b.get_editor_property('status'))

p('=== add two distinct BP audio components to one actor + GetComponentByClass ===')
act = BP.BlueprintTools.create('/Game/KhoangLang/Data', 'TMP39_Actor',
                               unreal.Actor.static_class())
c1 = ACT.ActorTools.add_component(act, unreal.load_class(
    None, '/Game/KhoangLang/Data/TMP39_Amb.TMP39_Amb_C'), 'BedAmb')
c2 = ACT.ActorTools.add_component(act, unreal.load_class(
    None, '/Game/KhoangLang/Data/TMP39_Mask.TMP39_Mask_C'), 'BedMask')
p('  c1=%s c2=%s' % (c1, c2))
BP.BlueprintTools.compile_blueprint(act)
g2 = unreal.BlueprintEditorLibrary.find_event_graph(act)
ed2 = unreal.BlueprintGraphEditor.get_graph_editor(g2)
n = ed2.create_node_from_name('Actor|GetComponentbyClass', unreal.Vector2D(0, 0), [], None)
if n is not None:
    p('  %s' % pins(n))
    for v in ('/Script/Engine.AudioComponent', '/Game/KhoangLang/Data/TMP39_Amb.TMP39_Amb_C'):
        BP.BlueprintTools.set_pin_value(BP.BlueprintTools.get_node_infos([n])[0].input_pins[1].pin_id, v)
        p('    ComponentClass %-56s -> %r' % (
            v, BP.BlueprintTools.get_pin_value(BP.BlueprintTools.get_node_infos([n])[0].input_pins[1].pin_id)))
    ed2.remove_nodes([n])

p('=== template character components ===')
ch = unreal.load_asset('/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter')
for c in ACT.ActorTools.get_components(BP.BlueprintTools.get_default_object(ch)):
    p('  %-46s [%s]' % (c.get_name(), c.get_class().get_name()))

p('=== cleanup ===')
for n in ('TMP39', 'TMP39_Amb', 'TMP39_Mask', 'TMP39_Scene', 'TMP39_Actor'):
    unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/' + n)
p('DONE')
