"""Discovery probe 22: poll keys in Tick (no new input event nodes needed)."""

import os
import sys
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
sys.path.insert(0, HERE)

OUT_DIR = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p22'
os.makedirs(OUT_DIR, exist_ok=True)
REPORT = []


def p(msg):
    line = str(msg)
    REPORT.append(line)
    unreal.log('KL22: ' + line)
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
    eas.make_directory('/Game/KhoangLang/Data')
    if unreal.load_asset('/Game/KhoangLang/Data/TMP22_Char'):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP22_Char')

    child = BPT.create('/Game/KhoangLang/Data', 'TMP22_Char', unreal.load_class(
        None, '/Game/FirstPerson/Blueprints/'
              'BP_FirstPersonCharacter.BP_FirstPersonCharacter_C'))
    BPT.add_variable(child, 'Hits', 'int')
    BPT.add_variable(child, 'Flag', 'bool')
    BPT.compile_blueprint(child)
    eg = unreal.BlueprintEditorLibrary.find_event_graph(child)

    p('=== A. pins ===')
    for nid in ('Game|Player|WasInputKeyJustPressed', 'Game|Player|IsInputKeyDown',
                'Game|Player|GetInputKeyTimeDown', 'Pawn|GetController',
                'Utilities|Casting|CastToPlayerController'):
        hits = BPT.find_node_types(eg, nid)
        if not hits:
            p('  %s MISSING' % nid)
            continue
        ni = BPT.get_node_type_pins(eg, hits[0])
        p('  %s' % hits[0])
        for x in ni.input_pins:
            p('     IN  %-22s %s' % (x.name, x.type_id))
        for x in ni.output_pins:
            p('     OUT %-22s %s' % (x.name, x.type_id))

    p('')
    p('=== B. literal FInputKeyParams in the DSL ===')
    for lit in ('(KeyName="E")', '((KeyName="E"))', '"E"'):
        code = (
            '(event EventTick\n'
            '  (bind ctrl (Pawn|GetController))\n'
            '  (bind pc (Utilities|Casting|CastToPlayerController :Object ctrl))\n'
            '  (if (Game|Player|WasInputKeyJustPressed pc %s)\n'
            '    (Variables|Default|SetHits 1)))' % lit
        )

        def go(code=code, lit=lit):
            g = unreal.BlueprintEditorLibrary.find_event_graph(child)
            BPT.write_graph_dsl(g, code)
            BPT.compile_blueprint(child)
            p('    status=%s nodes=%d' % (child.get_editor_property('status'),
                                         len(nodes_of(child))))
            return lit
        attempt('key literal %s' % lit, go)

    p('')
    p('=== C. inspect the produced Tick graph ===')
    g = unreal.BlueprintEditorLibrary.find_event_graph(child)
    try:
        code = BPT.read_graph_dsl(g)
        for ln in str(code).splitlines():
            p('   ' + ln)
    except Exception as exc:
        p('  read failed %r' % (exc,))
    p('  status: %s' % child.get_editor_property('status'))
    for n in nodes_of(child):
        p('   %-40s %r' % n)

    p('')
    p('=== D. node errors ===')
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    try:
        for n in ed.list_nodes_with_errors():
            p('   ERR %s %r -> %s' % (n.get_class().get_name(), _get_node_type_id(n),
                                      n.error_msg))
    except Exception as exc:
        p('  list_nodes_with_errors failed %r' % (exc,))

    p('')
    p('=== cleanup ===')
    unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP22_Char')
    p('PROBE22_DONE')


try:
    rep = os.path.join(OUT_DIR, 'report.txt')
    if os.path.exists(rep):
        os.remove(rep)
    main()
except Exception:
    p(traceback.format_exc())
    p('PROBE22_DONE_FATAL')
