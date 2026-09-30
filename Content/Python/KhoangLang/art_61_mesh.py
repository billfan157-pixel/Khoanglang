"""Art pass probe 61: exact factory + StaticMeshDescription authoring API."""

import os
import traceback

import unreal

OUT = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\art61'
os.makedirs(OUT, exist_ok=True)
L = []


def p(m=''):
    L.append(str(m))
    unreal.log('A61: ' + str(m))


def main():
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.make_directory('/Game/KhoangLang/ArtTest')
    at = unreal.AssetToolsHelpers.get_asset_tools()

    p('=== A. StaticMesh factory symbols ===')
    p('  %s' % [n for n in dir(unreal) if 'StaticMesh' in n and 'Factory' in n])
    p('  all *Factory* count=%d' % len([n for n in dir(unreal) if n.endswith('Factory')]))
    fac = None
    for name in ('StaticMeshFactoryNew', 'StaticMeshFactory', 'MeshFactory'):
        if hasattr(unreal, name):
            p('  using unreal.%s' % name)
            fac = getattr(unreal, name)()
            break
    if fac is None:
        p('  no factory symbol; try create_asset without factory')
        p('  %s' % [n for n in dir(unreal) if n.endswith('Factory') and 'Mesh' in n])
        p('DONE')
        return
    p('  factory members: %s' % [m for m in dir(fac) if not m.startswith('_')])

    mpath = '/Game/KhoangLang/ArtTest/A61_SM'
    if unreal.load_asset(mpath):
        unreal.EditorAssetLibrary.delete_asset(mpath)
    sm = at.create_asset('A61_SM', '/Game/KhoangLang/ArtTest', unreal.StaticMesh, fac)
    p('  created: %s' % (sm.get_name() if sm else None))

    p('')
    p('=== B. StaticMeshDescription members ===')
    SMD = unreal.StaticMeshDescription
    p('  class members: %s' % [m for m in dir(SMD) if not m.startswith('_')])
    for m in [x for x in dir(SMD) if not x.startswith('_')]:
        doc = (getattr(SMD, m).__doc__ or '').strip().replace('\r\n', ' ')
        if doc:
            p('    .%s -> %s' % (m, doc[:260]))
    p('  enum/other: %s' % [n for n in dir(unreal)
                            if n.startswith('MF_') or 'PolygonGroup' in n
                            or n.startswith('Attributes')][:20])

    p('')
    p('=== C. build a box through the description ===')
    try:
        md = sm.create_static_mesh_description()
        p('  md = %s [%s]' % (md, md.get_class().get_name()))
        p('  instance members: %s' % [m for m in dir(md) if not m.startswith('_')])
    except Exception as exc:
        p('  create_static_mesh_description -> %r' % str(exc)[:200])
        return

    p('')
    p('=== D. cleanup ===')
    if unreal.load_asset(mpath):
        unreal.EditorAssetLibrary.delete_asset(mpath)
    p('DONE')


try:
    main()
except Exception:
    p(traceback.format_exc())
    p('A61_FATAL')
finally:
    with open(os.path.join(OUT, 'report.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
