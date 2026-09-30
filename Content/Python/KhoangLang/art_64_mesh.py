"""Art pass probe 64: find the safe polygon-creation sequence.

Probe 63 crashed: create_polygon() then get_polygon_group_polygons()[-1] indexed
an empty array. Every call here is individually guarded so the probe reports
which sequence actually works instead of taking the process down.
"""

import os
import traceback

import unreal

OUT = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\art64'
os.makedirs(OUT, exist_ok=True)
L = []


def p(m=''):
    L.append(str(m))
    unreal.log('A64: ' + str(m))


def guard(label, fn, *a, **kw):
    try:
        r = fn(*a, **kw)
        p('  %s -> %r' % (label, r))
        return r
    except Exception as exc:
        p('  %s -> EXC %r' % (label, str(exc)[:200]))
        return None


def new_desc(sm):
    return sm.create_static_mesh_description()


def make_asset(name):
    at = unreal.AssetToolsHelpers.get_asset_tools()
    path = '/Game/KhoangLang/ArtTest/%s' % name
    if unreal.load_asset(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    sm = at.create_asset(name, '/Game/KhoangLang/ArtTest', unreal.StaticMesh, None)
    return path, sm


def quad_points(y=0.0, z=0.0, s=100.0):
    return [(0, y, z), (s, y, z), (s, y + s, z), (0, y + s, z)]


def main():
    p('=== A. sequence 1: create_vertex + create_polygon + set_polygon_vertex_instances ===')
    path, sm = make_asset('A64_Seq1')
    md = new_desc(sm)
    g = guard('create_polygon_group', md.create_polygon_group)
    pts = quad_points()
    vis = []
    for (x, y, z) in pts:
        v = guard('  create_vertex', md.create_vertex)
        guard('  set_vertex_position', md.set_vertex_position, v, unreal.Vector(x, y, z))
        vi = guard('  create_vertex_instance', md.create_vertex_instance, v)
        guard('  set_vertex_instance_uv', md.set_vertex_instance_uv, vi,
              unreal.Vector2D(x / 100.0, y / 100.0))
        vis.append(vi)
    p('  v=%d vi=%d' % (md.get_vertex_count(), md.get_vertex_instance_count()))
    poly = guard('create_polygon(g)', md.create_polygon, g)
    p('  after create_polygon: p=%d  returned=%r' % (md.get_polygon_count(), poly))
    p('  group polygons now: %r' % (md.get_polygon_group_polygons(g),))
    if poly is not None:
        pid = poly[0] if isinstance(poly, (tuple, list)) else poly
        guard('set_polygon_vertex_instances(pid, vis)', md.set_polygon_vertex_instances,
              pid, vis)
        p('  polygon valid=%s numverts=%s' % (
            md.is_polygon_valid(pid), md.get_num_polygon_vertices(pid)))
    p('  desc: p=%d t=%d' % (md.get_polygon_count(), md.get_triangle_count()))
    guard('build', sm.build_from_static_mesh_descriptions, [md])
    guard('save', unreal.EditorAssetLibrary.save_asset, path)
    p('  bounds=%s' % (sm.get_bounds().box_extent,))

    p('')
    p('=== B. sequence 2: create_triangle(polygon_group, [vi...]) ===')
    path2, sm2 = make_asset('A64_Seq2')
    md2 = new_desc(sm2)
    g2 = guard('create_polygon_group', md2.create_polygon_group)
    vis2 = []
    for (x, y, z) in [(0, 0, 0), (100, 0, 0), (100, 100, 0)]:
        v = md2.create_vertex()
        md2.set_vertex_position(v, unreal.Vector(x, y, z))
        vi = md2.create_vertex_instance(v)
        md2.set_vertex_instance_uv(vi, unreal.Vector2D(x / 100.0, y / 100.0))
        vis2.append(vi)
    t = guard('create_triangle(g, vis)', md2.create_triangle, g2, vis2)
    p('  desc: v=%d p=%d t=%d' % (md2.get_vertex_count(), md2.get_polygon_count(),
                                 md2.get_triangle_count()))
    guard('build', sm2.build_from_static_mesh_descriptions, [md2])
    guard('save', unreal.EditorAssetLibrary.save_asset, path2)
    p('  bounds=%s' % (sm2.get_bounds().box_extent,))

    p('')
    p('=== C. create_cube helper ===')
    path3, sm3 = make_asset('A64_Seq3')
    md3 = new_desc(sm3)
    g3 = md3.create_polygon_group()
    r = guard('create_cube', md3.create_cube, unreal.Vector(0, 0, 0),
              unreal.Vector(50, 20, 110), g3)
    p('  returned tuple len=%s' % (len(r) if r else None))
    p('  desc: v=%d p=%d t=%d' % (md3.get_vertex_count(), md3.get_polygon_count(),
                                  md3.get_triangle_count()))
    guard('build', sm3.build_from_static_mesh_descriptions, [md3])
    guard('save', unreal.EditorAssetLibrary.save_asset, path3)
    p('  bounds=%s' % (sm3.get_bounds().box_extent,))

    p('')
    p('=== D. material slot naming ===')
    for n in (0, 1):
        guard('set_polygon_group_material_slot_name(%d, slot)' % n,
              md.set_polygon_group_material_slot_name, g, 'KL_Wood')
    p('  group count=%d' % md.get_polygon_group_count())
    guard('rebuild', sm.build_from_static_mesh_descriptions, [md])
    guard('resave', unreal.EditorAssetLibrary.save_asset, path)
    guard('get_material(0)', sm.get_material, 0)
    p('  num_sections via get_num_sections: %s' % guard('get_num_sections',
                                                         sm.get_num_sections, 0))

    p('')
    p('=== E. UV readback after build ===')
    try:
        md5 = sm.get_static_mesh_description(0)
        p('  reloaded: v=%d p=%d t=%d vi=%d' % (
            md5.get_vertex_count(), md5.get_polygon_count(),
            md5.get_triangle_count(), md5.get_vertex_instance_count()))
        got = []
        for vi in range(min(4, md5.get_vertex_instance_count())):
            got.append(md5.get_vertex_instance_uv(vi))
        p('  UVs: %s' % (got,))
    except Exception as exc:
        p('  readback EXC %r' % str(exc)[:200])

    p('')
    p('=== F. smoothing groups (hard edges vs smooth) ===')
    p('  SmoothingGroup enum: %s' % (
        [a for a in dir(unreal.SmoothingGroup) if not a.startswith('_')]
        if hasattr(unreal, 'SmoothingGroup') else 'missing',))
    p('  StaticMesh props with smooth/lightmap: %s' % (
        [x for x in dir(unreal.StaticMesh) if 'smooth' in x.lower()],))

    p('')
    p('=== G. build settings that matter for perf ===')
    for prop, val in (('light_map_resolution_scale', 1.0),
                      ('light_map_coordinate_index', 0),
                      ('light_map_scale', 1.0),
                      ('light_map_relative_size_scale', 1.0),
                      ('distance_field_scale', 1.0),
                      ('import_uniform_scale', 1.0),
                      ('min_lightmap_resolution', 4),
                      ('b_support_uniformly_distributed_distributive_lightmaps', False)):
        guard('set %s' % prop, sm.set_editor_property, prop, val)

    p('')
    p('=== H. cleanup ===')
    for pp in (path, path2, path3):
        if unreal.load_asset(pp):
            unreal.EditorAssetLibrary.delete_asset(pp)
    p('DONE')


try:
    main()
except Exception:
    p(traceback.format_exc())
    p('A64_FATAL')
finally:
    with open(os.path.join(OUT, 'report.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
