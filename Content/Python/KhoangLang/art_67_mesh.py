"""Art pass probe 67: material slots and UV persistence on built meshes.

Probe 66 built a 2-slot mesh but get_material(0) returned None. Need to know
whether that is (a) a real failure or (b) a readback quirk, and whether
EditorStaticMeshLibrary (static, may work in a commandlet) can add slots.
"""

import os
import traceback

import unreal

OUT = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\art67'
os.makedirs(OUT, exist_ok=True)
REP = os.path.join(OUT, 'report.txt')


def p(m=''):
    line = str(m)
    unreal.log('A67: ' + line)
    with open(REP, 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


def guard(label, fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except Exception as exc:
        p('  ! %s -> %r' % (label, str(exc)[:200]))
        return None


def new(name, folder='/Game/KhoangLang/ArtTest'):
    at = unreal.AssetToolsHelpers.get_asset_tools()
    path = '%s/%s' % (folder, name)
    if unreal.load_asset(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    return path, at.create_asset(name, folder, unreal.StaticMesh, None)


def simple_mesh(sm):
    md = sm.create_static_mesh_description()
    for slot, (cx, hy) in (('KL_Wood', (0.0, 20.0)), ('KL_Metal', (200.0, 10.0))):
        g = md.create_polygon_group()
        md.set_polygon_group_material_slot_name(g, slot)
        md.create_cube(unreal.Vector(cx, 0, 50), unreal.Vector(50, hy, 50), g)
    return md


def main():
    p('=== A. is EditorStaticMeshLibrary usable in a commandlet? ===')
    p('  has EditorStaticMeshLibrary: %s' % hasattr(unreal, 'EditorStaticMeshLibrary'))
    L = unreal.EditorStaticMeshLibrary
    ms = [m for m in dir(L) if not m.startswith('_')]
    p('  members: %s' % ms)
    for n in ('add_simple_collisions', 'get_number_materials', 'get_number_sections',
              'get_number_verts', 'get_number_triangles', 'get_num_uv_channels',
              'set_material', 'generate_box_uv_channel'):
        d = (getattr(L, n).__doc__ or '')[:200].replace('\r\n', ' ') if hasattr(L, n) else ''
        p('    %s: %s' % (n, d))

    p('')
    p('=== B. build a 2-slot mesh, then inspect with the static library ===')
    path, sm = new('A67_Two')
    md = simple_mesh(sm)
    p('  desc: v=%d p=%d g=%d' % (md.get_vertex_count(), md.get_polygon_count(),
                                 md.get_polygon_group_count()))
    guard('build', sm.build_from_static_mesh_descriptions, [md])
    guard('save', unreal.EditorAssetLibrary.save_asset, path)
    p('  EditorStaticMeshLibrary.get_number_materials -> %s'
      % guard('get_number_materials', L.get_number_materials, sm))
    p('  EditorStaticMeshLibrary.get_number_sections -> %s'
      % guard('get_number_sections', L.get_number_sections, sm))
    p('  EditorStaticMeshLibrary.get_number_verts -> %s'
      % guard('get_number_verts', L.get_number_verts, sm))
    p('  EditorStaticMeshLibrary.get_num_uv_channels -> %s'
      % guard('get_num_uv_channels', L.get_num_uv_channels, sm))
    p('  StaticMesh.get_num_sections(0) -> %s' % guard('get_num_sections',
                                                       sm.get_num_sections, 0))
    p('  StaticMesh.get_material(0) -> %s' % guard('get_material', sm.get_material, 0))
    p('  StaticMesh.get_material(1) -> %s' % guard('get_material', sm.get_material, 1))

    p('')
    p('=== C. does the asset expose slots any other way? ===')
    for prop in ('static_materials', 'materials', 'override_materials'):
        try:
            v = sm.get_editor_property(prop)
            p('  %s = %s' % (prop, v))
        except Exception as exc:
            p('  %s -> %r' % (prop, str(exc)[:120]))
    p('  StaticMesh.add_material exists: %s' % hasattr(sm, 'add_material'))
    miw = unreal.load_asset('/Game/KhoangLang/MaterialsArt/MI_ART_Wood')
    mim = unreal.load_asset('/Game/KhoangLang/MaterialsArt/MI_ART_MetalRust')
    if miw:
        p('  add_material(0, MI_Wood) -> %r' % (guard('add_material', sm.add_material,
                                                      0, miw),))
        p('  get_material(0) now -> %s' % guard('get_material', sm.get_material, 0))
        p('  set_material(1, MI_Metal) -> %r' % (guard('set_material', sm.set_material,
                                                       1, mim),))
        p('  get_material(1) now -> %s' % guard('get_material', sm.get_material, 1))
        guard('resave', unreal.EditorAssetLibrary.save_asset, path)

    p('')
    p('=== D. reload from disk: do slots survive serialization? ===')
    del sm
    again = unreal.load_asset(path)
    p('  reloaded: %s' % (again.get_name() if again else None))
    if again:
        p('  get_material(0) = %s' % again.get_material(0))
        p('  get_material(1) = %s' % again.get_material(1))
        p('  sections = %s' % again.get_num_sections(0))
        p('  materials via lib = %s' % guard('n', unreal.EditorStaticMeshLibrary.
                                             get_number_materials, again))
        try:
            p('  static_materials = %s' % (again.get_editor_property('static_materials'),))
        except Exception as exc:
            p('  static_materials -> %r' % str(exc)[:120])

    p('')
    p('=== E. UV persistence: check via the editor subsystem on a loaded mesh ===')
    smi = guard('get_editor_subsystem(StaticMeshEditorSubsystem)',
                unreal.get_editor_subsystem, unreal.StaticMeshEditorSubsystem)
    p('  subsystem: %s' % smi)
    if again and smi:
        p('  uv channels = %s' % guard('uv', smi.get_num_uv_channels, again))
        p('  lightmap uv index = %s' % guard('lm', again.get_editor_property,
                                             'light_map_coordinate_index'))
        # a real check: the mesh must render with the material's UVs, so confirm
        # the render data has a UV channel by asking the mesh description
        try:
            mdR = again.get_static_mesh_description(0)
            p('  desc uv count = %s' % mdR.get_num_uv_channels())
        except Exception as exc:
            p('  desc uv count -> %r' % str(exc)[:150])
    p('  MeshDescription uv members: %s' % [m for m in dir(unreal.StaticMeshDescription)
                                            if 'uv' in m.lower()])

    p('')
    p('=== F. alternate route: set material on the ACTOR instead of the asset ===')
    p('  (this is what the level builder actually needs)')
    p('  StaticMeshActor override_materials is a component property; the')
    p('  component-level path is verified in art_30_level.py already.')

    p('')
    p('=== G. cleanup ===')
    for pp in (path,):
        if unreal.load_asset(pp):
            unreal.EditorAssetLibrary.delete_asset(pp)
    p('DONE')


if os.path.exists(REP):
    os.remove(REP)
try:
    main()
except Exception:
    p(traceback.format_exc())
    p('A67_FATAL')
