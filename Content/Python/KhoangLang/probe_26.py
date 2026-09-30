"""Discovery probe 26: the real action names for variables and own functions."""

import os
import sys
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
sys.path.insert(0, HERE)

OUT_DIR = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p26'
os.makedirs(OUT_DIR, exist_ok=True)
REPORT = []


def p(msg):
    line = str(msg)
    REPORT.append(line)
    unreal.log('KL26: ' + line)
    with open(os.path.join(OUT_DIR, 'report.txt'), 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


def main():
    from editor_toolset.toolsets import blueprint as BP
    from editor_toolset.toolsets import blueprint_dsl as BD
    BPT = BP.BlueprintTools
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.make_directory('/Game/KhoangLang/Data')
    if unreal.load_asset('/Game/KhoangLang/Data/TMP26_PC'):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP26_PC')

    pc = BPT.create('/Game/KhoangLang/Data', 'TMP26_PC', unreal.load_class(
        None, '/Game/FirstPerson/Blueprints/'
              'BP_FirstPersonPlayerController.BP_FirstPersonPlayerController_C'))
    BPT.add_variable(pc, 'Flag', 'bool')
    BPT.add_variable(pc, 'Log', 'string')
    BPT.add_variable(pc, 'Num', 'int')
    fg = BPT.add_function_graph(pc, 'DoThing')
    BPT.add_function_param(fg, 'Amount', 'int', True)
    BPT.add_function_param(fg, 'Said', 'string', False)
    BPT.write_graph_dsl(fg, '(fn DoThing (Amount)\n  (return "said"))')
    BPT.compile_blueprint(pc)
    g = unreal.BlueprintEditorLibrary.find_event_graph(pc)

    p('=== A. action names mentioning our members ===')
    for pat in ('Flag', 'Log', 'Num', 'DoThing', 'Variables', '|', 'Self'):
        hits = BPT.find_node_types(g, pat)
        p('  %-12s %d: %s' % (pat, len(hits), hits[:25]))

    p('')
    p('=== B. the decompiler\'s own ids for an existing call ===')
    code = '(event EventTick\n  (Development|PrintString "x"))'
    BPT.write_graph_dsl(g, code)
    for ln in str(BPT.read_graph_dsl(g)).splitlines():
        p('   ' + ln)

    p('')
    p('=== C. now build a graph by hand and read back the ids ===')
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    for nm in ('Variables|Default|GetFlag', 'Variables|Default|SetFlag',
               '|DoThing', 'Class|TMP26_PC_C|DoThing', 'TMP26_PC_C|DoThing',
               'Variables|GetFlag', 'Variables|SetFlag', 'Default|GetFlag',
               'Utilities|Operators|Add', 'Utilities|FlowControl|Branch'):
        n = ed.create_node_from_name(nm, unreal.Vector2D(0, 0), [], None)
        p('  create_node_from_name(%-34s) -> %s' % (nm, n.get_class().get_name()
                                                    if n else None))
        if n:
            p('     type_id=%r title=%r' % (BD.Decompiler and n.get_node_title(), n.get_node_title()))
            ed.remove_nodes([n])

    p('')
    p('=== D. what does read_graph_dsl emit for a real variable access? ===')
    # create a variable getter by whatever name works, then read it back
    for nm in ('Variables|Default|GetFlag', 'Variables|GetFlag', 'Default|GetFlag'):
        n = ed.create_node_from_name(nm, unreal.Vector2D(0, 0), [], None)
        if n:
            p('  SUCCESS id=%r -> type_id from toolset' % nm)
            p('     class=%s title=%r' % (n.get_class().get_name(), n.get_node_title()))
            BPT.compile_blueprint(pc)
            try:
                for ln in str(BPT.read_graph_dsl(g)).splitlines():
                    p('     | %s' % ln)
            except Exception as exc:
                p('     read failed %r' % (exc,))
            ed.remove_nodes([n])
            break
    for n in list(ed.list_all_nodes()):
        if n.get_class().get_name() not in ('K2Node_Event',):
            ed.remove_nodes([n])

    p('')
    p('=== E. how the decompiler names a self-property access in a template bp ===')
    tpl = unreal.load_asset('/Game/FirstPerson/Blueprints/BP_FirstPersonPlayerController')
    teg = unreal.BlueprintEditorLibrary.find_event_graph(tpl)
    for ln in str(BPT.read_graph_dsl(teg)).splitlines():
        p('   ' + ln)

    p('')
    p('=== F. how the decompiler names a variable access (character bp) ===')
    chr_bp = unreal.load_asset('/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter')
    cg = unreal.BlueprintEditorLibrary.find_event_graph(chr_bp)
    for ln in str(BPT.read_graph_dsl(cg)).splitlines():
        p('   ' + ln)
    p('  character vars: %s' % BPT.list_variables(chr_bp))
    hits = BPT.find_node_types(cg, 'Variable')
    p('  Variable-ish actions: %s' % hits[:20])
    for pat in ('bUseControllerRotationYaw', 'Variables', 'bIsCrouched', 'Getb'):
        p('  %-26s %s' % (pat, BPT.find_node_types(cg, pat)[:12]))

    p('')
    p('=== cleanup ===')
    unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP26_PC')
    p('PROBE26_DONE')


try:
    rep = os.path.join(OUT_DIR, 'report.txt')
    if os.path.exists(rep):
        os.remove(rep)
    main()
except Exception:
    p(traceback.format_exc())
    p('PROBE26_DONE_FATAL')
