"""Art pass probe 65: which polygon-creation call is actually safe?

Probe 64 crashed inside create_polygon(). The report is flushed to disk after
every step here, so a hard crash still leaves the findings of the steps that
already ran. Tests are ordered safest-first.

Candidates:
  A) create_cube(center, half_extents, polygon_group)      - built-in
  B) create_triangle(polygon_group, [vi...])              - creates its own edges
  C) create_edge(v0, v1) then create_polygon(g)           - pre-made edges
  D) create_polygon_with_id(...)
"""

import os
import traceback

import unreal

OUT = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\art65'
os.makedirs(OUT, exist_ok=True)
REP = os.path.join(OUT, 'report.txt')


def p(m=''):
    line = str(m)
    unreal.log('A65: ' + line)
    with open(REP, 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


def guard(label, fn, *a, **kw):
    try:
        r = fn(*a, **kw)
        p('  %s -> ok %r' % (label, r))
        return r
    except Exception as exc:
        p('  %s -> EXC %r' % (label, str(exc)[:220]))
        return None


def new(name):
    at = unreal.AssetToolsHelpers.get_asset_tools()
    path = '/Game/KhoangLang/ArtTest/%s' % name
    if unreal.load_asset(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    sm = at.create_asset(name, '/Game/KhoangLang/ArtTest', unreal.StaticMesh, None)
    return path, sm


def stats(md):
    return 'v=%d e=%d vi=%d p=%d t=%d g=%d' % (
        md.get_vertex_count(), md.get_edge_count(), md.get_vertex_instance_count(),
        md.get_polygon_count(), md.get_triangle_count(), md.get_polygon_group_count())


def main():
    p('start')

    # ---------------- A: create_cube -------------------------------------- #
    p('')
    p('=== A. create_cube ===')
    pA, smA = new('A65_Cube')
    mdA = smA.create_static_mesh_description()
    gA = mdA.create_polygon_group()
    p('  %s' % stats(mdA))
    r = guard('create_cube', mdA.create_cube, unreal.Vector(0, 0, 0),
              unreal.Vector(50, 20, 110), gA)
    p('  after cube: %s' % stats(mdA))
    if r is not None:
        p('  slot names on group: %s' % guard('set_slot_name',
                                              mdA.set_polygon_group_material_slot_name,
                                              gA, 'KL_Plaster'))
        guard('build', smA.build_from_static_mesh_descriptions, [mdA])
        guard('save', unreal.EditorAssetLibrary.save_asset, pA)
        p('  A bounds extent=%s' % (smA.get_bounds().box_extent,))
        try:
            mdR = smA.get_static_mesh_description(0)
            p('  A readback: %s' % stats(mdR))
        except Exception as exc:
            p('  A readback EXC %r' % str(exc)[:150])

    # ---------------- B: create_triangle ---------------------------------- #
    p('')
    p('=== B. create_triangle(polygon_group, [vi...]) ===')
    pB, smB = new('A65_Tri')
    mdB = smB.create_static_mesh_description()
    gB = mdB.create_polygon_group()
    vis = []
    for (x, y, z) in [(0, 0, 0), (100, 0, 0), (100, 100, 0)]:
        v = mdB.create_vertex()
        mdB.set_vertex_position(v, unreal.Vector(x, y, z))
        vi = mdB.create_vertex_instance(v)
        mdB.set_vertex_instance_uv(vi, unreal.Vector2D(x / 100.0, y / 100.0))
        vis.append(vi)
    p('  before: %s' % stats(mdB))
    guard('create_triangle', mdB.create_triangle, gB, vis)
    p('  after: %s' % stats(mdB))
    guard('build', smB.build_from_static_mesh_descriptions, [mdB])
    guard('save', unreal.EditorAssetLibrary.save_asset, pB)
    p('  B bounds extent=%s' % (smB.get_bounds().box_extent,))

    # ---------------- C: pre-made edges then create_polygon ---------------- #
    p('')
    p('=== C. create_edge x4 then create_polygon(g) ===')
    pC, smC = new('A65_Edge')
    mdC = smC.create_static_mesh_description()
    gC = mdC.create_polygon_group()
    vids = []
    for (x, y, z) in [(0, 0, 0), (100, 0, 0), (100, 100, 0), (0, 100, 0)]:
        v = mdC.create_vertex()
        mdC.set_vertex_position(v, unreal.Vector(x, y, z))
        vids.append(v)
    p('  after verts: %s' % stats(mdC))
    for i in range(4):
        guard('  create_edge %d' % i, mdC.create_edge, vids[i], vids[(i + 1) % 4])
    p('  after edges: %s' % stats(mdC))
    guard('create_polygon', mdC.create_polygon, gC)
    p('  after polygon: %s' % stats(mdC))

    p('')
    p('=== D. info dumps ===')
    p('  create_polygon doc: %s' % (mdC.create_polygon.__doc__ or '')[:300]
      .replace('\r\n', ' '))
    p('  create_polygon_with_id doc: %s' % (mdC.create_polygon_with_id.__doc__ or '')[:300]
      .replace('\r\n', ' '))
    p('  build_from_static_mesh_descriptions doc: %s'
      % (unreal.StaticMesh.build_from_static_mesh_descriptions.__doc__ or '')[:400]
      .replace('\r\n', ' '))

    p('')
    p('=== E. cleanup ===')
    for pp in (pA, pB, pC):
        if unreal.load_asset(pp):
            try:
                unreal.EditorAssetLibrary.delete_asset(pp)
            except Exception as exc:
                p('  del %s EXC %r' % (pp, str(exc)[:100]))
    p('DONE')


if os.path.exists(REP):
    os.remove(REP)
try:
    main()
except Exception:
    p(traceback.format_exc())
    p('A65_FATAL')
