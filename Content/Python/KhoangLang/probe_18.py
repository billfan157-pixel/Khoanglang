"""Discovery probe 18: how to obtain more Enhanced Input event nodes.

A. BlueprintGraphEditor API surface (node creation / duplication / raw classes).
B. The real property names on K2Node_EnhancedInputAction (template node).
C. Can the DSL create legacy InputKey / InputAction event nodes?
D. Does rebinding a template event node to a fresh action compile?
"""

import os
import sys
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
sys.path.insert(0, HERE)

OUT_DIR = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p18'
os.makedirs(OUT_DIR, exist_ok=True)
REPORT = []


def p(msg):
    line = str(msg)
    REPORT.append(line)
    unreal.log('KL18: ' + line)
    with open(os.path.join(OUT_DIR, 'report.txt'), 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


def attempt(label, fn):
    try:
        r = fn()
        p('  PASS %s %s' % (label, '' if r is None else r))
        return True
    except Exception as exc:
        p('  FAIL %s -> %s' % (label, str(exc)[:400]))
        return False


def main():
    from editor_toolset.toolsets import blueprint as BP
    from editor_toolset.toolsets.blueprint import _get_node_type_id
    BPT = BP.BlueprintTools
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    at = unreal.AssetToolsHelpers.get_asset_tools()
    eas.make_directory('/Game/KhoangLang/Input')
    eas.make_directory('/Game/KhoangLang/Data')

    p('=== A. BlueprintGraphEditor API ===')
    p('  %s' % sorted(x for x in dir(unreal.BlueprintGraphEditor) if not x.startswith('_')))

    p('')
    p('=== B. K2Node_EnhancedInputAction property names (template node) ===')
    tpl = unreal.load_asset('/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter')
    eg = unreal.BlueprintEditorLibrary.find_event_graph(tpl)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(eg)
    target = None
    for n in ed.list_all_nodes():
        if n.get_class().get_name() == 'K2Node_EnhancedInputAction':
            p('  node: %s' % _get_node_type_id(n))
            try:
                p('   dir: %s' % sorted(x for x in dir(n) if not x.startswith('_')))
            except Exception as exc:
                p('   dir failed %r' % (exc,))
            for prop in ('InputAction', 'input_action', 'Action', 'EnhancedInputAction'):
                try:
                    p('   %s = %s' % (prop, n.get_editor_property(prop)))
                except Exception as exc:
                    p('   %s -> %r' % (prop, str(exc)[:90]))
            if target is None:
                target = n

    p('')
    p('=== C. DSL: legacy InputKey / InputAction events ===')
    if unreal.load_asset('/Game/KhoangLang/Data/TMP18_Char'):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP18_Char')
    child = BPT.create('/Game/KhoangLang/Data', 'TMP18_Char', unreal.load_class(
        None, '/Game/FirstPerson/Blueprints/'
              'BP_FirstPersonCharacter.BP_FirstPersonCharacter_C'))
    ceg = unreal.BlueprintEditorLibrary.find_event_graph(child)
    ced = unreal.BlueprintGraphEditor.get_graph_editor(ceg)
    BPT.add_variable(child, 'Hits', 'int')

    for ev_name, params in (('InputKey', '(Key)'),
                            ('InputAction', '(ActionName)'),
                            ('InputAxis', '(AxisName)')):
        code = ('(event %s %s\n'
                '  (Variables|Default|SetHits 1))' % (ev_name, params))
        g2 = BPT.add_function_graph(child, 'Tmp%s' % ev_name)
        attempt('dsl event %s' % ev_name,
                lambda code=code: BPT.write_graph_dsl(g2, code))
        for n in ced.list_all_nodes():
            p('     -> %s / %r' % (n.get_class().get_name(), _get_node_type_id(n)))

    p('')
    p('=== C2. add_event with those names ===')
    for ev_name in ('InputKey', 'InputAction', 'InputAxis'):
        def go(ev_name=ev_name):
            n = BPT.add_event(child, ev_name)
            return '%s / %r' % (n.get_class().get_name(), _get_node_type_id(n))
        attempt('add_event %s' % ev_name, go)

    p('')
    p('=== D. rebind a template event node ===')
    if unreal.load_asset('/Game/KhoangLang/Input/IA_KL_Test'):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Input/IA_KL_Test')
    ia = at.create_asset('IA_KL_Test', '/Game/KhoangLang/Input', unreal.InputAction,
                         unreal.InputAction_Factory())
    ia.set_editor_property('value_type', unreal.InputActionValueType.BOOLEAN)
    eas.save_asset('/Game/KhoangLang/Input/IA_KL_Test', only_if_is_dirty=False)

    jump_node = None
    for n in ed.list_all_nodes():
        if n.get_class().get_name() == 'K2Node_EnhancedInputAction' and 'Jump' in \
                _get_node_type_id(n):
            jump_node = n
    p('  jump node: %s' % (_get_node_type_id(jump_node) if jump_node else None))

    def rebind():
        for prop in ('InputAction', 'input_action'):
            try:
                jump_node.set_editor_property(prop, ia)
                p('    bound via %s -> %s' % (prop, jump_node.get_editor_property(prop)))
                return True
            except Exception as exc:
                p('    %s failed: %s' % (prop, str(exc)[:110]))
        return False
    attempt('rebind template jump node', rebind)
    attempt('compile template', lambda: BPT.compile_blueprint(tpl))
    p('  template status: %s' % tpl.get_editor_property('status'))
    p('  jump node type_id after: %s' % _get_node_type_id(jump_node))

    p('')
    p('=== E. can a child Blueprint add its own input event node? ===')
    p('  child nodes:')
    for n in ced.list_all_nodes():
        p('   %-40s %r' % (n.get_class().get_name(), _get_node_type_id(n)))

    p('')
    p('=== cleanup ===')
    unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP18_Char')
    unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Input/IA_KL_Test')
    p('PROBE18_DONE')


try:
    rep = os.path.join(OUT_DIR, 'report.txt')
    if os.path.exists(rep):
        os.remove(rep)
    main()
except Exception:
    p(traceback.format_exc())
    p('PROBE18_FAILED')
