"""Discovery probe 16: real Enhanced Input event nodes + template repair.

Answers:
  A. What node classes actually live in the template character's EventGraph?
  B. Can `create_node` produce a real K2Node_EnhancedInputActionEvent, and can it
     be wired to a function call with the toolset API?
  C. Is there a Python API that reports Blueprint compile status?
"""

import os
import sys
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
sys.path.insert(0, HERE)

OUT_DIR = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p16'
os.makedirs(OUT_DIR, exist_ok=True)
REPORT = []


def p(msg):
    line = str(msg)
    REPORT.append(line)
    unreal.log('KL16: ' + line)
    with open(os.path.join(OUT_DIR, 'report.txt'), 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


def attempt(label, fn):
    try:
        fn()
        p('  PASS %s' % label)
        return True
    except Exception as exc:
        p('  FAIL %s -> %s' % (label, str(exc)[:500]))
        return False


def pin_summary(node):
    ni = unreal.BlueprintTools.get_node_infos([node])[0] if hasattr(
        unreal, 'BlueprintTools') else None
    return ni


def main():
    from editor_toolset.toolsets import blueprint as BP
    BPT = BP.BlueprintTools
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    at = unreal.AssetToolsHelpers.get_asset_tools()
    eas.make_directory('/Game/KhoangLang/Input')
    eas.make_directory('/Game/KhoangLang/Data')

    # ------------------------------------------------------------------ A
    p('=== A. every node in the template character EventGraph ===')
    tpl = unreal.load_asset('/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter')
    tg = BPT.list_graphs(tpl)[0]
    editor = unreal.BlueprintGraphEditor.get_graph_editor(tg)
    nodes = list(editor.list_all_nodes())
    p('  %d nodes' % len(nodes))
    for n in nodes:
        props = []
        for prop in ('input_action', 'input_action_name'):
            try:
                props.append('%s=%s' % (prop, n.get_editor_property(prop)))
            except Exception:
                pass
        p('   %-42s title=%-38r %s'
          % (n.get_class().get_name(), n.get_node_title(), ' '.join(props)))

    # ------------------------------------------------------------------ B
    p('')
    p('=== B. create a real enhanced input action event ===')

    def mk_ia(name, vtype):
        path = '/Game/KhoangLang/Input/' + name
        a = unreal.load_asset(path)
        if a is None:
            a = at.create_asset(name, '/Game/KhoangLang/Input', unreal.InputAction,
                                unreal.InputAction_Factory())
        a.set_editor_property('value_type', vtype)
        eas.save_asset(path, only_if_is_dirty=False)
        return a

    ia_press = mk_ia('TMP16_IA_Press', unreal.InputActionValueType.BOOLEAN)
    if unreal.load_asset('/Game/KhoangLang/Data/TMP16_Char'):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP16_Char')
    if unreal.load_asset('/Game/KhoangLang/Input/TMP16_IMC'):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Input/TMP16_IMC')

    child = BPT.create('/Game/KhoangLang/Data', 'TMP16_Char', unreal.load_class(
        None, '/Game/FirstPerson/Blueprints/'
              'BP_FirstPersonCharacter.BP_FirstPersonCharacter_C'))
    g = BPT.list_graphs(child)[0]
    BPT.add_variable(child, 'Hits', 'int')
    BPT.add_function_graph(child, 'OnPress')
    BPT.write_graph_dsl(BPT.get_graph(child, 'OnPress'),
                        '(fn OnPress ()\n  (Variables|Default|SetHits 1))')

    made = {}

    def create_event():
        node = BPT.create_node(g, 'EnhancedInputActionIA_Press', unreal.IntPoint(300, 0))
        made['node'] = node
        p('    created class=%s title=%r' % (node.get_class().get_name(),
                                             node.get_node_title()))
    if attempt('create enhanced input event node', create_event):
        node = made['node']
        attempt('set input_action', lambda: node.set_editor_property('input_action', ia_press))
        try:
            p('    input_action now = %s' % node.get_editor_property('input_action'))
        except Exception as exc:
            p('    input_action read failed %r' % (exc,))

        def wire():
            call = BPT.create_node(g, '|OnPress', unreal.IntPoint(700, 0))
            infos = BPT.get_node_infos([node, call])
            ev, cl = infos[0], infos[1]
            p('    event pins: in=%s out=%s' % ([x.name for x in ev.input_pins],
                                                [(x.name, x.type_id) for x in ev.output_pins]))
            p('    call   pins: in=%s out=%s' % ([x.name for x in cl.input_pins],
                                                [(x.name, x.type_id) for x in cl.output_pins]))
            ev_out = next(x for x in ev.output_pins if x.type_id == 'Exec')
            cl_in = next(x for x in cl.input_pins if x.type_id == 'Exec')
            BPT.connect_pins(ev_out.pin_id, cl_in.pin_id)
            p('    connected %s -> %s' % (ev_out.name, cl_in.name))
        attempt('wire event -> function', wire)
        attempt('compile child', lambda: BPT.compile_blueprint(child))

    p('')
    p('=== B2. same via a raw blueprint graph editor call ===')

    def raw():
        ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
        n2 = ed.create_node_from_name('EnhancedInputActionIA_Press',
                                      unreal.Vector2D(300, 400), [], None)
        p('    raw node: %s' % (n2.get_class().get_name() if n2 else None))
    attempt('raw create_node_from_name', raw)

    p('')
    p('=== C. compile status API hunt ===')
    for nm in ('BlueprintCompilationManager', 'KismetEditorUtilities', 'BlueprintEditorLibrary',
               'EditorValidatorSubsystem', 'BlueprintEditorSubsystem'):
        p('  unreal.%-32s %s' % (nm, hasattr(unreal, nm)))
    for nm in ('get_blueprint_asset', 'compile_blueprint', 'are_blueprints_compiled',
               'get_blueprint_status', 'refresh_open_editors', 'get_num_blueprints_in_list'):
        p('  BlueprintEditorLibrary.%-32s %s' % (nm, hasattr(unreal.BlueprintEditorLibrary, nm)))
    if hasattr(unreal, 'BlueprintCompilationManager'):
        p('  BlueprintCompilationManager: %s' % [x for x in dir(unreal.BlueprintCompilationManager)
                                                 if not x.startswith('_')])
    if hasattr(unreal, 'EditorValidatorSubsystem'):
        try:
            evs = unreal.get_editor_subsystem(unreal.EditorValidatorSubsystem)
            res = evs.validate_assets([child], True)
            for r in res:
                p('  validate %s: issues=%s' % (r.asset_name, r.issues))
        except Exception as exc:
            p('  validator failed %r' % (exc,))
    try:
        p('  bp status prop: %s' % child.get_editor_property('status'))
    except Exception as exc:
        p('  bp status unavailable: %r' % (str(exc)[:120],))

    p('')
    p('=== D. object function param ===')
    fg = BPT.add_function_graph(child, 'TakeThing')

    def objparam():
        BPT.add_object_function_param(fg, 'Who', unreal.Actor.static_class(), True)
        BPT.add_object_function_param(fg, 'Ref', unreal.DataAsset.static_class(), True)
        p('    object params added')
    attempt('add_object_function_param', objparam)
    attempt('write objparam graph', lambda: BPT.write_graph_dsl(
        fg, '(fn TakeThing (Who Ref)\n  (return))'))

    p('')
    p('=== E. IMC persisted mappings ===')
    imc = at.create_asset('TMP16_IMC', '/Game/KhoangLang/Input',
                          unreal.InputMappingContext, unreal.InputMappingContext_Factory())
    for keyname in ('E', 'Q', 'Tab', 'F', 'P', 'Enter', 'Escape'):
        k = unreal.Key()
        k.set_editor_property('key_name', keyname)
        imc.map_key(ia_press, k)
    eas.save_asset('/Game/KhoangLang/Input/TMP16_IMC', only_if_is_dirty=False)
    imc2 = unreal.load_asset('/Game/KhoangLang/Input/TMP16_IMC')
    dm = imc2.get_editor_property('default_key_mappings')
    p('  persisted: %s' % [(str(m.key), m.action.get_name()) for m in dm.mappings])

    p('')
    p('=== cleanup ===')
    for n in ('TMP16_Char',):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/' + n)
    for n in ('TMP16_IMC', 'TMP16_IA_Press'):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Input/' + n)
    p('PROBE16_DONE')


try:
    rep = os.path.join(OUT_DIR, 'report.txt')
    if os.path.exists(rep):
        os.remove(rep)
    main()
except Exception:
    p(traceback.format_exc())
    p('PROBE16_FAILED')
