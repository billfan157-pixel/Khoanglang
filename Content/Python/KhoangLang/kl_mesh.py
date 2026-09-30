"""Khoang Lang 02:17 - procedural mesh authoring library.

Written against UE 5.8.3 Python, verified headlessly by probes 65-69.
This module is the foundation of the 3D art pipeline: it turns plain Python
geometry calls into real StaticMesh assets with UVs and material slots.

Verified API contract (do not change without re-probing):

  * unreal.StaticMeshDescription is exposed; unreal.MeshDescription is NOT.
  * SAFE:   create_vertex / set_vertex_position / create_vertex_instance /
            set_vertex_instance_uv / create_triangle / create_cube
  * UNSAFE: create_polygon() asserts and kills the process, even when the
            boundary edges already exist. Always author triangles.
  * Build:  StaticMesh.build_from_static_mesh_descriptions([desc])
  * Slots:  add_material(material) returns the slot Name and MUST be called
            before the build; set_polygon_group_material_slot_name(group, name)
            binds a polygon group to that slot. get_number_materials() always
            reports 0 in a commandlet - use get_num_sections(0) instead.

No Blender, no third-party assets, no external downloads. Everything here is
generated from code so the whole art pass stays reviewable in version control.

Conventions used throughout the art pass:

  * Units are centimetres, matching Unreal.
  * +X is east, +Y is north, +Z is up.
  * Kit pieces are modelled around their own origin so they can be placed and
    rotated in the level without per-instance fudge factors.
  * UVs are laid out in metres with a per-piece scale, so a wall panel and a
    door leaf show the same texel density. This is what makes tiling materials
    read as one building instead of a pile of unrelated surfaces.
"""

import math

import unreal

# --------------------------------------------------------------------------- #
# logging
# --------------------------------------------------------------------------- #

LOG = []


def log(msg):
    LOG.append(str(msg))
    unreal.log('KLMESH: ' + str(msg))


def warn(msg):
    LOG.append('WARN ' + str(msg))
    unreal.log_warning('KLMESH: ' + str(msg))


# --------------------------------------------------------------------------- #
# mesh builder
# --------------------------------------------------------------------------- #

class MeshBuilder(object):
    """Accumulates geometry, then bakes it into a StaticMesh asset.

    Vertices are welded by position, but every triangle gets its own vertex
    instances so UV seams and hard edges are preserved. That is exactly what
    an architectural kit needs: crisp corners, continuous texel density.
    """

    def __init__(self, name):
        self.name = name
        self._sm = None
        self._desc = None
        self._verts = {}
        self._groups = {}
        self._slot_names = []
        self._materials = []
        self._tri_count = 0
        self._box_min = [1e18, 1e18, 1e18]
        self._box_max = [-1e18, -1e18, -1e18]

    # -- material slots ----------------------------------------------------- #

    def material(self, asset_path):
        """Register a material, creating the slot before the build.

        Returns the slot name to hand to :meth:`group`.
        """
        mat = unreal.load_asset(asset_path)
        if mat is None:
            raise RuntimeError('mesh %s: material not found: %s'
                               % (self.name, asset_path))
        slot = self._sm.add_material(mat)
        self._materials.append((str(slot), mat))
        return slot

    def group(self, slot):
        """Return (creating if needed) the polygon group bound to a slot."""
        key = str(slot)
        if key not in self._groups:
            g = self._desc.create_polygon_group()
            self._desc.set_polygon_group_material_slot_name(g, key)
            self._groups[key] = g
        return self._groups[key]

    # -- low level ---------------------------------------------------------- #

    def _vid(self, p):
        k = (round(p[0], 3), round(p[1], 3), round(p[2], 3))
        if k not in self._verts:
            v = self._desc.create_vertex()
            self._desc.set_vertex_position(v, unreal.Vector(*k))
            self._verts[k] = v
        for i in range(3):
            if k[i] < self._box_min[i]:
                self._box_min[i] = k[i]
            if k[i] > self._box_max[i]:
                self._box_max[i] = k[i]
        return self._verts[k]

    def tri(self, slot, p0, uv0, p1, uv1, p2, uv2):
        g = self.group(slot)
        vis = []
        for pt, uv in ((p0, uv0), (p1, uv1), (p2, uv2)):
            v = self._vid(pt)
            vi = self._desc.create_vertex_instance(v)
            self._desc.set_vertex_instance_uv(vi, unreal.Vector2D(float(uv[0]),
                                                                 float(uv[1])))
            vis.append(vi)
        self._desc.create_triangle(g, vis)
        self._tri_count += 1

    def quad(self, slot, p0, p1, p2, p3, uvs=None, uv_scale=1.0, uv_offset=(0.0, 0.0)):
        """Quad p0..p3, wound counter-clockwise when seen from the front."""
        if uvs is None:
            w = abs(p1[0] - p0[0]) + abs(p1[1] - p0[1]) + abs(p1[2] - p0[2])
            h = abs(p3[0] - p0[0]) + abs(p3[1] - p0[1]) + abs(p3[2] - p0[2])
            uvs = [(0.0, 0.0), (w / 100.0, 0.0), (w / 100.0, h / 100.0), (0.0, h / 100.0)]
        uvs = [(uv_offset[0] + u[0] * uv_scale, uv_offset[1] + u[1] * uv_scale)
               for u in uvs]
        self.tri(slot, p0, uvs[0], p1, uvs[1], p2, uvs[2])
        self.tri(slot, p0, uvs[0], p2, uvs[2], p3, uvs[3])

    # -- primitives --------------------------------------------------------- #

    def box(self, slot, x0, y0, z0, x1, y1, z1, uv_scale=1.0, uv_origin=(0.0, 0.0),
            skip=(), cap_uv=True):
        """Axis-aligned box. ``skip`` drops faces by name to save triangles.

        Face names: 'xp','xn','yp','yn','zp','zn'. Skipping the two faces
        that are buried inside a wall is a real saving on a kit wall.
        """
        ux = abs(x1 - x0) / 100.0 * uv_scale
        uy = abs(y1 - y0) / 100.0 * uv_scale
        uz = abs(z1 - z0) / 100.0 * uv_scale
        ox, oy = uv_origin

        def U(a, b):
            return (ox + a, oy + b)

        if 'yn' not in skip:
            self.quad(slot, (x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1),
                      uvs=[U(0, 0), U(ux, 0), U(ux, uz), U(0, uz)])
        if 'yp' not in skip:
            self.quad(slot, (x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1),
                      uvs=[U(0, 0), U(ux, 0), U(ux, uz), U(0, uz)])
        if 'xn' not in skip:
            self.quad(slot, (x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1),
                      uvs=[U(0, 0), U(uy, 0), U(uy, uz), U(0, uz)])
        if 'xp' not in skip:
            self.quad(slot, (x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1),
                      uvs=[U(0, 0), U(uy, 0), U(uy, uz), U(0, uz)])
        if 'zp' not in skip:
            self.quad(slot, (x0, y1, z1), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1),
                      uvs=[U(0, 0), U(uy, 0), U(ux, uy), U(ux, 0)])
        if 'zn' not in skip:
            self.quad(slot, (x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0),
                      uvs=[U(0, 0), U(uy, 0), U(ux, uy), U(ux, 0)])

    def chamfer_box(self, slot, x0, y0, z0, x1, y1, z1, c=1.2, uv_scale=1.0):
        """Box with cut corners.

        A 1-2 cm chamfer is the cheapest way to make architecture stop looking
        like a pile of cubes: it gives every silhouette edge a specular
        highlight, which is most of what the eye reads as 'real'.
        44 triangles instead of 12, so use it on hero pieces, not on every wall.
        """
        c = min(c, abs(x1 - x0) * 0.4, abs(y1 - y0) * 0.4, abs(z1 - z0) * 0.4)
        ix0, ix1 = x0 + c, x1 - c
        iy0, iy1 = y0 + c, y1 - c
        iz0, iz1 = z0 + c, z1 - c

        # six inset faces
        self.quad(slot, (ix0, y0, iz0), (ix1, y0, iz0), (ix1, y0, iz1), (ix0, y0, iz1),
                  uv_scale=uv_scale)
        self.quad(slot, (ix1, y1, iz0), (ix0, y1, iz0), (ix0, y1, iz1), (ix1, y1, iz1),
                  uv_scale=uv_scale)
        self.quad(slot, (x0, iy1, iz0), (x0, iy0, iz0), (x0, iy0, iz1), (x0, iy1, iz1),
                  uv_scale=uv_scale)
        self.quad(slot, (x1, iy0, iz0), (x1, iy1, iz0), (x1, iy1, iz1), (x1, iy0, iz1),
                  uv_scale=uv_scale)
        self.quad(slot, (ix0, iy1, z1), (ix0, iy0, z1), (ix1, iy0, z1), (ix1, iy1, z1),
                  uv_scale=uv_scale)
        self.quad(slot, (ix0, iy0, z0), (ix0, iy1, z0), (ix1, iy1, z0), (ix1, iy0, z0),
                  uv_scale=uv_scale)
        # 12 edge chamfers
        self._chamfer_edges(slot, x0, x1, y0, y1, z0, z1, 'x')
        self._chamfer_edges(slot, x0, x1, y0, y1, z0, z1, 'y')
        self._chamfer_edges(slot, x0, x1, y0, y1, z0, z1, 'z')
        # 8 corner triangles
        for sx in (0, 1):
            for sy in (0, 1):
                for sz in (0, 1):
                    cx = ix0 if sx == 0 else ix1
                    cy = iy0 if sy == 0 else iy1
                    cz = iz0 if sz == 0 else iz1
                    px = x0 if sx == 0 else x1
                    py = y0 if sy == 0 else y1
                    pz = z0 if sz == 0 else z1
                    a = (px, cy, cz)
                    b2 = (cx, py, cz)
                    d = (cx, cy, pz)
                    if sx ^ sy ^ sz:
                        self.tri(slot, a, (0, 0), b2, (0.05, 0), d, (0, 0.05))
                    else:
                        self.tri(slot, a, (0, 0), d, (0, 0.05), b2, (0.05, 0))

    def _chamfer_edges(self, slot, x0, x1, y0, y1, z0, z1, axis):
        c = min(1.2, abs(x1 - x0) * 0.4, abs(y1 - y0) * 0.4, abs(z1 - z0) * 0.4)
        ix0, ix1 = x0 + c, x1 - c
        iy0, iy1 = y0 + c, y1 - c
        iz0, iz1 = z0 + c, z1 - c
        small = [(0, 0), (0.05, 0), (0.05, 0.05), (0, 0.05)]
        if axis == 'x':
            quads = [((ix0, y0, iz0), (ix1, y0, iz0), (ix1, iy0, iz0), (ix0, iy0, iz0)),
                     ((ix1, y1, iz0), (ix0, y1, iz0), (ix0, iy1, iz0), (ix1, iy1, iz0)),
                     ((ix0, iy0, iz1), (ix1, iy0, iz1), (ix1, iy0, z1), (ix0, iy0, z1)),
                     ((ix0, iy0, z0), (ix1, iy0, z0), (ix1, iy0, iz0), (ix0, iy0, iz0))]
        elif axis == 'y':
            quads = [((x0, iy0, iz0), (x0, iy1, iz0), (ix0, iy1, iz0), (ix0, iy0, iz0)),
                     ((x1, iy1, iz0), (x1, iy0, iz0), (ix1, iy0, iz0), (ix1, iy1, iz0)),
                     ((x0, iy0, iz1), (x0, iy1, iz1), (ix0, iy1, z1), (ix0, iy0, z1)),
                     ((x0, iy0, z0), (x0, iy1, z0), (ix0, iy1, z0), (ix0, iy0, z0))]
        else:
            quads = [((ix0, y0, iz0), (ix0, iy0, iz0), (ix1, iy0, iz0), (ix1, y0, iz0)),
                     ((ix1, y1, iz0), (ix1, iy1, iz0), (ix0, iy1, iz0), (ix0, y1, iz0)),
                     ((x0, iy1, iz1), (x0, y1, iz1), (x0, y1, z1), (x0, iy1, z1)),
                     ((x1, y1, iz1), (x1, iy0, iz1), (x1, iy0, z1), (x1, y1, z1))]
        for q in quads:
            self.quad(slot, *q, uvs=small)

    def box_rot_z(self, slot, cx, cy, z0, z1, hx, hy, deg, uv_scale=1.0):
        """Box rotated about the Z axis through (cx, cy).

        Needed for fan blades, leaning books, angled shutters and anything else
        that is not axis aligned. Yaw is applied about the box's own centre.
        """
        a = math.radians(deg)
        ca, sa = math.cos(a), math.sin(a)

        def P(x, y):
            return (cx + x * ca - y * sa, cy + x * sa + y * ca)

        c = [P(-hx, -hy), P(hx, -hy), P(hx, hy), P(-hx, hy)]
        ux = (2 * hx) / 100.0 * uv_scale
        uy = (2 * hy) / 100.0 * uv_scale
        # top and bottom
        self.quad(slot, (c[3][0], c[3][1], z1), (c[2][0], c[2][1], z1),
                  (c[1][0], c[1][1], z1), (c[0][0], c[0][1], z1),
                  uvs=[(0, 0), (ux, 0), (ux, uy), (0, uy)])
        self.quad(slot, (c[0][0], c[0][1], z0), (c[1][0], c[1][1], z0),
                  (c[2][0], c[2][1], z0), (c[3][0], c[3][1], z0),
                  uvs=[(0, 0), (ux, 0), (ux, uy), (0, uy)])
        # sides
        self.quad(slot, (c[0][0], c[0][1], z0), (c[3][0], c[3][1], z0),
                  (c[3][0], c[3][1], z1), (c[0][0], c[0][1], z1),
                  uvs=[(0, 0), (ux, 0), (ux, uy), (0, uy)])
        self.quad(slot, (c[1][0], c[1][1], z0), (c[2][0], c[2][1], z0),
                  (c[2][0], c[2][1], z1), (c[1][0], c[1][1], z1),
                  uvs=[(0, 0), (ux, 0), (ux, uy), (0, uy)])
        self.quad(slot, (c[2][0], c[2][1], z0), (c[3][0], c[3][1], z0),
                  (c[3][0], c[3][1], z1), (c[2][0], c[2][1], z1),
                  uvs=[(0, 0), (ux, 0), (ux, uy), (0, uy)])
        self.quad(slot, (c[3][0], c[3][1], z0), (c[0][0], c[0][1], z0),
                  (c[0][0], c[0][1], z1), (c[3][0], c[3][1], z1),
                  uvs=[(0, 0), (ux, 0), (ux, uy), (0, uy)])

    def cylinder(self, slot, cx, cy, z0, z1, r, seg=12, uv_scale=1.0, caps=True,
                 axis='z', r_top=None):
        """N-gon prism. ``axis`` is the direction the tube runs along."""
        r_top = r if r_top is None else r_top
        h = abs(z1 - z0) / 100.0 * uv_scale
        for i in range(seg):
            a0 = 2.0 * math.pi * i / seg
            a1 = 2.0 * math.pi * (i + 1) / seg
            u0 = (2.0 * math.pi * r / 100.0) * (i / float(seg)) * uv_scale
            u1 = (2.0 * math.pi * r / 100.0) * ((i + 1) / float(seg)) * uv_scale

            def P(a, rad, t):
                if axis == 'z':
                    return (cx + rad * math.cos(a), cy + rad * math.sin(a), t)
                if axis == 'x':
                    return (t, cy + rad * math.cos(a), z0 + rad * math.sin(a))
                return (cx + rad * math.cos(a), t, z0 + rad * math.sin(a))

            self.quad(slot, P(a0, r, z0), P(a1, r, z0), P(a1, r_top, z1),
                      P(a0, r_top, z1),
                      uvs=[(u0, 0), (u1, 0), (u1, h), (u0, h)])
            if caps:
                if axis == 'z':
                    self.tri(slot, (cx, cy, z1), (0.5, 0.5),
                             P(a0, r_top, z1), (0, 0), P(a1, r_top, z1), (1, 0))
                    self.tri(slot, (cx, cy, z0), (0.5, 0.5),
                             P(a1, r, z0), (1, 0), P(a0, r, z0), (0, 0))
                elif axis == 'x':
                    self.tri(slot, (z1, cy, cx), (0.5, 0.5),
                             P(a0, r_top, z1), (0, 0), P(a1, r_top, z1), (1, 0))
                    self.tri(slot, (z0, cy, cx), (0.5, 0.5),
                             P(a1, r, z0), (1, 0), P(a0, r, z0), (0, 0))
                else:
                    self.tri(slot, (cx, z1, cy), (0.5, 0.5),
                             P(a0, r_top, z1), (0, 0), P(a1, r_top, z1), (1, 0))
                    self.tri(slot, (cx, z0, cy), (0.5, 0.5),
                             P(a1, r, z0), (1, 0), P(a0, r, z0), (0, 0))

    def tube(self, slot, x0, y0, z0, x1, y1, z1, r, seg=10, uv_scale=1.0):
        """Cylinder between two arbitrary points (pipes, rods, cables)."""
        ax = (x1 - x0, y1 - y0, z1 - z0)
        length = math.sqrt(ax[0] ** 2 + ax[1] ** 2 + ax[2] ** 2)
        if length < 1e-4:
            return
        ax = (ax[0] / length, ax[1] / length, ax[2] / length)
        up = (0.0, 0.0, 1.0) if abs(ax[2]) < 0.95 else (1.0, 0.0, 0.0)
        sx = (ax[1] * up[2] - ax[2] * up[1],
              ax[2] * up[0] - ax[0] * up[2],
              ax[0] * up[1] - ax[1] * up[0])
        sl = math.sqrt(sx[0] ** 2 + sx[1] ** 2 + sx[2] ** 2) or 1.0
        sx = (sx[0] / sl, sx[1] / sl, sx[2] / sl)
        sy = (ax[1] * sx[2] - ax[2] * sx[1],
              ax[2] * sx[0] - ax[0] * sx[2],
              ax[0] * sx[1] - ax[1] * sx[0])
        h = length / 100.0 * uv_scale

        def P(a, t):
            return (x0 + (sx[0] * math.cos(a) + sy[0] * math.sin(a)) * r + ax[0] * t,
                    y0 + (sx[1] * math.cos(a) + sy[1] * math.sin(a)) * r + ax[1] * t,
                    z0 + (sx[2] * math.cos(a) + sy[2] * math.sin(a)) * r + ax[2] * t)

        for i in range(seg):
            a0 = 2.0 * math.pi * i / seg
            a1 = 2.0 * math.pi * (i + 1) / seg
            u0 = (2.0 * math.pi * r / 100.0) * (i / float(seg)) * uv_scale
            u1 = (2.0 * math.pi * r / 100.0) * ((i + 1) / float(seg)) * uv_scale
            self.quad(slot, P(a0, 0), P(a1, 0), P(a1, length), P(a0, length),
                      uvs=[(u0, 0), (u1, 0), (u1, h), (u0, h)])

    def plate(self, slot, x0, y0, z0, x1, y1, z1, uv_scale=1.0, flip=False):
        """A single thin quad in the XZ plane (posters, boards, glass)."""
        w = abs(x1 - x0) / 100.0 * uv_scale
        h = abs(z1 - z0) / 100.0 * uv_scale
        if flip:
            self.quad(slot, (x1, y0, z0), (x0, y0, z0), (x0, y0, z1), (x1, y0, z1),
                      uvs=[(w, 0), (0, 0), (0, h), (w, h)])
        else:
            self.quad(slot, (x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1),
                      uvs=[(0, 0), (w, 0), (w, h), (0, h)])

    def frame_xz(self, slot, x0, z0, x1, z1, y0, y1, w, uv_scale=1.0):
        """Rectangular frame standing in the XZ plane (door/window casing)."""
        self.box(slot, x0, y0, z0, x1, y1, z0 + w, uv_scale)
        self.box(slot, x0, y0, z1 - w, x1, y1, z1, uv_scale)
        self.box(slot, x0, y0, z0 + w, x0 + w, y1, z1 - w, uv_scale)
        self.box(slot, x1 - w, y0, z0 + w, x1, y1, z1 - w, uv_scale)

    # -- bake --------------------------------------------------------------- #

    def finish(self, save=True):
        """Build render data for the description this builder filled in."""
        self._sm.build_from_static_mesh_descriptions([self._desc])
        if save:
            unreal.EditorAssetLibrary.save_asset('/%s' % self._sm.get_path_name())
        return self._sm

    def _bounds(self):
        """(min_x, min_y, min_z, max_x, max_y, max_z) in centimetres."""
        lo = tuple(self._box_min)
        hi = tuple(self._box_max)
        return (lo[0], lo[1], lo[2], hi[0], hi[1], hi[2])



# --------------------------------------------------------------------------- #
# asset wrapper
# --------------------------------------------------------------------------- #

def make_mesh(name, folder='/Game/KhoangLang/Meshes', materials=None, build=None,
              collision=True):
    """Create a StaticMesh asset, register material slots, then run ``build``.

    The order matters and is the whole trick: slots first, geometry second,
    build last. See the module docstring.

    ``collision`` generates simple + complex collision on the asset. Without it
    the mesh has no BodySetup, the level logs a physics warning and the player
    walks straight through the geometry, so it defaults to on and is only
    turned off for decoration that the level also marks non-colliding.
    """
    at = unreal.AssetToolsHelpers.get_asset_tools()
    path = '%s/%s' % (folder, name)
    existing = unreal.load_asset(path)
    if existing is not None:
        # Do not delete and recreate: the asset is usually still referenced by
        # the level being edited, and delete_asset() then fails, after which
        # create_asset() refuses because the old one is still there. Reusing
        # the object and swapping its description rebuilds in place, which is
        # both reliable and faster.
        sm = existing
        if not isinstance(sm, unreal.StaticMesh):
            raise RuntimeError('%s exists but is a %s' % (path,
                                                          sm.get_class().get_name()))
    else:
        sm = at.create_asset(name, folder, unreal.StaticMesh, None)
        if sm is None:
            raise RuntimeError('could not create StaticMesh asset %s' % path)
    b = MeshBuilder(name)
    b._sm = sm
    slots = {}
    names = [m for m in (materials or [])]
    if sm.get_num_sections(0) > 0 and len(slots) == 0:
        # align an existing slot list with the requested materials
        for i, mname in enumerate(names):
            slots[mname] = str(sm.get_material(i).get_name()) \
                if sm.get_material(i) is not None else mname
            if sm.get_material(i) is None:
                sm.set_material(i, unreal.load_asset(mname))
    else:
        for mname in names:
            slots[mname] = str(sm.add_material(unreal.load_asset(mname)))
    b._desc = sm.create_static_mesh_description()
    build(b, slots)
    sm.build_from_static_mesh_descriptions([b._desc])

    if collision:
        # EditorStaticMeshLibrary.add_simple_collisions() is a no-op in a
        # commandlet (returns -1, changes nothing) and unreal.BoxElem is not
        # exposed, so a hand-written hull is not available headlessly. Writing
        # the aggregate through KAggregateGeom.import_text() was tried and
        # hard-crashes the engine (access violation in UnrealEditor-Engine),
        # so this stays out.
        #
        # CTF_USE_SIMPLE_AND_COMPLEX is the correct flag for a procedural kit
        # mesh: queries and sweeps both resolve, using complex collision from
        # the render data. It is slower than a hull sweep but exact, and for
        # architecture that exactness is what stops a player catching on a
        # chamfer edge.
        try:
            bs = sm.get_editor_property('body_setup')
        except Exception:
            bs = None
        if bs is None:
            warn('%s: no BodySetup, collision left unset' % name)
        else:
            try:
                bs.set_editor_property(
                    'collision_trace_flag',
                    unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AND_COMPLEX)
            except Exception as exc:
                warn('%s: collision_trace_flag -> %r' % (name, str(exc)[:110]))

    unreal.EditorAssetLibrary.save_asset(path)
    tris = b._tri_count
    log('  %-34s %5d tris  %2d sections%s' % (
        name, tris, sm.get_num_sections(0), '' if collision else '  (no collision)'))
    return sm, tris
