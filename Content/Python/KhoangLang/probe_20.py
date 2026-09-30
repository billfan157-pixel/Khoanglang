"""Discovery probe 20: add_call_function_node takes a single function path."""

import os
import sys
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
sys.path.insert(0, HERE)

OUT_DIR = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p20'
os.makedirs(OUT_DIR, exist_ok=True)
REPORT = []


def p(msg):
    line = str(msg)
    REPORT.append(line)
    unreal.log('KL20: ' + line)
    with open(os.path.join(OUT_DIR, 'report.txt'), 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


def attempt(label, fn):
    try:
        r = fn()
        p('  PASS %s %s' % (label, '' if r is None else r))
        return True
    except Exception as exc:
        p('  FAIL %s -> %s' % (label, str(exc)[:400]))
        return False


def dump(tag, node):
    from editor_toolset.toolsets import blueprint as BP
    from editor_toolset.toolsets.blueprint import _get_node_type_id
    ni = BP.BlueprintTools.get_node_infos([node])[0]
    p('  %s -> %r' % (tag, _get_node_type_id(node)))
    for x in ni.input_pins:
        p('     IN  %-22s %s' % (x.name, x.type_id))
    for x in ni.output_pins:
        p('     OUT %-22s %s' % (x.name, x.type_id))
    return ni


def main():
    from editor_toolset.toolsets import blueprint as BP
    from editor_toolset.toolsets.blueprint import _get_node_type_id
    BPT = BP.BlueprintTools
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    at = unreal.AssetToolsHelpers.get_asset_tools()
    eas.make_directory('/Game/KhoangLang/Input')
    eas.make_directory('/Game/KhoangLang/Data')

    if unreal.load_asset('/Game/KhoangLang/Data/TMP20_Char'):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP20_Char')
    if unreal.load_asset('/Game/KhoangLang/Input/IA_KL_Test'):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Input/IA_KL_Test')
    ia = at.create_asset('IA_KL_Test', '/Game/KhoangLang/Input', unreal.InputAction,
                         unreal.InputAction_Factory())
    ia.set_editor_property('value_type', unreal.InputActionValueType.BOOLEAN)
    eas.save_asset('/Game/KhoangLang/Input/IA_KL_Test', only_if_is_dirty=False)

    child = BPT.create('/Game/KhoangLang/Data', 'TMP20_Char', unreal.load_class(
        None, '/Game/FirstPerson/Blueprints/'
              'BP_FirstPersonCharacter.BP_FirstPersonCharacter_C'))
    BPT.add_variable(child, 'Hits', 'int')
    BPT.add_function_graph(child, 'KL_OnPress')
    BPT.write_graph_dsl(BPT.get_graph(child, 'KL_OnPress'),
                        '(fn KL_OnPress ()\n  (Variables|Default|SetHits 1))')
    BPT.compile_blueprint(child)

    p('=== A. function-path call nodes ===')
    paths = [
        '/Script/EnhancedInput.EnhancedInputComponent:BindAction',
        '/Script/EnhancedInput.EnhancedInputComponent:BindKey',
        '/Script/Engine.InputComponent:BindAction',
        '/Script/Engine.InputComponent:BindKey',
        '/Script/Engine.Actor:GetInputComponent',
        '/Script/Engine.InputComponent:GetInputComponent',
    ]
    for path in paths:
        def go(path=path):
            g = unreal.BlueprintEditorLibrary.find_event_graph(child)
            ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
            n = ed.add_call_function_node(path)
            if n is None:
                return 'None'
            dump(path, n)
            ed.remove_nodes([n])
            return 'ok'
        attempt('add_call_function_node %s' % path, go)

    p('')
    p('=== B. what IS the correct accessor for the input component? ===')
    g = unreal.BlueprintEditorLibrary.find_event_graph(child)
    for pat in ('InputComponent', 'GetPawn', 'SetupPlayerInput'):
        p('  %-22s %s' % (pat, BPT.find_node_types(g, pat)[:10]))

    p('')
    p('=== C. Blueprint input delegate bindings property ===')
    for prop in ('input_delegate_bindings', 'InputDelegateBindings'):
        try:
            v = child.get_editor_property(prop)
            p('  %s = %s' % (prop, v))
        except Exception as exc:
            p('  %s -> %s' % (prop, str(exc)[:130]))

    p('')
    p('=== D. real DSL: SetupPlayerInputComponent + BindAction ===')
    code = (
        '(event SetupPlayerInputComponent\n'
        '  (bind ic (Actor|GetComponentbyClass self '
        '"/Script/EnhancedInput.EnhancedInputComponent"))\n'
        '  (Class|EnhancedInputComponent|BindAction ic '
        '"/Game/KhoangLang/Input/IA_KL_Test.IA_KL_Test" "Triggered"\n'
        '    (:"Create New Event"\n'
        '      (bind ev (AddEvent|Custom|KL_Interact)\n'
        '        (|KL_OnPress))))'
    )

    def do_dsl():
        eg = unreal.BlueprintEditorLibrary.find_event_graph(child)
        BPT.write_graph_dsl(eg, code)
        BPT.compile_blueprint(child)
        ed2 = unreal.BlueprintGraphEditor.get_graph_editor(eg)
        nodes = list(ed2.list_all_nodes())
        p('  nodes after write: %d' % len(nodes))
        for n in nodes:
            p('   %-40s %r' % (n.get_class().get_name(), _get_node_type_id(n)))
        p('  status: %s' % child.get_editor_property('status'))
        p('  functions: %s' % [str(f.name) for f in BPT.list_functions(child)])
        return len(nodes)
    attempt('dsl bind action', do_dsl)

    p('')
    p('=== E. simpler: does the DSL keep an event it created earlier? ===')
    code2 = ('(event EventBeginPlay\n  (Development|PrintString :InString "hello-bp"))')
    attempt('plain beginplay write', lambda: BPT.write_graph_dsl(
        unreal.BlueprintEditorLibrary.find_event_graph(child), code2))
    eg = unreal.BlueprintEditorLibrary.find_event_graph(child)
    ed3 = unreal.BlueprintGraphEditor.get_graph_editor(eg)
    p('  nodes now: %d' % len(list(ed3.list_all_nodes())))
    for n in ed3.list_all_nodes():
        p('   %-40s %r' % (n.get_class().get_name(), _get_node_type_id(n)))

    p('')
    p('=== cleanup ===')
    unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP20_Char')
    unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Input/IA_KL_Test')
    p('PROBE20_DONE')


try:
    rep = os.path.join(OUT_DIR, 'report.txt')
    if os.path.exists(rep):
        os.remove(rep)
    main()
except Exception:
    p(traceback.format_exc())
    p('PROBE20_DONE_FATAL')
