"""Discovery probe 27: the manual graph-builder API surface.

write_graph_dsl cannot create Blueprint variable accessors or Blueprint function
calls, so the build must wire nodes by hand. This probe pins down every call.
"""

import os
import sys
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
sys.path.insert(0, HERE)

OUT_DIR = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p27'
os.makedirs(OUT_DIR, exist_ok=True)
REPORT = []


def p(msg):
    line = str(msg)
    REPORT.append(line)
    unreal.log('KL27: ' + line)
    with open(os.path.join(OUT_DIR, 'report.txt'), 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


def pins(node):
    from editor_toolset.toolsets import blueprint as BP
    ni = BP.BlueprintTools.get_node_infos([node])[0]
    out = []
    for x in ni.input_pins:
        out.append('IN %s:%s' % (x.name, x.type_id))
    for x in ni.output_pins:
        out.append('OUT %s:%s' % (x.name, x.type_id))
    return ' | '.join(out)


def main():
    from editor_toolset.toolsets import blueprint as BP
    from editor_toolset.toolsets.blueprint import _get_node_type_id
    BPT = BP.BlueprintTools
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.make_directory('/Game/KhoangLang/Data')
    for n in ('TMP27_Target', 'TMP27_PC'):
        if unreal.load_asset('/Game/KhoangLang/Data/' + n):
            unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/' + n)

    # ---- target blueprint with a function
    tgt = BPT.create('/Game/KhoangLang/Data', 'TMP27_Target', unreal.Actor.static_class())
    fg = BPT.add_function_graph(tgt, 'Ping')
    BPT.add_function_param(fg, 'Times', 'int', True)
    BPT.add_function_param(fg, 'Out', 'string', False)
    BPT.write_graph_dsl(fg, '(fn Ping (Times)\n  (return "pong"))')
    BPT.compile_blueprint(tgt)
    eas.save_asset('/Game/KhoangLang/Data/TMP27_Target', only_if_is_dirty=False)

    # ---- caller blueprint
    pc = BPT.create('/Game/KhoangLang/Data', 'TMP27_PC', unreal.load_class(
        None, '/Game/FirstPerson/Blueprints/'
              'BP_FirstPersonPlayerController.BP_FirstPersonPlayerController_C'))
    BPT.add_variable(pc, 'Flag', 'bool')
    BPT.add_variable(pc, 'Log', 'string')
    BPT.add_variable(pc, 'Num', 'int')
    fgc = BPT.add_function_graph(pc, 'DoThing')
    BPT.add_function_param(fgc, 'Amount', 'int', True)
    BPT.add_function_param(fgc, 'Said', 'string', False)
    BPT.write_graph_dsl(fgc, '(fn DoThing (Amount)\n  (return "said"))')
    BPT.compile_blueprint(pc)
    g = unreal.BlueprintEditorLibrary.find_event_graph(pc)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)

    p('=== A. member variable accessor nodes ===')
    for maker, nm in (('add_get_member_variable_node', 'get'),
                      ('add_set_member_variable_node', 'set')):
        fn = getattr(ed, maker, None)
        p('  %s available: %s' % (maker, fn is not None))
        if fn is None:
            continue
        try:
            n = fn(unreal.Name('Flag'))
            if n is None:
                p('    -> None')
            else:
                p('    %s -> %s / %r' % (nm, n.get_class().get_name(),
                                         _get_node_type_id(n)))
                p('       %s' % pins(n))
                ed.remove_nodes([n])
        except Exception as exc:
            p('    %s raised %r' % (nm, exc))

    p('')
    p('=== B. branch / return / custom event nodes ===')
    for maker, args in (('add_branch_node', ()),
                        ('add_return_node', ()),
                        ('add_custom_event_node', ('KL_Probe',))):
        fn = getattr(ed, maker, None)
        if fn is None:
            p('  %s MISSING' % maker)
            continue
        try:
            n = fn(*args)
            p('  %s -> %s / %r' % (maker, n.get_class().get_name() if n else None,
                                    _get_node_type_id(n) if n else None))
            if n:
                p('     %s' % pins(n))
                ed.remove_nodes([n])
        except Exception as exc:
            p('  %s raised %r' % (maker, exc))

    p('')
    p('=== C. add_call_function_node path formats ===')
    formats = [
        'Development|PrintString',
        '/Script/Engine.PrintString',
        'KismetSystemLibrary.PrintString',
        'GameplayStatics.PrintString',
        '/Script/Engine.GameplayStatics:PrintString',
        '/Script/Engine.KismetSystemLibrary:PrintString',
        'KismetSystemLibrary:PrintString',
        'GameplayStatics:PrintString',
        '/Script/Engine.PlayerController:K2_DeprecatedShowDebug',
        'PlayerController:K2_DeprecatedShowDebug',
        '/Game/KhoangLang/Data/TMP27_Target.TMP27_Target_C:Ping',
        '/Game/KhoangLang/Data/TMP27_Target.TMP27_Target_C.Ping',
        'TMP27_Target_C:Ping',
        '/Game/KhoangLang/Data/TMP27_PC.TMP27_PC_C:DoThing',
        'TMP27_PC_C:DoThing',
        'DoThing',
    ]
    for f in formats:
        try:
            n = ed.add_call_function_node(f)
            if n is None:
                p('  %-58s -> None' % f)
            else:
                p('  %-58s -> %s / %r' % (f, n.get_class().get_name(),
                                          _get_node_type_id(n)))
                ed.remove_nodes([n])
        except Exception as exc:
            p('  %-58s raised %r' % (f, exc))

    p('')
    p('=== D. hand-built graph: beginplay -> set flag -> branch -> print ===')
    try:
        g2 = unreal.BlueprintEditorLibrary.find_event_graph(pc)
        ed = unreal.BlueprintGraphEditor.get_graph_editor(g2)
        for n in list(ed.list_all_nodes()):
            if n.get_class().get_name() == 'K2Node_Event' and \
                    _get_node_type_id(n) == 'AddEvent|EventBeginPlay':
                ed.remove_nodes([n])
        begin = ed.create_node_from_name('AddEvent|EventBeginPlay',
                                         unreal.Vector2D(0, 0), [], None)
        p('  begin: %s / %s' % (begin.get_class().get_name(), pins(begin)))
        setter = ed.add_set_member_variable_node(unreal.Name('Flag'))
        p('  setter: %s' % pins(setter))
        br = ed.add_branch_node()
        p('  branch: %s' % pins(br))
        pr = ed.create_node_from_name('Development|PrintString',
                                      unreal.Vector2D(600, 0), [], None)
        p('  print: %s' % pins(pr))

        from editor_toolset.toolsets import blueprint as BPT2
        infos = BPT2.BlueprintTools.get_node_infos([begin, setter, br, pr])
        ib, iset, ibr, ipr = infos

        def outp(info, name):
            return next(x for x in info.output_pins if x.name == name)

        def inp(info, name):
            return next(x for x in info.input_pins if x.name == name)

        BPT2.BlueprintTools.connect_pins(outp(ib, 'then').pin_id,
                                        inp(iset, 'execute').pin_id)
        BPT2.BlueprintTools.connect_pins(outp(iset, 'then').pin_id,
                                        inp(ibr, 'execute').pin_id)
        getter = ed.add_get_member_variable_node(unreal.Name('Flag'))
        ginfo = BPT2.BlueprintTools.get_node_infos([getter])[0]
        p('  getter: %s' % pins(getter))
        BPT2.BlueprintTools.connect_pins(
            next(x for x in ginfo.output_pins if x.type_id != 'Exec').pin_id,
            inp(ibr, 'Condition').pin_id)
        BPT2.BlueprintTools.connect_pins(outp(ibr, 'True').pin_id,
                                        inp(ipr, 'execute').pin_id)
        BPT2.BlueprintTools.compile_blueprint(pc)
        p('  status: %s' % pc.get_editor_property('status'))
        p('  errors: %s' % [n.error_msg() for n in
                            unreal.BlueprintGraphEditor.get_graph_editor(g2).list_all_nodes()
                            if n.has_error()])
        p('  round trip:')
        for ln in str(BPT2.BlueprintTools.read_graph_dsl(g2)).splitlines():
            p('     | %s' % ln)
    except Exception as exc:
        p('  D failed: %r' % (exc,))
        p(traceback.format_exc())

    p('')
    p('=== cleanup ===')
    for n in ('TMP27_Target', 'TMP27_PC'):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/' + n)
    p('PROBE27_DONE')


try:
    rep = os.path.join(OUT_DIR, 'report.txt')
    if os.path.exists(rep):
        os.remove(rep)
    main()
except Exception:
    p(traceback.format_exc())
    p('PROBE27_DONE_FATAL')
