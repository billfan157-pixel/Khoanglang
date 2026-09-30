"""Discovery probe 33: HUD events, macro nodes, object-pin literals, fn graphs."""

import os
import sys
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
sys.path.insert(0, HERE)

OUT_DIR = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p33'
os.makedirs(OUT_DIR, exist_ok=True)


def p(msg):
    line = str(msg)
    unreal.log('KL33: ' + line)
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
    BPT = BP.BlueprintTools
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.make_directory('/Game/KhoangLang/Data')
    for n in ('TMP33_Actor', 'TMP33_Hud', 'TMP33_Comp'):
        if unreal.load_asset('/Game/KhoangLang/Data/' + n):
            unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/' + n)

    p('=== A. HUD event graph events ===')
    hud = BPT.create('/Game/KhoangLang/Data', 'TMP33_Hud', unreal.HUD.static_class())
    BPT.compile_blueprint(hud)
    hg = unreal.BlueprintEditorLibrary.find_event_graph(hud)
    hed = unreal.BlueprintGraphEditor.get_graph_editor(hg)
    for n in hed.list_all_nodes():
        p('  node %s' % n.get_class().get_name())
        for prop in ('member_name', 'custom_function_name', 'custom_function_class',
                     'event_name', 'b_override_function'):
            try:
                p('     %s = %r' % (prop, n.get_editor_property(prop)))
            except Exception as exc:
                p('     %s err %r' % (prop, exc))
        p('     %s' % pins(n))
    p('  dsl:')
    for ln in str(BPT.read_graph_dsl(hg)).splitlines():
        p('    | %s' % ln)
    p('  graphs: %s' % [g.get_name() for g in BPT.list_graphs(hud)])

    p('')
    p('=== B. add_macro_node signature ===')
    import inspect
    p('  doc: %r' % (hed.add_macro_node.__doc__,))
    for args in (('ForEachLoop',), ('ForLoop',), ('DoOnce',)):
        try:
            n = hed.add_macro_node(*args)
            p('  %s -> %s' % (args, n))
            if n is not None:
                p('    %s' % pins(n))
                hed.remove_nodes([n])
        except Exception as exc:
            p('  %s raised %r' % (args, exc))

    p('')
    p('=== C. object pin literal formats ===')
    act = BPT.create('/Game/KhoangLang/Data', 'TMP33_Actor', unreal.Actor.static_class())
    BPT.add_variable(act, 'EvDef', unreal.DataAsset.static_class())
    BPT.add_variable(act, 'Snds', unreal.SoundWave.static_class(), None,
                     __import__('editor_toolset.toolsets.blueprint', fromlist=['x']).ContainerType.ARRAY)
    BPT.add_variable(act, 'Mesh', unreal.StaticMeshComponent.static_class())
    BPT.compile_blueprint(act)
    g = unreal.BlueprintEditorLibrary.find_event_graph(act)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    n = ed.add_call_function_node('/Script/Engine.AudioComponent:SetSound')
    ni = BPT.get_node_infos([n])[0]
    sp = next(x for x in ni.input_pins if x.name == 'NewSound')
    cands = [
        "SoundWave'/Game/KhoangLang/Audio/S_KL_RollCall.S_KL_RollCall'",
        "SoundWave'/Game/KhoangLang/Audio/S_KL_RollCall'",
        "/Game/KhoangLang/Audio/S_KL_RollCall.S_KL_RollCall",
        "/Game/KhoangLang/Audio/S_KL_RollCall",
        "Class'/Script/Engine.SoundWave'",
        "unreal.SoundWave'/Game/KhoangLang/Audio/S_KL_RollCall'",
    ]
    for c in cands:
        try:
            BPT.set_pin_value(sp.pin_id, c)
            p('  set %-58s -> %r' % (c, BPT.get_pin_value(sp.pin_id)))
        except Exception as exc:
            p('  set %-58s raised %r' % (c, exc))
    ed.remove_nodes([n])

    p('')
    p('=== D. Class-pin literal (for GetAllActorsOfClass) ===')
    n = ed.create_node_from_name('Actor|GetAllActorsOfClass', unreal.Vector2D(0, 0), [], None)
    ni = BPT.get_node_infos([n])[0]
    p('  pins: %s' % [(x.name, x.type_id) for x in ni.input_pins])
    cp = next(x for x in ni.input_pins if x.name == 'ActorClass')
    for c in ("Class'/Script/Engine.Actor'",
              "Actor'/Script/Engine.Actor'",
              "Class'/Game/KhoangLang/Data/TMP33_Actor.TMP33_Actor_C'",
              "'/Script/Engine.Actor'"):
        try:
            BPT.set_pin_value(cp.pin_id, c)
            p('  set %-52s -> %r' % (c, BPT.get_pin_value(cp.pin_id)))
        except Exception as exc:
            p('  set %-52s raised %r' % (c, exc))
    ed.remove_nodes([n])

    p('')
    p('=== E. function graph + return + params ===')
    fg = BPT.add_function_graph(act, 'KL_TryFmt')
    for nm, ty in (('In', 'string'), ('Out', 'string')):
        BPT.add_function_param(fg, nm, ty, nm == 'In')
    settry = ed.add_set_member_variable_node(unreal.Name('Snds'))
    ret = ed.add_return_node()
    p('  setter %s' % pins(settry))
    p('  return %s' % pins(ret))
    infos = BPT.get_node_infos([settry, ret])
    pinfo = BPT.get_node_infos([settry])[0]
    npin = next(x for x in pinfo.input_pins if x.name == 'NewItem')
    objvar = ed.add_get_member_variable_node(unreal.Name('Mesh'))
    p('  getobj %s' % pins(objvar))
    BPT.connect_pins(objvar_pin_id(objvar), npin.pin_id)
    rinfo = BPT.get_node_infos([ret])[0]
    p('  return pin: %s' % [(x.name, x.type_id) for x in rinfo.input_pins])
    BPT.connect_pins(BPT.get_node_infos([settry])[0].output_pins[0].pin_id,
                     rinfo.input_pins[0].pin_id)
    BPT.compile_blueprint(act)
    p('  status %s' % act.get_editor_property('status'))
    p('  dsl:')
    for ln in str(BPT.read_graph_dsl(fg)).splitlines():
        p('    | %s' % ln)

    p('')
    p('=== F. cleanup ===')
    unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP33_Actor')
    unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP33_Hud')
    p('PROBE33_DONE')


def objvar_pin_id(node):
    from editor_toolset.toolsets import blueprint as BP
    ni = BP.BlueprintTools.get_node_infos([node])[0]
    for x in ni.output_pins:
        if x.type_id != 'Exec':
            return x.pin_id
    raise RuntimeError('no output')


try:
    rep = os.path.join(OUT_DIR, 'report.txt')
    if os.path.exists(rep):
        os.remove(rep)
    main()
except Exception:
    p(traceback.format_exc())
    p('PROBE33_DONE_FATAL')
