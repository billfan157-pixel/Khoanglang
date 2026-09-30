"""Discovery probe 15: validate the exact DSL shapes Milestone 1 depends on."""

import os
import sys
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
sys.path.insert(0, HERE)

OUT_DIR = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p15'
os.makedirs(OUT_DIR, exist_ok=True)
REPORT = []

TARGET_C = '/Game/KhoangLang/Data/TMP15_Target.TMP15_Target_C'
IA_EVENT_CLASS = None



def p(msg):
    line = str(msg)
    REPORT.append(line)
    unreal.log('KL15: ' + line)
    with open(os.path.join(OUT_DIR, 'report.txt'), 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


def attempt(label, fn):
    try:
        fn()
        p('  PASS %s' % label)
        return True
    except Exception as exc:
        p('  FAIL %s -> %s' % (label, str(exc)[:400]))
        return False


def wr(BPT, graph, code, compile_bp=None):
    BPT.write_graph_dsl(graph, code)
    if compile_bp is not None:
        BPT.compile_blueprint(compile_bp)


def mk(name, folder, cls, factory):
    """Idempotent asset creation: reuse an existing asset of the right class."""
    at = unreal.AssetToolsHelpers.get_asset_tools()
    path = '%s/%s' % (folder, name)
    a = unreal.load_asset(path)
    if a is not None:
        p('  reuse %s' % path)
        return a
    for attempt_no in range(3):
        unreal.SystemLibrary.collect_garbage()
        a = at.create_asset(name, folder, cls, factory())
        if a is not None:
            return a
        p('  create_asset %s attempt %d -> None' % (name, attempt_no + 1))
    raise RuntimeError('create_asset failed for %s' % path)



def main():
    from editor_toolset.toolsets import blueprint as BP
    from editor_toolset.toolsets import actor as ACT
    BPT = BP.BlueprintTools
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    at = unreal.AssetToolsHelpers.get_asset_tools()
    eas.make_directory('/Game/KhoangLang/Input')
    eas.make_directory('/Game/KhoangLang/Data')

    global IA_EVENT_CLASS
    IA_EVENT_CLASS = unreal.K2Node_EnhancedInputActionEvent.static_class()
    p('ia event node class: %s' % IA_EVENT_CLASS.get_name())
    ia = mk('TMP15_IA_Test', '/Game/KhoangLang/Input', unreal.InputAction,
            unreal.InputAction_Factory)
    ia.set_editor_property('value_type', unreal.InputActionValueType.BOOLEAN)
    eas.save_asset('/Game/KhoangLang/Input/TMP15_IA_Test', only_if_is_dirty=False)
    p('input action: %s' % ia)

    tpl = unreal.load_asset('/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter')
    p('template character loaded: %s' % (tpl is not None))

    child = BPT.create('/Game/KhoangLang/Data', 'TMP15_Char',
                       unreal.load_class(
                           None,
                           '/Game/FirstPerson/Blueprints/'
                           'BP_FirstPersonCharacter.BP_FirstPersonCharacter_C'))
    g = BPT.list_graphs(child)[0]

    p('')
    p('=== template character: existing enhanced input events ===')
    tg = BPT.list_graphs(tpl)[0]
    for n in BPT.find_nodes(tg, node_class=IA_EVENT_CLASS) or []:
        try:
            p('  %s title=%r action=%s'
              % (n.get_name(), n.get_node_title(0), n.get_editor_property('input_action')))
        except Exception as exc:
            p('  %s inspect failed %r' % (n.get_name(), exc))

    p('')
    p('=== A. enhanced input action event through the DSL ===')
    code_a = (
        '(event EnhancedInputActionIA_Test (ActionValue))\n'
        '  (Development|PrintString :InString "ia event")'
    )
    if attempt('dsl enhanced input event', lambda: wr(BPT, g, code_a, child)):
        for n in BPT.find_nodes(g, node_class=IA_EVENT_CLASS) or []:
            p('    created: %r action=%s'
              % (n.get_node_title(0), n.get_editor_property('input_action')))

    def b_bind():
        nodes = BPT.find_nodes(g, node_class=IA_EVENT_CLASS) or []
        p('    found %d input action event nodes' % len(nodes))
        for n in nodes:
            n.set_editor_property('input_action', ia)
        BPT.compile_blueprint(child)
        for n in BPT.find_nodes(g, node_class=IA_EVENT_CLASS) or []:
            p('    bound: %r action=%s'
              % (n.get_node_title(0), n.get_editor_property('input_action')))
    attempt('bind input_action', b_bind)

    p('')
    p('=== B. add_event() path ===')
    attempt('add_event', lambda: p('    add_event -> %s'
                                   % BPT.add_event(child, 'EnhancedInputActionIA_Test')))

    p('')
    p('=== C. control flow ===')
    BPT.add_variable(child, 'bFlag', 'bool')
    for n in ('S0', 'S1', 'S2', 'S3', 'S4', 'S5'):
        BPT.add_function_graph(child, n)

    c0 = (
        '(fn S0 ()\n'
        '  (if (Variables|Default|GetbFlag) (Development|PrintString :InString "a"))\n'
        '  (if (not (Variables|Default|GetbFlag)) (Development|PrintString :InString "b"))\n'
        '  (return))'
    )
    attempt('two sequential ifs', lambda: wr(BPT, BPT.get_graph(child, 'S0'), c0, child))

    c1 = (
        '(fn S1 ()\n'
        '  (if (Variables|Default|GetbFlag) (Development|PrintString :InString "a")\n'
        '    (else (Development|PrintString :InString "b"))))'
    )
    attempt('else branch', lambda: wr(BPT, BPT.get_graph(child, 'S1'), c1, child))

    c2 = (
        '(fn S2 ()\n'
        '  (if (Variables|Default|GetbFlag)\n'
        '    (Utilities|FlowControl|Sequence\n'
        '      (:0\n'
        '        (Development|PrintString :InString "x")\n'
        '        (Development|PrintString :InString "y")))))'
    )
    attempt('Sequence :0 continuation',
            lambda: wr(BPT, BPT.get_graph(child, 'S2'), c2, child))

    c3 = (
        '(fn S3 ()\n'
        '  (Utilities|IsValid (Actor|GetActorOfClass "%s")\n'
        '    (:"Is Valid" (Development|PrintString :InString "yes"))\n'
        '    (:"Is Not Valid" (Development|PrintString :InString "no"))))' % TARGET_C
    )
    attempt('IsValid multi-exec', lambda: wr(BPT, BPT.get_graph(child, 'S3'), c3, child))

    c4 = (
        '(fn S4 ()\n'
        '  (Utilities|FlowControl|Delay 1.0\n'
        '    (Development|PrintString :InString "later")))'
    )
    attempt('Delay node', lambda: wr(BPT, BPT.get_graph(child, 'S4'), c4, child))

    c5 = (
        '(fn S4 ()\n'
        '  (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "S0" '
        ':Time 0.2 :bLooping false)\n'
        '  (return))'
    )
    attempt('SetTimerbyFunctionName',
            lambda: wr(BPT, BPT.get_graph(child, 'S4'), c5, child))
    attempt('compile after control flow', lambda: BPT.compile_blueprint(child))

    p('')
    p('=== D. cross-BP cast + call ===')
    if unreal.load_asset('/Game/KhoangLang/Data/TMP15_Target'):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP15_Target')
    tgt = BPT.create('/Game/KhoangLang/Data', 'TMP15_Target', unreal.Actor.static_class())
    fg = BPT.add_function_graph(tgt, 'Ping')
    BPT.add_function_param(fg, 'Who', unreal.Actor.static_class(), True)
    BPT.add_function_param(fg, 'Loud', 'bool', True)
    BPT.add_function_param(fg, 'Result', 'string', False)
    wr(BPT, fg, '(fn Ping (Who Loud)\n  (return "pong"))', tgt)
    BPT.compile_blueprint(tgt)
    eas.save_asset('/Game/KhoangLang/Data/TMP15_Target', only_if_is_dirty=False)
    BPT.add_variable(child, 'Tgt', 'bool')

    d0 = (
        '(event EventBeginPlay\n'
        '  (bind found (Actor|GetActorOfClass "%s"))\n'
        '  (bind tj (Utilities|Casting|CastToTMP15_Target :Object found)\n'
        '    (:then\n'
        '      (Variables|Default|SetTgt true)\n'
        '      (bind r (TMP15_Target_C|Ping self true))\n'
        '      (Development|PrintString :InString r))\n'
        '    (:CastFailed\n'
        '      (Variables|Default|SetTgt false)))\n'
        '  (Development|PrintString :InString "done"))' % TARGET_C
    )
    attempt('cross-bp cast+call', lambda: wr(BPT, g, d0, child))

    p('')
    p('=== E. array node pins ===')
    arr = BPT.get_graph(child, 'S3')
    for nid in ('Utilities|Array|Add', 'Utilities|Array|Get(aref)', 'Utilities|Array|Length',
                'Utilities|Array|IsEmpty', 'Utilities|Array|ContainsItem'):
        try:
            ni = BPT.get_node_type_pins(arr, nid)
            p('  %s\n     IN [%s]\n     OUT [%s]' % (
                nid,
                ', '.join('%s:%s' % (x.name, x.type_id) for x in ni.input_pins),
                ', '.join('%s:%s' % (x.name, x.type_id) for x in ni.output_pins)))
        except Exception as exc:
            p('  %s ERR %r' % (nid, exc))

    p('')
    p('=== F. for-each over an object array ===')
    BPT.add_object_variable(child, 'Found', unreal.Actor)
    f3 = ('(fn S5 ()\n'
          '  (for e (Variables|Default|GetFound)\n'
          '    (Development|PrintString :InString "x")))')
    attempt('for each', lambda: wr(BPT, BPT.get_graph(child, 'S5'), f3, child))

    p('')
    p('=== G. component-by-class + audio filter + sound ref ===')
    BPT.add_object_variable(child, 'Snd', unreal.SoundBase)
    f4 = (
        '(fn S4 ()\n'
        '  (bind ac (Actor|GetComponentbyClass self "/Script/Engine.AudioComponent"))\n'
        '  (Audio|Components|Audio|SetLowPassFilterEnabled ac true)\n'
        '  (Audio|Components|Audio|SetLowPassFilterFrequency ac 650.0)\n'
        '  (Audio|Components|Audio|SetSound ac (Variables|Default|GetSnd))\n'
        '  (Audio|Components|Audio|SetVolumeMultiplier ac 0.5)\n'
        '  (Audio|Components|Audio|Play ac)\n'
        '  (return))'
    )
    attempt('audio filter chain', lambda: wr(BPT, BPT.get_graph(child, 'S4'), f4, child))

    p('')
    p('=== H. spot light parented to the camera ===')
    cam = None
    for c in ACT.ActorTools.get_components(BPT.get_default_object(child)):
        p('   comp %-30s %s' % (c.get_name(), c.get_class().get_name()))
        if 'Camera' in c.get_class().get_name():
            cam = c
    if cam is not None:
        attempt('attach spot to camera', lambda: ACT.ActorTools.add_component(
            cam, unreal.SpotLightComponent.static_class(), 'KLFlash'))
        p('  components after:')
        for c in ACT.ActorTools.get_components(BPT.get_default_object(child)):
            ap = c.get_attach_parent()
            p('   comp %-30s %-32s parent=%s' % (c.get_name(), c.get_class().get_name(),
                                                 ap.get_name() if ap else '-'))
    else:
        p('  NO CAMERA COMPONENT FOUND on the template character')

    p('')
    p('=== I. HUD draw ===')
    if unreal.load_asset('/Game/KhoangLang/Data/TMP15_HUD'):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP15_HUD')
    hud = BPT.create('/Game/KhoangLang/Data', 'TMP15_HUD', unreal.HUD.static_class())
    BPT.add_variable(hud, 'Line', 'string')
    hg = BPT.list_graphs(hud)[0]
    h0 = (
        '(event DrawHUD\n'
        '  (HUD|DrawRect :RectColor (Math|Color|MakeColor :R 0.0 :G 0.0 :B 0.0 :A 0.5) '
        ':ScreenX 20.0 :ScreenY 20.0 :ScreenW 400.0 :ScreenH 100.0)\n'
        '  (HUD|DrawText :Text (Variables|Default|GetLine) '
        ':TextColor (Math|Color|MakeColor :R 1.0 :G 0.9 :B 0.7 :A 1.0) '
        ':ScreenX 30.0 :ScreenY 30.0 :Font "/Engine/EngineFonts/Roboto" :Scale 1.0 '
        ':bScalePosition false))'
    )
    attempt('hud draw', lambda: wr(BPT, hg, h0, hud))
    attempt('hud compile', lambda: BPT.compile_blueprint(hud))

    p('')
    p('=== J. IMC with 4 actions + save + reload ===')
    if unreal.load_asset('/Game/KhoangLang/Input/TMP15_IMC'):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Input/TMP15_IMC')
    imc = mk('TMP15_IMC', '/Game/KhoangLang/Input', unreal.InputMappingContext,
             unreal.InputMappingContext_Factory)
    for keyname in ('E', 'Q', 'Tab', 'F'):
        k = unreal.Key()
        k.set_editor_property('key_name', keyname)
        imc.map_key(ia, k)
    eas.save_asset('/Game/KhoangLang/Input/TMP15_IMC', only_if_is_dirty=False)
    imc2 = unreal.load_asset('/Game/KhoangLang/Input/TMP15_IMC')
    p('  reloaded mappings: %s' % imc2.get_editor_property('default_key_mappings'))
    p('  IMC struct: %s' % imc2.get_editor_property('default_key_mappings').mappings)

    p('')
    p('=== cleanup ===')
    for n in ('TMP15_Char', 'TMP15_Target', 'TMP15_HUD'):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/' + n)
    unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Input/TMP15_IA_Test')
    unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Input/TMP15_IMC')
    p('PROBE15_DONE')


try:
    rep = os.path.join(OUT_DIR, 'report.txt')
    if os.path.exists(rep):
        os.remove(rep)
    main()
except Exception:
    p(traceback.format_exc())
    p('PROBE15_FAILED')


