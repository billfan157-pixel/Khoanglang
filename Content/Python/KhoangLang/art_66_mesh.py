"""Art pass probe 66: verify the mesh kit primitives end to end.

Safe authoring calls established by probe 65:
  create_cube(center, half_extents, polygon_group)
  create_triangle(polygon_group, [vi, vi, vi])   <- create_polygon() crashes

This probe builds a real modular piece (a panelled door leaf) and checks that
UVs, material slots and collision all survive the build.
"""

import math
import os
import traceback

import unreal

OUT = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\art66'
os.makedirs(OUT, exist_ok=True)
REP = os.path.join(OUT, 'report.txt')


def p(m=''):
    line = str(m)
    unreal.log('A66: ' + line)
    with open(REP, 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


def guard(label, fn, *a, **kw):
    try:
        r = fn(*a, **kw)
        return r
    except Exception as exc:
        p('  ! %s -> %r' % (label, str(exc)[:200]))
        return None


# --------------------------------------------------------------------------- #
# mesh builder
# --------------------------------------------------------------------------- #

class MB(object):
    """Accumulates vertices / vertex instances / triangles with UVs."""

    def __init__(self, desc):
        self.d = desc
        self.verts = {}
        self.groups = {}

    def group(self, slot):
        if slot not in self.groups:
            g = self.d.create_polygon_group()
            self.d.set_polygon_group_material_slot_name(g, slot)
            self.groups[slot] = g
        return self.groups[slot]

    def _vid(self, x, y, z):
        k = (round(x, 4), round(y, 4), round(z, 4))
        if k not in self.verts:
            v = self.d.create_vertex()
            self.d.set_vertex_position(v, unreal.Vector(*k))
            self.verts[k] = v
        return self.verts[k]

    def tri(self, slot, p0, uv0, p1, uv1, p2, uv2):
        g = self.group(slot)
        vis = []
        for (pt, uv) in ((p0, uv0), (p1, uv1), (p2, uv2)):
            v = self._vid(*pt)
            vi = self.d.create_vertex_instance(v)
            self.d.set_vertex_instance_uv(vi, unreal.Vector2D(*uv))
            vis.append(vi)
        self.d.create_triangle(g, vis)

    def quad(self, slot, p0, p1, p2, p3, u0, u1, u2, u3):
        """p0..p3 counter-clockwise seen from the front."""
        self.tri(slot, p0, (u0[0], u0[1]), p1, (u1[0], u1[1]), p2, (u2[0], u2[1]))
        self.tri(slot, p0, (u0[0], u0[1]), p2, (u2[0], u2[1]), p3, (u3[0], u3[1]))

    def box(self, slot, x0, y0, z0, x1, y1, z1, uv_scale=1.0, base=(0.0, 0.0)):
        """Axis-aligned box with per-face planar UVs in metres."""
        s = uv_scale
        ux = abs(x1 - x0) / 100.0 * s
        uy = abs(y1 - y0) / 100.0 * s
        uz = abs(z1 - z0) / 100.0 * s
        bx, by = base

        def U(a, b):
            return (bx + a, by + b)
        # -Y / +Y faces (front/back), normal along Y
        self.quad(slot, (x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1),
                  U(0, 0), U(ux, 0), U(ux, uz), U(0, uz))
        self.quad(slot, (x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1),
                  U(0, 0), U(ux, 0), U(ux, uz), U(0, uz))
        # -X / +X
        self.quad(slot, (x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1),
                  U(0, 0), U(uy, 0), U(uy, uz), U(0, uz))
        self.quad(slot, (x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1),
                  U(0, 0), U(uy, 0), U(uy, uz), U(0, uz))
        # top / bottom
        self.quad(slot, (x0, y1, z1), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1),
                  U(0, 0), U(uy, 0), U(ux + uy, 0), U(ux, uy))
        self.quad(slot, (x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0),
                  U(0, 0), U(uy, 0), U(ux + uy, 0), U(ux, uy))


def new(name, folder='/Game/KhoangLang/ArtTest'):
    at = unreal.AssetToolsHelpers.get_asset_tools()
    path = '%s/%s' % (folder, name)
    if unreal.load_asset(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    sm = at.create_asset(name, folder, unreal.StaticMesh, None)
    return path, sm


def main():
    p('=== A. build a panelled door leaf ===')
    path, sm = new('A66_Door')
    md = sm.create_static_mesh_description()
    b = MB(md)
    W, H, T = 90.0, 210.0, 4.0
    # stile/rail frame, 4 recessed panels -> reads as a real door, not a slab
    b.box('KL_Wood', 0, 0, 0, W, T, H, 0.35)
    for (pz0, pz1) in ((0, 70), (80, 130), (140, 210)):
        # recessed panel: pull the face in by 1.2 cm, inset 9 cm from stiles
        b.box('KL_WoodDark', 9, T, pz0 + 8, W - 9, T + 1.2, pz1 - 8, 0.6)
    p('  desc: v=%d e=%d vi=%d p=%d t=%d g=%d' % (
        md.get_vertex_count(), md.get_edge_count(), md.get_vertex_instance_count(),
        md.get_polygon_count(), md.get_triangle_count(), md.get_polygon_group_count()))
    guard('build', sm.build_from_static_mesh_descriptions, [md])
    guard('save', unreal.EditorAssetLibrary.save_asset, path)
    bb = sm.get_bounds()
    p('  bounds origin=%s extent=%s' % (bb.origin, bb.box_extent))
    p('  num sections=%s  num tris=%s' % (
        guard('get_num_sections', sm.get_num_sections, 0),
        guard('get_num_triangles', sm.get_num_triangles, 0)))

    p('')
    p('=== B. do UVs survive the build? ===')
    try:
        md2 = sm.get_static_mesh_description(0)
        p('  readback: v=%d vi=%d p=%d t=%d' % (
            md2.get_vertex_count(), md2.get_vertex_instance_count(),
            md2.get_polygon_count(), md2.get_triangle_count()))
        uvs = []
        for vi in range(min(8, md2.get_vertex_instance_count())):
            uvs.append(str(md2.get_vertex_instance_uv(vi)))
        p('  first UVs: %s' % uvs)
        nonzero = 0
        for vi in range(md2.get_vertex_instance_count()):
            uv = md2.get_vertex_instance_uv(vi)
            if abs(uv.x) > 1e-6 or abs(uv.y) > 1e-6:
                nonzero += 1
        p('  vertex instances with non-zero UV: %d / %d'
          % (nonzero, md2.get_vertex_instance_count()))
    except Exception as exc:
        p('  readback EXC %r' % str(exc)[:200])

    p('')
    p('=== C. material slots ===')
    for n in range(3):
        p('  slot %d = %s' % (n, guard('get_material', sm.get_material, n)))
    miw = unreal.load_asset('/Game/KhoangLang/MaterialsArt/MI_ART_Wood')
    mid = unreal.load_asset('/Game/KhoangLang/MaterialsArt/MI_ART_WoodDark')
    p('  MI_Wood=%s MI_WoodDark=%s' % (miw is not None, mid is not None))
    if miw:
        guard('set_material(0)', sm.set_material, 0, miw)
        guard('set_material(1)', sm.set_material, 1, mid)
        guard('resave', unreal.EditorAssetLibrary.save_asset, path)
        p('  after assign: 0=%s 1=%s' % (sm.get_material(0), sm.get_material(1)))

    p('')
    p('=== D. collision on the asset ===')
    smi = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    p('  StaticMeshEditorSubsystem available: %s' % (smi is not None))
    p('  has add_simple_collisions: %s' % hasattr(smi, 'add_simple_collisions'))
    if smi:
        guard('add_simple_collisions', smi.add_simple_collisions, sm)
        p('  simple collision count=%s' % guard('get_simple_collision_count',
                                                smi.get_simple_collision_count, sm))

    p('')
    p('=== E. component collision API (the art_30_level crash) ===')
    comp = unreal.StaticMeshComponent()
    p('  set_collision_enabled: %s' % hasattr(comp, 'set_collision_enabled'))
    guard('set_collision_enabled', comp.set_collision_enabled,
          unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    p('  get_collision_enabled -> %s' % guard('get_collision_enabled',
                                              comp.get_collision_enabled))
    guard('set_collision_profile_name', comp.set_collision_profile_name, 'BlockAll')
    for n in ('generate_lightmap_uvs', 'cast_shadow', 'can_ever_affect_navigation',
              'visible_in_ray_tracing', 'b_allow_distance_field_shadows',
              'b_cast_dynamic_shadow', 'b_receives_decals'):
        try:
            comp.set_editor_property(n, True)
            p('    %s settable' % n)
        except Exception as exc:
            p('    %s NOT settable (%s)' % (n, str(exc)[:70]))

    p('')
    p('=== F. AutoExposureMethod members (art_30_level crash cause) ===')
    p('  all: %s' % [a for a in dir(unreal.AutoExposureMethod) if not a.startswith('_')])
    p('  with AEM_ prefix: %s' % [a for a in dir(unreal.AutoExposureMethod)
                                  if a.startswith('AEM')])
    p('  get_name() helper available: %s' % hasattr(unreal.AutoExposureMethod, 'get_name'))

    p('')
    p('=== G. exponential height fog properties ===')
    fog = unreal.ExponentialHeightFogComponent()
    p('  members: %s' % [m for m in dir(fog) if not m.startswith('_')
                         and ('fog' in m or 'scatter' in m or 'volum' in m)])

    p('')
    p('=== H. cleanup ===')
    if unreal.load_asset(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    p('DONE')


if os.path.exists(REP):
    os.remove(REP)
try:
    main()
except Exception:
    p(traceback.format_exc())
    p('A66_FATAL')
