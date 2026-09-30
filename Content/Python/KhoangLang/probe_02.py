"""Discovery probe: inspect the real FirstPerson template wiring before building.

Answers:
  1. Which Input Action / Input Mapping Context assets exist, and what do they map?
  2. What does BP_FirstPersonCharacter actually do (DSL dump)?
  3. Does a Blueprint with UPrimaryDataAsset as parent succeed?
  4. What engine content is available for meshes / fonts / materials?
"""

import os
import sys
import traceback

import unreal

sys.path.insert(0, r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang')

from editor_toolset.toolsets import blueprint as BP  # noqa: E402
import kl_kit as K  # noqa: E402

OUT = []


def p(msg):
    line = str(msg)
    OUT.append(line)
    unreal.log('KLPROBE: ' + line)
    try:
        with open(K.REPORT_PATH, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
            f.flush()
    except Exception:
        pass


def find_by_class(ar, class_name, pkg=None):
    """Version-proof: scan all /Game assets and match on class name."""
    out = []
    for a in ar.get_assets_by_path('/Game', recursive=True):
        if str(a.asset_class_path.asset_name) == class_name:
            out.append(a)
    return out


def guard(label, fn):
    try:
        fn()
    except Exception as exc:
        p('  !! %s FAILED: %r' % (label, exc))


def dump_imc(a):
    ctx = a.get_asset()
    maps = ctx.get_mappings()
    p('  %s : %d mappings' % (a.package_name, len(maps)))
    for m in maps:
        iam = m.action.get_asset()
        p('     key=%-28s action=%-22s type=%s' % (str(m.key), iam.get_name(), iam.value_type))


def dump_ia(a):
    iam = a.get_asset()
    p('  %-58s value_type=%s' % (a.package_name, iam.value_type))


def main():
    p('=== 1. /Game/FirstPerson assets ===')
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    assets = ar.get_assets_by_path('/Game/FirstPerson', recursive=True)
    for a in sorted(assets, key=lambda x: str(x.package_name)):
        p('  %-55s %s' % (str(a.package_name), a.asset_class_path.asset_name))

    p('')
    p('=== 2. Enhanced Input assets anywhere in /Game ===')
    try:
        ias = find_by_class(ar, 'InputAction')
        imcs = find_by_class(ar, 'InputMappingContext')
        for a in ias:
            p('  IA  %s' % a.package_name)
        for a in imcs:
            p('  IMC %s' % a.package_name)
        p('  counts: IA=%d IMC=%d' % (len(ias), len(imcs)))
    except Exception as exc:
        ias, imcs = [], []
        p('  !! scan failed: %r' % (exc,))

    p('')
    p('=== 2b. ALL non-map assets under /Game (class census) ===')
    census = {}
    for a in ar.get_assets_by_path('/Game', recursive=True):
        cn = str(a.asset_class_path.asset_name)
        census[cn] = census.get(cn, 0) + 1
    for k in sorted(census):
        p('  %-40s %d' % (k, census[k]))

    p('')
    p('=== 3. IMC contents (mappings) ===')
    for a in imcs:
        guard('IMC %s' % a.package_name, lambda a=a: dump_imc(a))

    p('')
    p('=== 4. IA contents ===')
    for a in ias:
        guard('IA %s' % a.package_name, lambda a=a: dump_ia(a))

    p('')
    p('=== 5. BP_FirstPersonCharacter DSL ===')
    for path in ('/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter',
                 '/Game/FirstPerson/Blueprints/BP_FirstPersonPlayerController',
                 '/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode'):
        bp = unreal.load_asset(path)
        if bp is None:
            p('  %s MISSING' % path)
            continue
        p('--- %s' % path)
        try:
            p('  parent = %s' % BP.BlueprintTools.get_parent(bp).get_name())
        except Exception as e:
            p('  parent err %r' % (e,))
        try:
            for g in BP.BlueprintTools.list_graphs(bp):
                try:
                    code = BP.BlueprintTools.read_graph_dsl(g)
                except Exception as e:
                    code = '<read err %r>' % (e,)
                p('  GRAPH %s:' % g.get_name())
                for ln in str(code).splitlines():
                    p('    ' + ln)
        except Exception as e:
            p('  graph err %r' % (e,))

    p('')
    p('=== 6. Test PrimaryDataAsset blueprint parent ===')
    for cls_name in ('PrimaryDataAsset', 'DataAsset', 'Object'):
        try:
            cls = getattr(unreal, cls_name)
        except Exception:
            p('  %s : no unreal attr' % cls_name)
            continue
        try:
            folder = '/Game/KhoangLang/Data'
            bp = BP.BlueprintTools.create(folder, 'TMP_Probe_' + cls_name, cls.static_class())
            p('  %s -> %r' % (cls_name, bp.get_name() if bp else None))
        except Exception as e:
            p('  %s -> EXC %r' % (cls_name, e))

    p('')
    p('=== 7. Engine assets available ===')
    checks = [
        '/Engine/BasicShapes/Cube', '/Engine/BasicShapes/Cylinder',
        '/Engine/BasicShapes/Plane', '/Engine/BasicShapes/Sphere',
        '/Engine/BasicShapes/Cone', '/Engine/BasicShapes/BasicShapeMaterial',
        '/Engine/EngineFonts/RobotoDistanceField', '/Engine/Functions/Blueprint_MathLibrary',
    ]
    for c in checks:
        p('  %-52s %s' % (c, 'OK' if unreal.load_asset(c) else 'MISSING'))

    p('')
    p('=== 8. Engine assets available ===')
    checks = [
        '/Engine/BasicShapes/Cube', '/Engine/BasicShapes/Cylinder',
        '/Engine/BasicShapes/Plane', '/Engine/BasicShapes/Sphere',
        '/Engine/BasicShapes/Cone', '/Engine/BasicShapes/BasicShapeMaterial',
        '/Engine/EngineFonts/RobotoDistanceField',
    ]
    for c in checks:
        p('  %-52s %s' % (c, 'OK' if unreal.load_asset(c) else 'MISSING'))

    p('')
    p('=== 9. Maps present ===')
    p('  Lvl_FirstPerson exists: %s' % (unreal.load_asset('/Game/FirstPerson/Lvl_FirstPerson') is not None))
    p('  Lvl_KL_School3 exists : %s' % (unreal.load_asset('/Game/KhoangLang/Maps/Lvl_KL_School3') is not None))

    p('')
    p('=== 10. Material instances sanity ===')
    for m in ('M_KL_Wall', 'M_KL_Floor', 'M_KL_Paper'):
        p('  %s : %s' % (m, 'OK' if unreal.load_asset('/Game/KhoangLang/Materials/' + m) else 'MISSING'))

    p('')
    p('=== 11. Sound waves sanity ===')
    for s in ('S_KL_T2_Masked', 'S_KL_T2_Clear', 'S_KL_NoiseMask', 'S_KL_ClarityTone',
              'S_KL_RollCall', 'S_KL_ChildReply', 'S_KL_Ambience_Hall', 'S_KL_TapeDeck',
              'S_KL_SpeakerHum', 'S_KL_UI_Interact', 'S_KL_UI_Evidence', 'S_KL_UI_ModeShift'):
        a = unreal.load_asset('/Game/KhoangLang/Audio/' + s)
        if a is None:
            p('  %-22s MISSING' % s)
        else:
            d = a.get_editor_property('duration')
            p('  %-22s dur=%.2fs' % (s, d))

    p('PROBE_DONE')
    return True


try:
    if os.path.exists(K.REPORT_PATH):
        os.remove(K.REPORT_PATH)
    main()
except Exception:
    p(traceback.format_exc())
    p('PROBE_FAILED')
