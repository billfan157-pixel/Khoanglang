"""Discovery probe 19: bind Enhanced Input actions from Python.

The only supported way left to get new input events is to call
UEnhancedInputComponent::BindAction (a BlueprintCallable CustomThunk) from
Setup Player Input Component and bind the delegate to a custom event.
"""

import os
import sys
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
sys.path.insert(0, HERE)

OUT_DIR = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p19'
os.makedirs(OUT_DIR, exist_ok=True)
REPORT = []


def p(msg):
    line = str(msg)
    REPORT.append(line)
    unreal.log('KL19: ' + line)
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


def pins(tag, node):
    from editor_toolset.toolsets import blueprint as BP
    ni = BP.BlueprintTools.get_node_infos([node])[0]
    p('  %s pins:' % tag)
    for x in ni.input_pins:
        p('     IN  %-22s %s' % (x.name, x.type_id))
    for x in ni.output_pins:
        p('     OUT %-22s %s' % (x.name, x.type_id))


def main():
    from editor_toolset.toolsets import blueprint as BP
    from editor_toolset.toolsets.blueprint import _get_node_type_id
    BPT = BP.BlueprintTools
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    at = unreal.AssetToolsHelpers.get_asset_tools()
    eas.make_directory('/Game/KhoangLang/Input')
    eas.make_directory('/Game/KhoangLang/Data')

    p('add_call_function_node doc: %s' % unreal.BlueprintGraphEditor.add_call_function_node.__doc__)
    p('add_component_bound_event_node doc: %s'
      % unreal.BlueprintGraphEditor.add_component_bound_event_node.__doc__)

    for n in ('TMP19_Char',):
        if unreal.load_asset('/Game/KhoangLang/Data/' + n):
            unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/' + n)
    if unreal.load_asset('/Game/KhoangLang/Input/IA_KL_Test'):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Input/IA_KL_Test')
    ia = at.create_asset('IA_KL_Test', '/Game/KhoangLang/Input', unreal.InputAction,
                         unreal.InputAction_Factory())
    ia.set_editor_property('value_type', unreal.InputActionValueType.BOOLEAN)
    eas.save_asset('/Game/KhoangLang/Input/IA_KL_Test', only_if_is_dirty=False)

    child = BPT.create('/Game/KhoangLang/Data', 'TMP19_Char', unreal.load_class(
        None, '/Game/FirstPerson/Blueprints/'
              'BP_FirstPersonCharacter.BP_FirstPersonCharacter_C'))
    eg = unreal.BlueprintEditorLibrary.find_event_graph(child)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(eg)
    BPT.add_variable(child, 'Hits', 'int')
    BPT.add_function_graph(child, 'KL_OnPress')
    BPT.write_graph_dsl(BPT.get_graph(child, 'KL_OnPress'),
                        '(fn KL_OnPress ()\n  (Variables|Default|SetHits 1))')

    p('')
    p('=== A. add_call_function_node on EnhancedInputComponent ===')
    for fname in ('BindAction', 'BindKey', 'RemoveBindingByHandle'):
        def go(fname=fname):
            n = ed.add_call_function_node(unreal.EnhancedInputComponent, fname, eg,
                                         unreal.IntPoint(400, 0))
            if n is None:
                return 'None'
            pins(fname, n)
            return '%s / %r' % (n.get_class().get_name(), _get_node_type_id(n))
        attempt('add_call_function_node %s' % fname, go)

    p('')
    p('=== B. full DSL BindAction + custom event ===')
    code = (
        '(event SetupPlayerInputComponent\n'
        '  (bind ic (Actor|GetComponentbyClass self '
        '"/Script/EnhancedInput.EnhancedInputComponent"))\n'
        '  (Class|EnhancedInputComponent|BindAction ic "/Game/KhoangLang/Input/IA_KL_Test'
        '.IA_KL_Test" "Triggered"\n'
        '    (:"Create New Event"\n'
        '      (bind ev (AddEvent|Custom|KL_Interact)\n'
        '        (|KL_OnPress))))'
    )
    if attempt('dsl BindAction', lambda: BPT.write_graph_dsl(eg, code)):
        attempt('compile', lambda: BPT.compile_blueprint(child))
        p('  status: %s' % child.get_editor_property('status'))
        p('  nodes:')
        for n in ed.list_all_nodes():
            p('   %-40s %r' % (n.get_class().get_name(), _get_node_type_id(n)))
        p('  functions: %s' % [str(f.name) for f in BPT.list_functions(child)])

    p('')
    p('=== C. legacy UInputComponent::BindAction / BindKey ===')
    for fname in ('BindAction', 'BindKey', 'BindAxis', 'BindTouch'):
        def go(fname=fname):
            n = ed.add_call_function_node(unreal.InputComponent, fname, eg,
                                         unreal.IntPoint(600, 0))
            if n is None:
                return 'None'
            pins('%s (InputComponent)' % fname, n)
            return '%r' % _get_node_type_id(n)
        attempt('add_call_function_node %s' % fname, go)

    p('')
    p('=== D. get the enhanced input component: candidate nodes ===')
    for pat in ('GetInputComponent', 'EnhancedInputComponent'):
        p('  %-24s %s' % (pat, BPT.find_node_types(eg, pat)[:8]))
    attempt('component-by-class node', lambda: BPT.write_graph_dsl(eg, (
        '(event EventBeginPlay\n'
        '  (bind ic (Actor|GetComponentbyClass self '
        '"/Script/EnhancedInput.EnhancedInputComponent"))\n'
        '  (Development|PrintString :InString "got"))')))
    attempt('compile after comp', lambda: BPT.compile_blueprint(child))

    p('')
    p('=== cleanup ===')
    unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP19_Char')
    unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Input/IA_KL_Test')
    p('PROBE19_DONE')


try:
    rep = os.path.join(OUT_DIR, 'report.txt')
    if os.path.exists(rep):
        os.remove(rep)
    main()
except Exception:
    p(traceback.format_exc())
    p('PROBE19_FAILED')
