"""Discovery probe 30: real project state needed before building Milestone 1."""

import os
import sys
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
sys.path.insert(0, HERE)

OUT_DIR = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p30'
os.makedirs(OUT_DIR, exist_ok=True)


def p(msg):
    line = str(msg)
    unreal.log('KL30: ' + line)
    with open(os.path.join(OUT_DIR, 'report.txt'), 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


def dsl(bp, label):
    from editor_toolset.toolsets import blueprint as BP
    p('')
    p('=== %s ===' % label)
    if bp is None:
        p('  (asset missing)')
        return
    for g in BP.BlueprintTools.list_graphs(bp):
        try:
            txt = str(BP.BlueprintTools.read_graph_dsl(g))
        except Exception as exc:
            txt = 'ERR %r' % (exc,)
        p('--- graph %s' % g.get_name())
        for ln in txt.splitlines():
            p('  | %s' % ln)


def main():
    from editor_toolset.toolsets import blueprint as BP
    rows = []
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    res = []
    try:
        res = ar.get_assets_by_path(unreal.Name('/Game'), recursive=True,
                                    include_only_on_disk_assets=False)
    except Exception as exc:
        p('registry raised %r' % (exc,))
    p('registry /Game -> %d entries' % len(res))
    for entry in res:
        sp = str(entry.get_object_path()) if hasattr(entry, 'get_object_path') \
            else str(entry)
        sp = sp.split('.')[0]
        a = unreal.load_asset(sp)
        if a is None:
            continue
        rows.append('%s   [%s]' % (sp, a.get_class().get_name()))
    if not rows:
        for sp in unreal.EditorAssetLibrary.list_assets('/Game', True, False):
            sp = str(sp)
            a = unreal.load_asset(sp)
            if a is not None:
                rows.append('%s   [%s]' % (sp, a.get_class().get_name()))

    p('')
    p('=== A. /Game assets (%d) ===' % len(rows))
    for r in sorted(rows):
        p('  ' + r)

    p('')
    p('--- directory probe ---')
    for d in ('/Game/Input', '/Game/KhoangLang', '/Game/KhoangLang/Input',
              '/Game/FirstPerson/Input'):
        p('  does_directory_exist %s = %s' % (
            d, unreal.EditorAssetLibrary.does_directory_exist(d)))
    for a in ('/Game/Input/IMC_Default', '/Game/Input/IMC_MouseLook',
              '/Game/Input/IA_Move', '/Game/Input/IA_Look', '/Game/Input/IA_Jump',
              '/Game/Input/IA_Shoot', '/Game/KhoangLang/Input/TMP15_IA_Test',
              '/Game/KhoangLang/Data/TMP14_Caller', '/Game/KhoangLang/Audio/S_KL_RollCall'):
        p('  does_asset_exist %s = %s' % (a, unreal.EditorAssetLibrary.does_asset_exist(a)))

    p('')
    p('=== C. enhanced input assets ===')
    for r in sorted(rows):
        sp = r.split('   ')[0]
        a = unreal.load_asset(sp)
        cn = a.get_class().get_name()
        if 'InputAction' in cn or 'MappingContext' in cn:
            p('  %s [%s]' % (sp, cn))
            try:
                p('    mappings: %s' % (a.get_editor_property('mappings'),))
            except Exception as exc:
                p('    mappings err %r' % (exc,))
            try:
                p('    value: %s' % (a.get_editor_property('value'),))
            except Exception as exc:
                p('    value err %r' % (exc,))

    dsl(unreal.load_asset('/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode'),
        'B3 BP_FirstPersonGameMode')
    p('')
    p('=== template PC cdo props ===')
    pc = unreal.load_class(None, '/Game/FirstPerson/Blueprints/'
                              'BP_FirstPersonPlayerController.BP_FirstPersonPlayerController_C')
    cdo = unreal.get_default_object(pc)
    for prop in ('bShowMouseCursor', 'bEnableClickEvents', 'bEnableMouseOverEvents',
                 'bEnableTouchEvents', 'bEnableTouchOverEvents'):
        try:
            p('  %s = %r' % (prop, cdo.get_editor_property(prop)))
        except Exception as exc:
            p('  %s err %r' % (prop, exc))

    p('')
    p('=== D. current level ===')
    p('  world=%s' % (unreal.EditorLevelLibrary.get_editor_world().get_name(),))
    p('PROBE30_DONE')


try:
    rep = os.path.join(OUT_DIR, 'report.txt')
    if os.path.exists(rep):
        os.remove(rep)
    main()
except Exception:
    p(traceback.format_exc())
    p('PROBE30_DONE_FATAL')
