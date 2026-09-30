"""Discovery probe 25: get the REAL exception behind write_graph_dsl's silent rollback.

write_graph_dsl() swallows errors, so the same Transpiler is driven directly here.
"""

import os
import sys
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
sys.path.insert(0, HERE)

OUT_DIR = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p25'
os.makedirs(OUT_DIR, exist_ok=True)
REPORT = []


def p(msg):
    line = str(msg)
    REPORT.append(line)
    unreal.log('KL25: ' + line)
    with open(os.path.join(OUT_DIR, 'report.txt'), 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


def main():
    from editor_toolset.toolsets import blueprint as BP
    from editor_toolset.toolsets import blueprint_dsl as BD
    BPT = BP.BlueprintTools
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.make_directory('/Game/KhoangLang/Data')
    if unreal.load_asset('/Game/KhoangLang/Data/TMP25_PC'):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP25_PC')

    pc = BPT.create('/Game/KhoangLang/Data', 'TMP25_PC', unreal.load_class(
        None, '/Game/FirstPerson/Blueprints/'
              'BP_FirstPersonPlayerController.BP_FirstPersonPlayerController_C'))
    BPT.add_variable(pc, 'Flag', 'bool')
    BPT.add_variable(pc, 'Log', 'string')
    BPT.add_variable(pc, 'Num', 'int')
    BPT.add_function_graph(pc, 'DoThing')
    BPT.write_graph_dsl(BPT.get_graph(pc, 'DoThing'),
                        '(fn DoThing ()\n  (Variables|Default|SetFlag true))')
    BPT.compile_blueprint(pc)
    g = unreal.BlueprintEditorLibrary.find_event_graph(pc)

    def raw(label, code):
        tr = BD.Transpiler(
            g,
            BPT.create_node,
            BPT.connect_pins,
            BPT._get_node_info,
            BPT.set_pin_value,
            lambda gg: BPT.find_nodes(gg),
            delete_node_fn=BPT.delete_node,
            find_node_types_fn=lambda f: BPT.find_node_types(g, f),
        )
        try:
            tr.transpile(code)
            n = len(list(unreal.BlueprintGraphEditor.get_graph_editor(g).list_all_nodes()))
            p('  OK   %-30s nodes=%d' % (label, n))
            return True
        except Exception as exc:
            p('  ERR  %-30s %s' % (label, str(exc)[:400]))
            return False

    p('=== isolating each construct with the real exception ===')
    raw('plain print', '(event EventTick\n  (Development|PrintString "x"))')
    raw('set bool', '(event EventTick\n  (Variables|Default|SetFlag true))')
    raw('get bool bind',
        '(event EventTick\n  (bind f (Variables|Default|GetFlag))\n'
        '  (Development|PrintString "x"))')
    raw('if', '(event EventTick\n  (if (Variables|Default|GetFlag)\n'
             '    (Development|PrintString "a")))')
    raw('if else', '(event EventTick\n  (if (Variables|Default|GetFlag)\n'
                   '    (Development|PrintString "a")\n    (else\n'
                   '      (Development|PrintString "b")))')
    raw('own fn call', '(event EventTick\n  (|DoThing))')
    raw('key literal', '(event EventTick\n  (if (Game|Player|WasInputKeyJustPressed self '
                       '(KeyName="E"))\n    (Development|PrintString "e")))')
    raw('key literal nodirect', '(event EventTick\n'
                               '  (bind k (Game|Player|WasInputKeyJustPressed self '
                               '(KeyName="E")))\n  (Development|PrintString "e"))')
    raw('get actor of class', '(event EventTick\n'
                              '  (bind t (Actor|GetActorOfClass "/Game/FirstPerson/Blueprints/'
                              'BP_FirstPersonGameMode.BP_FirstPersonGameMode_C"))\n'
                              '  (Development|PrintString "t"))')
    raw('get all of class', '(event EventTick\n'
                            '  (bind l (Actor|GetAllActorsOfClass "/Game/FirstPerson/Blueprints/'
                            'BP_FirstPersonGameMode.BP_FirstPersonGameMode_C"))\n'
                            '  (Development|PrintString "l"))')
    raw('for each', '(event EventTick\n  (bind l (Actor|GetAllActorsOfClass '
                    '"/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode'
                    '.BP_FirstPersonGameMode_C"))\n'
                    '  (for e l\n    (Development|PrintString "e")))')
    raw('math', '(event EventTick\n  (Variables|Default|SetNum (+ 1 2)))')
    raw('string append', '(event EventTick\n  (Variables|Default|SetLog (+ "a" "b")))')
    raw('drawtext on hud? (not here)', '(event EventTick\n  (Development|PrintString "z"))')

    p('')
    p('=== what the Tick graph looks like now ===')
    for ln in str(BPT.read_graph_dsl(g)).splitlines():
        p('   ' + ln)

    p('')
    p('=== cleanup ===')
    unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP25_PC')
    p('PROBE25_DONE')


try:
    rep = os.path.join(OUT_DIR, 'report.txt')
    if os.path.exists(rep):
        os.remove(rep)
    main()
except Exception:
    p(traceback.format_exc())
    p('PROBE25_DONE_FATAL')
