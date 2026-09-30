"""Discovery probe 21: the last input route.

  1. add_event_override for SetupPlayerInputComponent, then let the DSL fill it.
  2. Is UEnhancedInputComponent::BindAction in the action database?
  3. Can the DSL bind its 'Create New Event' delegate to a custom event?
"""

import os
import sys
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
sys.path.insert(0, HERE)

OUT_DIR = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p21'
os.makedirs(OUT_DIR, exist_ok=True)
REPORT = []


def p(msg):
    line = str(msg)
    REPORT.append(line)
    unreal.log('KL21: ' + line)
    with open(os.path.join(OUT_DIR, 'report.txt'), 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


def attempt(label, fn):
    try:
        r = fn()
        p('  PASS %s %s' % (label, '' if r is None else r))
        return True
    except Exception as exc:
        p('  FAIL %s -> %s' % (label, str(exc)[:500]))
        return False


def nodes_of(child):
    from editor_toolset.toolsets import blueprint as BP
    from editor_toolset.toolsets.blueprint import _get_node_type_id
    eg = unreal.BlueprintEditorLibrary.find_event_graph(child)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(eg)
    return [(n.get_class().get_name(), _get_node_type_id(n)) for n in ed.list_all_nodes()]


def main():
    from editor_toolset.toolsets import blueprint as BP
    from editor_toolset.toolsets.blueprint import _get_node_type_id
    BPT = BP.BlueprintTools
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    at = unreal.AssetToolsHelpers.get_asset_tools()
    eas.make_directory('/Game/KhoangLang/Input')
    eas.make_directory('/Game/KhoangLang/Data')

    if unreal.load_asset('/Game/KhoangLang/Data/TMP21_Char'):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP21_Char')
    if unreal.load_asset('/Game/KhoangLang/Input/IA_KL_Test'):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Input/IA_KL_Test')
    ia = at.create_asset('IA_KL_Test', '/Game/KhoangLang/Input', unreal.InputAction,
                         unreal.InputAction_Factory())
    if ia is None:
        ia = unreal.load_asset('/Game/KhoangLang/Input/IA_KL_Test')
        p('  reused existing IA_KL_Test: %s' % ia)
    ia.set_editor_property('value_type', unreal.InputActionValueType.BOOLEAN)
    eas.save_asset('/Game/KhoangLang/Input/IA_KL_Test', only_if_is_dirty=False)

    child = BPT.create('/Game/KhoangLang/Data', 'TMP21_Char', unreal.load_class(
        None, '/Game/FirstPerson/Blueprints/'
              'BP_FirstPersonCharacter.BP_FirstPersonCharacter_C'))
    BPT.add_variable(child, 'Hits', 'int')
    BPT.add_function_graph(child, 'KL_OnPress')
    BPT.write_graph_dsl(BPT.get_graph(child, 'KL_OnPress'),
                        '(fn KL_OnPress ()\n  (Variables|Default|SetHits 1))')
    BPT.compile_blueprint(child)
    BPT.add_object_variable(child, 'ProbeIco', unreal.Actor.static_class())

    p('=== A. inherited event list on the character ===')
    p('  events: %s' % [(str(e.name), e.is_implemented) for e in BPT.list_events(child)])

    p('')
    p('=== B. BindAction node availability ===')
    eg = unreal.BlueprintEditorLibrary.find_event_graph(child)
    for pat in ('BindAction', 'Class|EnhancedInputComponent', 'Class|InputComponent'):
        p('  %-32s %s' % (pat, BPT.find_node_types(eg, pat)[:10]))
    for cand in ('Class|EnhancedInputComponent|BindAction',
                 'Class|InputComponent|BindAction',
                 'Class|EnhancedInputComponent|BindKey'):
        hits = BPT.find_node_types(eg, cand)
        if hits:
            ni = BPT.get_node_type_pins(eg, hits[0])
            p('  %s' % hits[0])
            for x in ni.input_pins:
                p('     IN  %-22s %s' % (x.name, x.type_id))
            for x in ni.output_pins:
                p('     OUT %-22s %s' % (x.name, x.type_id))

    p('')
    p('=== C. add_event_override SetupPlayerInputComponent ===')

    def add_evt():
        n = BPT.add_event(child, 'SetupPlayerInputComponent')
        return '%s / %r' % (n.get_class().get_name(), _get_node_type_id(n))
    attempt('add_event SetupPlayerInputComponent', add_evt)
    p('  nodes: %s' % nodes_of(child))

    p('')
    p('=== D. DSL body into that event ===')
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

    def d():
        g = unreal.BlueprintEditorLibrary.find_event_graph(child)
        BPT.write_graph_dsl(g, code)
        BPT.compile_blueprint(child)
        p('  nodes: %s' % nodes_of(child))
        p('  status: %s' % child.get_editor_property('status'))
        p('  functions: %s' % [str(f.name) for f in BPT.list_functions(child)])
    attempt('dsl into SetupPlayerInputComponent', d)

    p('')
    p('=== E. fallback: a simple body, no BindAction ===')
    code2 = (
        '(event SetupPlayerInputComponent\n'
        '  (Development|PrintString :InString "setup"))'
    )

    def e2():
        g = unreal.BlueprintEditorLibrary.find_event_graph(child)
        BPT.write_graph_dsl(g, code2)
        p('  nodes: %s' % nodes_of(child))
    attempt('dsl simple body', e2)

    p('')
    p('=== cleanup ===')
    unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP21_Char')
    unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Input/IA_KL_Test')
    p('PROBE21_DONE')


try:
    rep = os.path.join(OUT_DIR, 'report.txt')
    if os.path.exists(rep):
        os.remove(rep)
    main()
except Exception:
    p(traceback.format_exc())
    p('PROBE21_DONE_FATAL')
