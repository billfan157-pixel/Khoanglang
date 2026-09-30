"""Discovery probe 23: final input gate - key polling inside a cast continuation."""

import os
import sys
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
sys.path.insert(0, HERE)

OUT_DIR = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p23'
os.makedirs(OUT_DIR, exist_ok=True)
REPORT = []


def p(msg):
    line = str(msg)
    REPORT.append(line)
    unreal.log('KL23: ' + line)
    with open(os.path.join(OUT_DIR, 'report.txt'), 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


def attempt(label, fn):
    try:
        r = fn()
        p('  PASS %s %s' % (label, '' if r is None else r))
        return True
    except Exception as exc:
        p('  FAIL %s -> %s' % (label, str(exc)[:600]))
        return False


def graph_state(child):
    from editor_toolset.toolsets import blueprint as BP
    from editor_toolset.toolsets.blueprint import _get_node_type_id
    g = unreal.BlueprintEditorLibrary.find_event_graph(child)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    nodes = list(ed.list_all_nodes())
    errs = []
    for n in nodes:
        try:
            if n.has_error():
                errs.append('%s %r -> %s' % (n.get_class().get_name(),
                                             _get_node_type_id(n), n.error_msg()))
        except Exception:
            pass
    return len(nodes), errs, nodes


def main():
    from editor_toolset.toolsets import blueprint as BP
    BPT = BP.BlueprintTools
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.make_directory('/Game/KhoangLang/Data')
    if unreal.load_asset('/Game/KhoangLang/Data/TMP23_Char'):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP23_Char')

    child = BPT.create('/Game/KhoangLang/Data', 'TMP23_Char', unreal.load_class(
        None, '/Game/FirstPerson/Blueprints/'
              'BP_FirstPersonCharacter.BP_FirstPersonCharacter_C'))
    BPT.add_variable(child, 'Hits', 'int')
    BPT.add_function_graph(child, 'DoInteract')
    BPT.write_graph_dsl(BPT.get_graph(child, 'DoInteract'),
                        '(fn DoInteract ()\n  (Variables|Default|SetHits 1))')
    BPT.compile_blueprint(child)
    g = unreal.BlueprintEditorLibrary.find_event_graph(child)

    p('=== A. the exact shape, one key literal at a time ===')
    for lit in ('(KeyName="E")', '((KeyName="E"))', 'E'):
        code = (
            '(event EventTick\n'
            '  (bind ctrl (Pawn|GetController))\n'
            '  (bind pc (Utilities|Casting|CastToPlayerController :Object ctrl)\n'
            '    (:then\n'
            '      (if (Game|Player|WasInputKeyJustPressed pc %s)\n'
            '        (|DoInteract)))))' % lit
        )

        def go(code=code, lit=lit):
            BPT.write_graph_dsl(g, code)
            BPT.compile_blueprint(child)
            n, errs, _ = graph_state(child)
            p('    literal=%-16s nodes=%d status=%s errs=%s'
              % (lit, n, child.get_editor_property('status'), errs[:3]))
            return n
        attempt('literal %s' % lit, go)

    p('')
    p('=== B. round-trip read ===')
    try:
        for ln in str(BPT.read_graph_dsl(g)).splitlines():
            p('   ' + ln)
    except Exception as exc:
        p('  read failed %r' % (exc,))

    p('')
    p('=== C. trace + focus in the same tick ===')
    code = (
        '(event EventTick\n'
        '  (bind ctrl (Pawn|GetController))\n'
        '  (bind pc (Utilities|Casting|CastToPlayerController :Object ctrl)\n'
        '    (:then\n'
        '      (if (Game|Player|WasInputKeyJustPressed pc (KeyName="Q"))\n'
        '        (|DoInteract))\n'
        '      (bind hit (Collision|SphereTraceByChannel '
        '(Transformation|GetActorLocation) (Transformation|GetActorLocation) '
        '8.0 "Visibility"))\n'
        '      (if hit\n'
        '        (|DoInteract)))))'
    )

    def c():
        BPT.write_graph_dsl(g, code)
        BPT.compile_blueprint(child)
        n, errs, _ = graph_state(child)
        p('    nodes=%d status=%s errs=%s' % (n, child.get_editor_property('status'), errs[:3]))
    attempt('trace in tick', c)
    try:
        for ln in str(BPT.read_graph_dsl(g)).splitlines():
            p('   ' + ln)
    except Exception as exc:
        p('  read failed %r' % (exc,))

    p('')
    p('=== cleanup ===')
    unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP23_Char')
    p('PROBE23_DONE')


try:
    rep = os.path.join(OUT_DIR, 'report.txt')
    if os.path.exists(rep):
        os.remove(rep)
    main()
except Exception:
    p(traceback.format_exc())
    p('PROBE23_DONE_FATAL')
