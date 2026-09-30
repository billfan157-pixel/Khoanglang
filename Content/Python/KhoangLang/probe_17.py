"""Discovery probe 17: the exact Enhanced Input event node type id."""

import os
import sys
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
sys.path.insert(0, HERE)

OUT_DIR = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p17'
os.makedirs(OUT_DIR, exist_ok=True)
REPORT = []


def p(msg):
    line = str(msg)
    REPORT.append(line)
    unreal.log('KL17: ' + line)
    with open(os.path.join(OUT_DIR, 'report.txt'), 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


def main():
    from editor_toolset.toolsets import blueprint as BP
    from editor_toolset.toolsets.blueprint import _get_node_type_id
    BPT = BP.BlueprintTools
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    at = unreal.AssetToolsHelpers.get_asset_tools()
    eas.make_directory('/Game/KhoangLang/Input')
    eas.make_directory('/Game/KhoangLang/Data')

    p('=== A. template character EVENT GRAPH node ids ===')
    tpl = unreal.load_asset('/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter')
    eg = unreal.BlueprintEditorLibrary.find_event_graph(tpl)
    p('  event graph: %s' % (eg.get_name() if eg else None))
    ed = unreal.BlueprintGraphEditor.get_graph_editor(eg)
    for n in ed.list_all_nodes():
        p('   %-40s type_id=%-46r title=%r' % (n.get_class().get_name(),
                                               _get_node_type_id(n), n.get_node_title()))
        for prop in ('input_action',):
            try:
                p('        %s = %s' % (prop, n.get_editor_property(prop)))
            except Exception as exc:
                p('        %s unreadable (%s)' % (prop, str(exc)[:60]))

    p('')
    p('=== B. what does the action database offer in that graph? ===')
    for pat in ('EnhancedInputAction', 'InputAction', 'enhancedinput'):
        hits = BPT.find_node_types(eg, pat)
        p('  %-20s %d hits: %s' % (pat, len(hits), hits[:12]))

    p('')
    p('=== C. create a fresh action and hunt for its event id ===')
    for n in ('IA_ZZ', 'TMP17_IA_ZZ'):
        if unreal.load_asset('/Game/KhoangLang/Input/' + n):
            unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Input/' + n)
    ia = at.create_asset('IA_ZZ', '/Game/KhoangLang/Input', unreal.InputAction,
                         unreal.InputAction_Factory())
    ia.set_editor_property('value_type', unreal.InputActionValueType.BOOLEAN)
    eas.save_asset('/Game/KhoangLang/Input/IA_ZZ', only_if_is_dirty=False)
    p('  action: %s' % ia)

    if unreal.load_asset('/Game/KhoangLang/Data/TMP17_Char'):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP17_Char')
    child = BPT.create('/Game/KhoangLang/Data', 'TMP17_Char', unreal.load_class(
        None, '/Game/FirstPerson/Blueprints/'
              'BP_FirstPersonCharacter.BP_FirstPersonCharacter_C'))
    ceg = unreal.BlueprintEditorLibrary.find_event_graph(child)
    p('  child event graph: %s' % (ceg.get_name() if ceg else None))

    for pat in ('EnhancedInputAction', 'IA_ZZ'):
        hits = BPT.find_node_types(ceg, pat)
        p('  find %-20s -> %s' % (pat, hits[:12]))

    ced = unreal.BlueprintGraphEditor.get_graph_editor(ceg)
    for cand in ('EnhancedInputActionIA_ZZ', 'EnhancedInputActionIA ZZ',
                 'EnhancedInputAction|IA_ZZ'):
        try:
            n = ced.create_node_from_name(cand, unreal.Vector2D(100, 100), [], None)
            if n is None:
                p('  create_node_from_name(%r) -> None' % cand)
            else:
                p('  create_node_from_name(%r) -> %s type_id=%r'
                  % (cand, n.get_class().get_name(), _get_node_type_id(n)))
                try:
                    n.set_editor_property('input_action', ia)
                    p('     bound action = %s' % n.get_editor_property('input_action'))
                except Exception as exc:
                    p('     bind failed %r' % (exc,))
        except Exception as exc:
            p('  create_node_from_name(%r) raised %r' % (cand, exc))

    p('')
    p('=== D. duplicate an existing template input event node? ===')
    for nm in ('duplicate_node', 'duplicate_nodes'):
        p('  BlueprintGraphEditor.%s = %s' % (nm, hasattr(ed, nm)))
    p('  BlueprintEditorLibrary members: %s'
      % [x for x in dir(unreal.BlueprintEditorLibrary) if not x.startswith('_')])
    p('  EditorValidatorSubsystem members: %s'
      % [x for x in dir(unreal.get_editor_subsystem(unreal.EditorValidatorSubsystem))
         if not x.startswith('_')][:40])

    p('')
    p('=== E. status after compile ===')
    BPT.compile_blueprint(child)
    p('  child status: %s' % child.get_editor_property('status'))
    BPT.compile_blueprint(tpl)
    p('  template status: %s' % tpl.get_editor_property('status'))

    p('')
    p('=== cleanup ===')
    unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP17_Char')
    unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Input/IA_ZZ')
    p('PROBE17_DONE')


try:
    rep = os.path.join(OUT_DIR, 'report.txt')
    if os.path.exists(rep):
        os.remove(rep)
    main()
except Exception:
    p(traceback.format_exc())
    p('PROBE17_FAILED')
