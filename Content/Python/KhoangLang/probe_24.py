"""Discovery probe 24: verify the exact statement shapes the build will use.

Every case is verified by node count + node errors + a DSL round-trip read,
because write_graph_dsl can silently drop multi-exec bodies.
"""

import os
import sys
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
sys.path.insert(0, HERE)

OUT_DIR = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p24'
os.makedirs(OUT_DIR, exist_ok=True)
REPORT = []


def p(msg):
    line = str(msg)
    REPORT.append(line)
    unreal.log('KL24: ' + line)
    with open(os.path.join(OUT_DIR, 'report.txt'), 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


def state(bp):
    from editor_toolset.toolsets import blueprint as BP
    from editor_toolset.toolsets.blueprint import _get_node_type_id
    g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    nodes = list(ed.list_all_nodes())
    errs = []
    for n in nodes:
        try:
            if n.has_error():
                errs.append('%s %r %s' % (n.get_class().get_name(),
                                          _get_node_type_id(n), n.error_msg()))
        except Exception:
            pass
    return g, len(nodes), errs


def attempt(label, fn):
    try:
        r = fn()
        p('  PASS %s %s' % (label, '' if r is None else r))
        return True
    except Exception as exc:
        p('  FAIL %s -> %s' % (label, str(exc)[:600]))
        return False


def main():
    from editor_toolset.toolsets import blueprint as BP
    BPT = BP.BlueprintTools
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.make_directory('/Game/KhoangLang/Data')
    for n in ('TMP24_Target', 'TMP24_PC', 'TMP24_Char', 'TMP24_HUD'):
        if unreal.load_asset('/Game/KhoangLang/Data/' + n):
            unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/' + n)

    # target actor with a function
    tgt = BPT.create('/Game/KhoangLang/Data', 'TMP24_Target', unreal.Actor.static_class())
    BPT.add_variable(tgt, 'N', 'int')
    gT = BPT.add_function_graph(tgt, 'Ping')
    BPT.add_function_param(gT, 'Times', 'int', True)
    BPT.add_function_param(gT, 'Out', 'string', False)
    BPT.write_graph_dsl(gT, '(fn Ping (Times)\n  (return "pong"))')
    BPT.compile_blueprint(tgt)
    eas.save_asset('/Game/KhoangLang/Data/TMP24_Target', only_if_is_dirty=False)

    pc = BPT.create('/Game/KhoangLang/Data', 'TMP24_PC', unreal.load_class(
        None, '/Game/FirstPerson/Blueprints/'
              'BP_FirstPersonPlayerController.BP_FirstPersonPlayerController_C'))
    BPT.add_variable(pc, 'Flag', 'bool')
    BPT.add_variable(pc, 'Log', 'string')
    BPT.add_function_graph(pc, 'DoThing')
    BPT.write_graph_dsl(BPT.get_graph(pc, 'DoThing'),
                        '(fn DoThing ()\n  (Variables|Default|SetFlag true))')
    BPT.compile_blueprint(pc)

    g = unreal.BlueprintEditorLibrary.find_event_graph(pc)

    def run(label, code):
        def go():
            BPT.write_graph_dsl(g, code)
            BPT.compile_blueprint(pc)
            gg, n, errs = state(pc)
            p('    %-34s nodes=%d status=%s errs=%d' % (label, n,
                                                       pc.get_editor_property('status'),
                                                       len(errs)))
            for e in errs[:4]:
                p('        ERR %s' % e)
            try:
                for ln in str(BPT.read_graph_dsl(gg)).splitlines():
                    p('        | %s' % ln)
            except Exception as exc:
                p('        read failed %r' % (exc,))
            return n
        return attempt(label, go)

    p('=== A. single if ===')
    run('if', '(event EventTick\n'
              '  (if (Variables|Default|GetFlag)\n'
              '    (|DoThing)))')

    p('')
    p('=== B. if / else ===')
    run('if-else', '(event EventTick\n'
                   '  (if (Variables|Default|GetFlag)\n'
                   '    (|DoThing)\n'
                   '    (else\n'
                   '      (Variables|Default|SetFlag false))))')

    p('')
    p('=== C. two sequential ifs + a plain statement ===')
    run('seq', '(event EventTick\n'
               '  (if (Variables|Default|GetFlag) (|DoThing))\n'
               '  (if (Variables|Default|GetFlag) (Variables|Default|SetFlag false))\n'
               '  (Development|PrintString :InString "tick"))')

    p('')
    p('=== D. key literal on a player controller (self is the PC) ===')
    for lit in ('(KeyName="E")', '((KeyName="E"))', 'E'):
        run('key %s' % lit,
            '(event EventTick\n'
            '  (if (Game|Player|WasInputKeyJustPressed self %s)\n'
            '    (|DoThing)))' % lit)

    p('')
    p('=== E. GetActorOfClass typed result -> cross-BP call (no cast) ===')
    run('typed get',
        '(event EventTick\n'
        '  (bind t (Actor|GetActorOfClass "/Game/KhoangLang/Data/TMP24_Target'
        '.TMP24_Target_C"))\n'
        '  (bind s (TMP24_Target_C|Ping t 2))\n'
        '  (Variables|Default|SetLog s))')

    p('')
    p('=== F. GetAllActorsOfClass + for loop + typed call ===')
    run('for each',
        '(event EventTick\n'
        '  (bind list (Actor|GetAllActorsOfClass "/Game/KhoangLang/Data/TMP24_Target'
        '.TMP24_Target_C"))\n'
        '  (for e list\n'
        '    (bind s (TMP24_Target_C|Ping e 1))\n'
        '    (Variables|Default|SetLog s)))')

    p('')
    p('=== G. HUD access from the PC ===')
    for pat in ('HUD|GetHUD', 'GetHUD', 'PlayerController|GetPawn', 'Class|PlayerController|GetPawn',
                'GetPlayerViewPoint', 'ProjectWorldLocation'):
        p('  %-36s %s' % (pat, BPT.find_node_types(g, pat)[:6]))
    run('get hud',
        '(event EventTick\n'
        '  (bind h (HUD|GetHUD))\n'
        '  (Development|PrintString :InString "hud"))')

    p('')
    p('=== H. string helpers + select ===')
    run('select', '(event EventTick\n'
                  '  (Variables|Default|SetLog (Utilities|Select '
                  '(Variables|Default|GetFlag) "on" "off")))')
    run('concat', '(event EventTick\n'
                  '  (Variables|Default|SetLog (+ "a" "b")))')

    p('')
    p('=== cleanup ===')
    for n in ('TMP24_Target', 'TMP24_PC'):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/' + n)
    p('PROBE24_DONE')


try:
    rep = os.path.join(OUT_DIR, 'report.txt')
    if os.path.exists(rep):
        os.remove(rep)
    main()
except Exception:
    p(traceback.format_exc())
    p('PROBE24_DONE_FATAL')
