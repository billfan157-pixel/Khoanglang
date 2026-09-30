"""Discovery probe 34: API docstrings, node database search, HUD draw event."""

import os
import sys
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
sys.path.insert(0, HERE)

OUT_DIR = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p34'
os.makedirs(OUT_DIR, exist_ok=True)


def p(msg):
    line = str(msg)
    unreal.log('KL34: ' + line)
    with open(os.path.join(OUT_DIR, 'report.txt'), 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


DOCS = [
    'create', 'set_parent', 'add_variable', 'add_object_variable',
    'add_function_graph', 'add_function_param', 'write_graph_dsl',
    'compile_blueprint', 'set_variable_instance_editable', 'get_default_object',
    'list_graphs', 'get_node_infos', 'connect_pins', 'set_pin_value',
    'get_pin_value', 'find_node_types', 'add_variable_instance_editable',
    'add_input_variable', 'add_output_variable', 'set_default_value',
    'add_local_variable', 'create_and_edit_function_graph',
]


def main():
    from editor_toolset.toolsets import blueprint as BP
    from editor_toolset.toolsets import actor as ACT
    BPT = BP.BlueprintTools
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.make_directory('/Game/KhoangLang/Data')
    for n in ('TMP34_Act', 'TMP34_Hud'):
        if unreal.load_asset('/Game/KhoangLang/Data/' + n):
            unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/' + n)

    p('=== A. BlueprintTools docstrings ===')
    for d in DOCS:
        fn = getattr(BPT, d, None)
        if fn is None:
            p('  %s : ABSENT' % d)
            continue
        p('  --- %s' % d)
        for ln in str(fn.__doc__).splitlines():
            p('      %s' % ln.strip())
    p('  --- ContainerType: %s' % [e for e in dir(BP.ContainerType) if not e.startswith('_')])
    p('  --- ActorTools docstrings')
    for d in ('add_component', 'get_components', 'set_label', 'add_tag',
              'get_actor_property', 'set_actor_property'):
        fn = getattr(ACT.ActorTools, d, None)
        p('  --- %s -> %s' % (d, (str(fn.__doc__).splitlines()[0] if fn else 'ABSENT')))
    p('  --- ActorTools members: %s' % [m for m in dir(ACT.ActorTools)
                                        if not m.startswith('_')])

    p('')
    p('=== B. node database search: draw / hud / canvas ===')
    hud = BPT.create('/Game/KhoangLang/Data', 'TMP34_Hud', unreal.HUD.static_class())
    BPT.compile_blueprint(hud)
    hg = unreal.BlueprintEditorLibrary.find_event_graph(hud)
    hed = unreal.BlueprintGraphEditor.get_graph_editor(hg)
    av = hed.list_available_nodes()
    p('  list_available_nodes -> %d' % len(av))
    hits = []
    for s in av:
        s = str(s)
        low = s.lower()
        if 'draw' in low or 'canvas' in low or 'hud' in low:
            hits.append(s)
    p('  hits: %s' % hits[:60])
    p('  sample of all: %s' % [str(x) for x in av[:40]])

    p('')
    p('=== C. add_dispatcher_event_node candidates ===')
    for nm in ('DrawHUD', 'ReceiveDrawHUD', 'EventDrawHUD', 'PostRender',
               'DrawTile', 'OnDrawCanvas'):
        try:
            n = hed.add_dispatcher_event_node(nm)
            p('  %-18s -> %s' % (nm, n))
            if n is not None:
                from editor_toolset.toolsets.blueprint import _get_node_type_id
                ni = BPT.get_node_infos([n])[0]
                p('     id=%r' % _get_node_type_id(n))
                p('     IN [%s]' % ', '.join('%s:%s' % (x.name, x.type_id)
                                             for x in ni.input_pins))
                p('     OUT [%s]' % ', '.join('%s:%s' % (x.name, x.type_id)
                                              for x in ni.output_pins))
                hed.remove_nodes([n])
        except Exception as exc:
            p('  %-18s raised %r' % (nm, exc))

    p('')
    p('=== D. call_method / find_event_node ===')
    for m in ('list_component_events',):
        try:
            p('  %s -> %s' % (m, [str(x) for x in getattr(hed, m)()]))
        except Exception as exc:
            p('  %s raised %r' % (m, exc))
    p('  call_method doc: %r' % (hed.call_method.__doc__,))
    p('  find_event_node doc: %r' % (hed.find_event_node.__doc__,))

    p('')
    p('=== E. end to end: actor + component bp + object var + function ===')
    try:
        from editor_toolset.toolsets.blueprint import ContainerType
        cbp = BPT.create('/Game/KhoangLang/Data', 'TMP34_Comp', unreal.ActorComponent.static_class())
        BPT.add_variable(cbp, 'Prompt', 'text')
        BPT.add_variable(cbp, 'bConsumed', 'bool')
        BPT.add_object_variable(cbp, 'Def', unreal.DataAsset.static_class())
        BPT.add_object_variable(cbp, 'Sfx', unreal.SoundWave.static_class())
        BPT.add_object_variable(cbp, 'Mesh', unreal.StaticMeshComponent.static_class())
        BPT.add_object_variable(cbp, 'Reveal', unreal.StaticMeshComponent.static_class())
        BPT.set_variable_instance_editable(cbp, 'Prompt', True)
        BPT.set_variable_instance_editable(cbp, 'Sfx', True)
        BPT.compile_blueprint(cbp)
        p('  comp status %s' % cbp.get_editor_property('status'))
        for gg in BPT.list_graphs(cbp):
            p('   graph %s' % gg.get_name())

        act = BPT.create('/Game/KhoangLang/Data', 'TMP34_Act', unreal.Actor.static_class())
        comp = ACT.ActorTools.add_component(act, cbp.get_class(), 'KL_Interact')
        p('  added comp: %s' % comp)
        BPT.compile_blueprint(act)
        p('  act status %s' % act.get_editor_property('status'))
        cdo = BPT.get_default_object(act)
        sw = unreal.load_asset('/Game/KhoangLang/Audio/S_KL_RollCall')
        for c in ACT.ActorTools.get_components(cdo):
            p('   comp %s [%s]' % (c.get_name(), c.get_class().get_name()))
            if c.get_class().get_name() == 'KL_InteractComp_C':
                c.set_editor_property('Sfx', sw)
                c.set_editor_property('Prompt', unreal.Text('Xem'))
                p('     set Sfx -> %r' % (c.get_editor_property('Sfx'),))
                p('     set Prompt -> %r' % (c.get_editor_property('Prompt'),))
        p('  cdo read back: %s' % [
            c.get_editor_property('Prompt') for c in ACT.ActorTools.get_components(cdo)
            if c.get_class().get_name() == 'KL_InteractComp_C'])
    except Exception:
        p(traceback.format_exc())

    p('')
    p('=== F. cleanup ===')
    for n in ('TMP34_Act', 'TMP34_Hud', 'TMP34_Comp'):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/' + n)
    p('PROBE34_DONE')


try:
    rep = os.path.join(OUT_DIR, 'report.txt')
    if os.path.exists(rep):
        os.remove(rep)
    main()
except Exception:
    p(traceback.format_exc())
    p('PROBE34_DONE_FATAL')
