"""Discovery probe 35: resolve the HUD overlay path."""

import os
import sys
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
sys.path.insert(0, HERE)

OUT_DIR = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p35'
os.makedirs(OUT_DIR, exist_ok=True)


def p(msg):
    line = str(msg)
    unreal.log('KL35: ' + line)
    with open(os.path.join(OUT_DIR, 'report.txt'), 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


def pins(node):
    from editor_toolset.toolsets import blueprint as BP
    ni = BP.BlueprintTools.get_node_infos([node])[0]
    ins = ', '.join('%s:%s' % (x.name, x.type_id) for x in ni.input_pins)
    outs = ', '.join('%s:%s' % (x.name, x.type_id) for x in ni.output_pins)
    return 'IN [%s] OUT [%s]' % (ins, outs)


def main():
    from editor_toolset.toolsets import blueprint as BP
    from editor_toolset.toolsets.blueprint import _get_node_type_id
    BPT = BP.BlueprintTools
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.make_directory('/Game/KhoangLang/Data')
    for n in ('TMP35_Hud',):
        if unreal.load_asset('/Game/KhoangLang/Data/' + n):
            unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/' + n)

    hud = BPT.create('/Game/KhoangLang/Data', 'TMP35_Hud', unreal.HUD.static_class())
    BPT.compile_blueprint(hud)
    hg = unreal.BlueprintEditorLibrary.find_event_graph(hud)
    hed = unreal.BlueprintGraphEditor.get_graph_editor(hg)

    p('=== A. node database hits for draw/canvas/hud/tile ===')
    av = hed.list_available_nodes([])
    p('  total %d' % len(av))
    for kw in ('draw', 'canvas', 'hud', 'tile', 'font', 'text'):
        hits = [str(x) for x in av if kw in str(x).lower()]
        p('  %-8s -> %s' % (kw, hits[:25]))

    p('')
    p('=== B. add_function_graph(hud, "DrawHUD") override attempt ===')
    try:
        fg = BPT.add_function_graph(hud, 'DrawHUD')
        BPT.compile_blueprint(hud)
        p('  graph: %s [%s]' % (fg.get_name(), fg.get_class().get_name()))
        hed2 = unreal.BlueprintGraphEditor.get_graph_editor(fg)
        for n in hed2.list_all_nodes():
            p('    node %s %r %s' % (n.get_class().get_name(),
                                      _get_node_type_id(n), pins(n)))
        n = hed2.add_call_function_node('/Script/Engine.HUD:DrawText')
        p('    DrawText: %s' % pins(n))
        p('  status %s' % hud.get_editor_property('status'))
        for g in BPT.list_graphs(hud):
            p('  graph %s -> %s' % (g.get_name(), g.get_class().get_name()))
        p('  dsl:')
        for ln in str(BPT.read_graph_dsl(fg)).splitlines():
            p('    | %s' % ln)
    except Exception:
        p(traceback.format_exc())

    p('')
    p('=== C. object pin literal, per docs ===')
    act = BPT.create('/Game/KhoangLang/Data', 'TMP35_Act', unreal.Actor.static_class())
    BPT.compile_blueprint(act)
    g = unreal.BlueprintEditorLibrary.find_event_graph(act)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    n = ed.add_call_function_node('/Script/Engine.AudioComponent:SetSound')
    ni = BPT.get_node_infos([n])[0]
    sp = next(x for x in ni.input_pins if x.name == 'NewSound')
    for c in ("/Game/KhoangLang/Audio/S_KL_RollCall.S_KL_RollCall",
              "/Game/KhoangLang/Audio/S_KL_RollCall",
              "SoundWave'/Game/KhoangLang/Audio/S_KL_RollCall.S_KL_RollCall'"):
        try:
            BPT.set_pin_value(sp.pin_id, c)
            p('  set %-58s -> %r' % (c, BPT.get_pin_value(sp.pin_id)))
        except Exception as exc:
            p('  set %-58s raised %r' % (c, exc))
    ed.remove_nodes([n])
    p('  --- class pin')
    n = ed.create_node_from_name('Actor|GetAllActorsOfClass', unreal.Vector2D(0, 0), [], None)
    ni = BPT.get_node_infos([n])[0]
    cp = next(x for x in ni.input_pins if x.name == 'ActorClass')
    for c in ("/Script/Engine.Actor", "Actor'/Script/Engine.Actor'",
              "Class'/Script/Engine.Actor'"):
        try:
            BPT.set_pin_value(cp.pin_id, c)
            p('  set %-40s -> %r' % (c, BPT.get_pin_value(cp.pin_id)))
        except Exception as exc:
            p('  set %-40s raised %r' % (c, exc))
    ed.remove_nodes([n])
    p('  --- trace channel / enum pins')
    n = ed.create_node_from_name('Collision|SphereTraceByChannel',
                                 unreal.Vector2D(0, 0), [], None)
    ni = BPT.get_node_infos([n])[0]
    for pn in ('TraceChannel', 'DrawDebugType'):
        pin = next(x for x in ni.input_pins if x.name == pn)
        for c in ('Visibility', 'ETraceTypeQuery::Visibility', '1',
                  'EDrawDebugTrace::None', 'None', '0'):
            try:
                BPT.set_pin_value(pin.pin_id, c)
                p('  %-16s set %-30s -> %r' % (pn, c, BPT.get_pin_value(pin.pin_id)))
            except Exception as exc:
                p('  %-16s set %-30s raised %r' % (pn, c, exc))
    ed.remove_nodes([n])
    p('  --- audio curve enum pin')
    n = ed.create_node_from_name('Audio|Components|Audio|FadeOut',
                                 unreal.Vector2D(0, 0), [], None)
    ni = BPT.get_node_infos([n])[0]
    pin = next(x for x in ni.input_pins if x.name == 'FadeCurve')
    for c in ('Linear', 'SCurve', 'Logarithmic', 'Exponential', '0'):
        try:
            BPT.set_pin_value(pin.pin_id, c)
            p('  FadeCurve set %-14s -> %r' % (c, BPT.get_pin_value(pin.pin_id)))
        except Exception as exc:
            p('  FadeCurve set %-14s raised %r' % (c, exc))
    ed.remove_nodes([n])
    p('  --- FKey struct pin')
    n = ed.add_call_function_node('/Script/Engine.PlayerController:WasInputKeyJustPressed')
    ni = BPT.get_node_infos([n])[0]
    kp = next(x for x in ni.input_pins if x.name == 'Key')
    for c in ('(KeyName="E")', 'E', '"E"'):
        try:
            BPT.set_pin_value(kp.pin_id, c)
            p('  FKey set %-16s -> %r' % (c, BPT.get_pin_value(kp.pin_id)))
        except Exception as exc:
            p('  FKey set %-16s raised %r' % (c, exc))
    ed.remove_nodes([n])
    p('  --- KeyStructure make node')
    for nid in ('Utilities|Struct|MakeKey', 'Key|Struct|Key', 'Utilities|InputKey|Key'):
        nn = ed.create_node_from_name(nid, unreal.Vector2D(0, 0), [], None)
        p('  %-34s -> %s' % (nid, nn))
        if nn is not None:
            p('     %s' % pins(nn))
            ed.remove_nodes([nn])

    p('')
    p('=== D. cleanup ===')
    for n in ('TMP35_Hud', 'TMP35_Act'):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/' + n)
    p('PROBE35_DONE')


try:
    rep = os.path.join(OUT_DIR, 'report.txt')
    if os.path.exists(rep):
        os.remove(rep)
    main()
except Exception:
    p(traceback.format_exc())
    p('PROBE35_DONE_FATAL')
