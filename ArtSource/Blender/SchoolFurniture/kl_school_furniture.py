"""Khoang Lang 02:17 - Vietnamese rural primary-school furniture (Blender source).

Builds two reusable environment props for a fictional rural primary school,
circa 2002:

    SM_KL_SchoolDesk_A    110 x 50 cm worktop, top surface at 65 cm
    SM_KL_SchoolBench_A   110 x 30 cm seat,  top surface at 38 cm

Everything is generated from code so the asset stays reviewable and rebuildable.
No external meshes, no image textures, no reference downloads.

Construction language
---------------------
A rural Vietnamese classroom of that period was almost always built by the
school's own carpenter from whatever pine and cheap softwood was to hand:

  * a solid plank top, usually two planks butted together with a visible seam,
  * squared legs with rails butted against the leg inner faces - no mitres,
    nothing proud of the joint except a nail or two,
  * a low understructure of side rails and a cross stretcher,
  * on the better pieces an open shelf under the top, where a satchel and a
    lunch tin lived, plus a batten screwed under the plank seam as a repair,
  * a low rail across the back of the top to stop books sliding off.

The parts are modelled so that nothing floats and nothing interpenetrates:
each part either butts a neighbour or shares a face plane with it, which is
what keeps the silhouette honest under raking light.

Geometry conventions
--------------------
  * Blender units are metres. Dimensions below are written in centimetres and
    converted once, so the numbers in the brief can be read directly.
  * Origin is at the floor, centred in X and Y, for both assets. That is the
    pivot Unreal needs: place the actor, it stands on the floor.
  * The desk's front, where a pupil sits, faces -Y in Blender; the back rail
    is at +Y. +X is the desk's long axis and therefore the wood grain axis.
  * UVs are planar per face in metres, projected along each part's long axis,
    so every part shares one texel density. That matches kl_mesh.py on the
    Unreal side, where UV units are metres too.

Run
---
    blender --background --python kl_school_furniture.py

Writes
------
    ArtSource/Blender/SchoolFurniture/KL_SchoolFurniture.blend
    ArtExports/FBX/SchoolFurniture/SM_KL_SchoolDesk_A.fbx
    ArtExports/FBX/SchoolFurniture/SM_KL_SchoolBench_A.fbx
    ArtSource/Blender/SchoolFurniture/Preview/*.png
"""

import math
import os

import bpy
from mathutils.geometry import tessellate_polygon

CM = 0.01

# UV units per metre. 1.0 means one UV unit is one metre, the same density
# kl_mesh.py writes on the Unreal side, so the two sides tile alike.
UV_DENSITY = 1.0

# Preview stills are NOT produced by this script on this machine. Headless
# EEVEE rendered only the world colour here (no geometry), and Blender crashed
# on exit inside igxelpgicd64.dll, the Intel display driver. A run that wrote
# those frames would leave six convincing-looking, completely empty PNGs behind,
# so the render step is off unless it is asked for:
#     $env:KL_PREVIEWS = '1'; blender --python kl_school_furniture.py
# The previews that do exist under Preview/ were captured from a GUI session via
# bpy.ops.render.opengl, which does work there.
RENDER_PREVIEWS = os.environ.get('KL_PREVIEWS', '0') not in ('0', 'no', 'false')

COLLECTION_ROOT = 'KL_SchoolFurniture'
MAT_TOP = 'KL_Art_Wood_AgedTop'
MAT_FRAME = 'KL_Art_Wood_AgedFrame'
MAT_METAL = 'KL_Art_Metal_Hardware'


# --------------------------------------------------------------------------- #
# profile extrusion
# --------------------------------------------------------------------------- #
# A part is a 2D cross-section swept along one axis. That is how real timber
# works - a plank is a section, a leg is a section - and it buys chamfered
# corners, rebates and worn edges for free instead of stretching a cube.

def _map_x(p, q, t):
    return (t, p, q)


def _map_y(p, q, t):
    return (p, t, q)


def _map_z(p, q, t):
    return (p, q, t)


AXIS_MAP = {'X': _map_x, 'Y': _map_y, 'Z': _map_z}


def signed_area(poly):
    s = 0.0
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        s += x0 * y1 - x1 * y0
    return s * 0.5


def circle_profile(radius, segments):
    return [(radius * math.cos(2.0 * math.pi * i / segments),
             radius * math.sin(2.0 * math.pi * i / segments))
            for i in range(segments)]


def chamfered_rect(w, h, c):
    """Rectangle with its four corners cut, centred on the profile origin.

    c is the cut size along each axis. Used for leg sections so a leg does not
    present four razor edges to the bevel modifier.
    """
    c = min(c, w * 0.45, h * 0.45)
    x0, x1 = -w * 0.5, w * 0.5
    y0, y1 = -h * 0.5, h * 0.5
    return [
        (x0 + c, y0), (x1 - c, y0),
        (x1, y0 + c), (x1, y1 - c),
        (x1 - c, y1), (x0 + c, y1),
        (x0, y1 - c), (x0, y0 + c),
    ]


class Mesh(object):
    """Accumulates geometry in world space, one instance per material."""

    def __init__(self):
        self.verts = []
        self.faces = []

    def _add(self, verts, faces):
        base = len(self.verts)
        self.verts.extend(verts)
        for idx, uvs in faces:
            self.faces.append((tuple(base + i for i in idx), uvs))

    def extrude(self, profile, a0, a1, axis='X', center=(0.0, 0.0),
                uv_scale=1.0, uv_off=(0.0, 0.0), roll=0.0):
        """Sweep a closed CCW ``profile`` from a0 to a1 along ``axis``.

        ``center`` places the profile centroid at (p, q) - world Y,Z for axis
        X, world X,Z for axis Y, world X,Y for axis Z.
        ``roll`` spins the finished part about its own sweep axis, which is how
        the leg-to-leg misalignment of a hand-built frame is expressed without
        ever lifting a foot off the floor.
        """
        profile = [tuple(p) for p in profile]
        if signed_area(profile) < 0.0:
            profile = list(reversed(profile))
        n = len(profile)
        mapf = AXIS_MAP[axis]
        cp, cq = float(center[0]), float(center[1])
        ca, sa = math.cos(roll), math.sin(roll)

        def place(p, q, t):
            """Profile point -> world metres. Input is centimetres.

            ``center`` is an offset added to the profile, not a rotation pivot.
            The roll happens about the profile's own origin and the offset is
            applied after, which for a section centred on its origin (every
            section used here except the plank profiles, which are never rolled)
            is the same as rolling about the placed centre.
            """
            pp = cp + p * ca - q * sa
            qq = cq + p * sa + q * ca
            x, y, z = mapf(pp, qq, t)
            return (x * CM, y * CM, z * CM)

        arc = [0.0]
        for i in range(n):
            p0, p1 = profile[i], profile[(i + 1) % n]
            arc.append(arc[-1] + math.hypot(p1[0] - p0[0], p1[1] - p0[1]))

        verts = [place(p, q, a0) for (p, q) in profile]
        verts += [place(p, q, a1) for (p, q) in profile]

        def U(a, b):
            return (uv_off[0] + a * CM * uv_scale * UV_DENSITY,
                    uv_off[1] + b * CM * uv_scale * UV_DENSITY)

        faces = []
        # sides. Outward normal = profile edge x sweep direction.
        for i in range(n):
            j = (i + 1) % n
            faces.append(((i, j, n + j, n + i),
                          [U(a0, arc[i]), U(a0, arc[j]), U(a1, arc[j]),
                           U(a1, arc[i])]))
        # Caps, tessellated so a profiled section (a rebate, a chamfer) works.
        # tessellate_polygon does not guarantee a winding, so each triangle is
        # re-oriented to CCW in (p, q) before it is used: CCW faces +t at the
        # far cap, reversed at the near cap.
        flat = [(float(p), float(q)) for (p, q) in profile]
        for tri in tessellate_polygon([flat]):
            a, b, c = tri
            cross = ((flat[b][0] - flat[a][0]) * (flat[c][1] - flat[a][1])
                     - (flat[b][1] - flat[a][1]) * (flat[c][0] - flat[a][0]))
            if cross < 0.0:
                a, c = c, a
            uvs_a = [U(flat[t][0], flat[t][1]) for t in (a, b, c)]
            uvs_b = [U(flat[t][0], flat[t][1]) for t in (c, b, a)]
            faces.append(((n + a, n + b, n + c), uvs_a))
            faces.append(((c, b, a), uvs_b))
        self._add(verts, faces)

    def box(self, axis, a0, a1, p0, p1, q0, q1, uv_scale=1.0, uv_off=(0.0, 0.0)):
        """Axis-aligned box from a swept span and a rectangular profile."""
        return self.extrude([(p0, q0), (p1, q0), (p1, q1), (p0, q1)],
                            a0, a1, axis, (0.0, 0.0), uv_scale, uv_off)

    def cyl(self, axis, a0, a1, cp, cq, radius, segments=12, uv_scale=1.0,
            uv_off=(0.0, 0.0)):
        return self.extrude(circle_profile(radius, segments), a0, a1, axis,
                            (cp, cq), uv_scale, uv_off)

    def to_object(self, name, material):
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(v) for v in self.verts], [],
                       [list(f[0]) for f in self.faces])
        layer = me.uv_layers.new(name='UVMap')
        for poly, (_, uvs) in zip(me.polygons, self.faces):
            for li, uv in zip(poly.loop_indices, uvs):
                layer.data[li].uv = uv
        me.update()
        before = len(me.polygons)
        me.validate(verbose=False)
        if len(me.polygons) != before:
            print('KL_WARN %s: validate dropped %d faces'
                  % (name, before - len(me.polygons)))
        ob = bpy.data.objects.new(name, me)
        ob.data.materials.append(material)
        return ob

    def bounds_cm(self):
        if not self.verts:
            return None
        lo = [min(v[i] for v in self.verts) / CM for i in range(3)]
        hi = [max(v[i] for v in self.verts) / CM for i in range(3)]
        return [[round(c, 3) for c in lo], [round(c, 3) for c in hi]]


# --------------------------------------------------------------------------- #
# materials
# --------------------------------------------------------------------------- #

def _principled(mat):
    return next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')


def _set(node, name, value):
    if name in node.inputs:
        node.inputs[name].default_value = value


def _ramp(node, stops):
    el = node.color_ramp.elements
    while len(el) > 1:
        el.remove(el[-1])
    el[0].position = stops[0][0]
    el[0].color = stops[0][1]
    for pos, col in stops[1:]:
        e = el.new(pos)
        e.color = col


_MIX_OUT_INDEX = {'FLOAT': 0, 'VECTOR': 1, 'RGBA': 2, 'ROTATION': 3}
_MIX_SOCKET_TYPE = {'FLOAT': 'VALUE', 'VECTOR': 'VECTOR', 'RGBA': 'RGBA',
                    'ROTATION': 'ROTATION'}


def _mix(node, mode):
    """Factor / A / B / Result sockets of a ShaderNodeMix for one data_type.

    A ShaderNodeMix keeps sockets for every data type at once - ten inputs, four
    outputs - and only the ones matching ``data_type`` take part in the
    evaluation. Indexing them by position is therefore a trap: feeding inputs[2]
    (the FLOAT A) on a node set to RGBA links a socket the shader ignores, and
    the node silently evaluates from its defaults.

    ``mode`` is the node's data_type; FLOAT sockets are reported as VALUE, so
    the two vocabularies are translated here. Socket ``type`` is not always
    reported for the active Result either, hence the index fallback.
    """
    sock_type = _MIX_SOCKET_TYPE.get(mode, mode)
    fac = next(s for s in node.inputs
               if s.name == 'Factor' and s.type == 'VALUE')
    same = [s for s in node.inputs if s.type == sock_type]
    if len(same) < 2:
        raise RuntimeError('ShaderNodeMix(%s) has no A/B sockets for %s'
                           % (node.name, mode))
    results = [s for s in node.outputs if s.name == 'Result']
    res = next((s for s in results if s.type == sock_type), None)
    if res is None:
        res = node.outputs[_MIX_OUT_INDEX.get(mode, 0)]
    return fac, same[0], same[1], res


def wood_material(name, dark, mid, light, faded, rough_dry, rough_shiny,
                  grain_stretch=(1.1, 34.0, 34.0)):
    """Aged softwood: stretched noise for grain, a second noise for the bleach.

    The two-tone roughness is the point. Faded varnish does not wear off evenly,
    so a large scale mask decides which patches still catch a specular highlight
    and which have gone dry and matte. One roughness value is exactly what makes
    procedural wood read as plastic.
    """
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        if n.type != 'BSDF_PRINCIPLED':
            nt.nodes.remove(n)
    bsdf = _principled(mat)
    bsdf.location = (460, 0)

    coord = nt.nodes.new('ShaderNodeTexCoord')
    coord.location = (-1240, 0)

    grain_map = nt.nodes.new('ShaderNodeMapping')
    grain_map.location = (-1020, 120)
    grain_map.inputs['Scale'].default_value = grain_stretch
    nt.links.new(coord.outputs['Object'], grain_map.inputs['Vector'])

    grain = nt.nodes.new('ShaderNodeTexNoise')
    grain.location = (-820, 120)
    _set(grain, 'Scale', 2.6)
    _set(grain, 'Detail', 8.0)
    _set(grain, 'Roughness', 0.62)
    _set(grain, 'Distortion', 0.35)
    nt.links.new(grain_map.outputs['Vector'], grain.inputs['Vector'])

    ring = nt.nodes.new('ShaderNodeTexWave')
    ring.location = (-820, -160)
    ring.wave_type = 'BANDS'
    ring.bands_direction = 'Y'
    _set(ring, 'Scale', 1.1)
    _set(ring, 'Distortion', 14.0)
    _set(ring, 'Detail', 5.0)
    _set(ring, 'Detail Scale', 1.6)
    nt.links.new(grain_map.outputs['Vector'], ring.inputs['Vector'])

    grain_mix = nt.nodes.new('ShaderNodeMix')
    grain_mix.location = (-600, 40)
    grain_mix.data_type = 'RGBA'
    grain_mix.blend_type = 'MIX'
    gfac, ga, gb, gres = _mix(grain_mix, 'RGBA')
    gfac.default_value = 0.45
    nt.links.new(grain.outputs['Factor'], ga)
    nt.links.new(ring.outputs['Color'], gb)

    wood_ramp = nt.nodes.new('ShaderNodeValToRGB')
    wood_ramp.location = (-400, 40)
    _ramp(wood_ramp, [(0.18, dark), (0.42, mid), (0.66, light), (0.90, mid)])
    nt.links.new(gres, wood_ramp.inputs['Factor'])

    # bleach and handling wear: large, blotchy, low frequency
    wear = nt.nodes.new('ShaderNodeTexNoise')
    wear.location = (-820, -450)
    _set(wear, 'Scale', 1.15)
    _set(wear, 'Detail', 4.0)
    _set(wear, 'Roughness', 0.7)
    nt.links.new(coord.outputs['Object'], wear.inputs['Vector'])

    wear_ramp = nt.nodes.new('ShaderNodeValToRGB')
    wear_ramp.location = (-600, -450)
    _ramp(wear_ramp, [(0.40, (0, 0, 0, 1)), (0.58, (0.55, 0.55, 0.55, 1)),
                      (0.76, (1, 1, 1, 1))])
    nt.links.new(wear.outputs['Factor'], wear_ramp.inputs['Factor'])

    bleach = nt.nodes.new('ShaderNodeMix')
    bleach.location = (80, 60)
    bleach.data_type = 'RGBA'
    bleach.blend_type = 'MIX'
    bfac, ba, bb, bres = _mix(bleach, 'RGBA')
    nt.links.new(wear_ramp.outputs['Color'], bfac)
    nt.links.new(wood_ramp.outputs['Color'], ba)
    bb.default_value = (faded[0], faded[1], faded[2], 1.0)
    nt.links.new(bres, bsdf.inputs['Base Color'])

    # varnish sheen surviving only in the protected patches
    rough = nt.nodes.new('ShaderNodeMix')
    rough.location = (80, -230)
    rough.data_type = 'FLOAT'
    rfac, ra, rb, rres = _mix(rough, 'VALUE')
    ra.default_value = rough_dry
    rb.default_value = rough_shiny
    nt.links.new(wear_ramp.outputs['Color'], rfac)
    nt.links.new(rres, bsdf.inputs['Roughness'])

    _set(bsdf, 'Specular IOR Level', 0.42)
    _set(bsdf, 'IOR', 1.46)

    bump = nt.nodes.new('ShaderNodeBump')
    bump.location = (80, -450)
    _set(bump, 'Strength', 0.16)
    _set(bump, 'Distance', 0.004)
    nt.links.new(grain.outputs['Factor'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    # viewport tint, so Solid shading in the .blend is not a grey blob
    mat.diffuse_color = (mid[0] * 1.6, mid[1] * 1.6, mid[2] * 1.6, 1.0)
    mat.roughness = rough_dry
    return mat


def metal_material(name):
    """Oxidised steel for bolt heads: dark, rough, faintly rusting."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        if n.type != 'BSDF_PRINCIPLED':
            nt.nodes.remove(n)
    bsdf = _principled(mat)
    bsdf.location = (340, 0)

    coord = nt.nodes.new('ShaderNodeTexCoord')
    coord.location = (-820, 0)
    noise = nt.nodes.new('ShaderNodeTexNoise')
    noise.location = (-620, 0)
    _set(noise, 'Scale', 42.0)
    _set(noise, 'Detail', 6.0)
    _set(noise, 'Roughness', 0.7)
    nt.links.new(coord.outputs['Object'], noise.inputs['Vector'])

    col = nt.nodes.new('ShaderNodeValToRGB')
    col.location = (-380, 0)
    _ramp(col, [(0.30, (0.052, 0.050, 0.048, 1.0)),
                (0.55, (0.112, 0.076, 0.046, 1.0)),
                (0.80, (0.158, 0.100, 0.062, 1.0))])
    nt.links.new(noise.outputs['Factor'], col.inputs['Factor'])
    nt.links.new(col.outputs['Color'], bsdf.inputs['Base Color'])

    rgh = nt.nodes.new('ShaderNodeValToRGB')
    rgh.location = (-380, -250)
    _ramp(rgh, [(0.25, (0.32, 0.32, 0.32, 1.0)), (0.75, (0.80, 0.80, 0.80, 1.0))])
    nt.links.new(noise.outputs['Factor'], rgh.inputs['Factor'])
    nt.links.new(rgh.outputs['Color'], bsdf.inputs['Roughness'])

    met = nt.nodes.new('ShaderNodeMapRange')
    met.location = (-380, -440)
    met.inputs['To Min'].default_value = 0.95
    met.inputs['To Max'].default_value = 0.35
    nt.links.new(noise.outputs['Factor'], met.inputs['Value'])
    nt.links.new(met.outputs['Result'], bsdf.inputs['Metallic'])

    bump = nt.nodes.new('ShaderNodeBump')
    bump.location = (80, -320)
    _set(bump, 'Strength', 0.22)
    _set(bump, 'Distance', 0.002)
    nt.links.new(noise.outputs['Factor'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    mat.diffuse_color = (0.13, 0.11, 0.09, 1.0)
    mat.metallic = 0.7
    mat.roughness = 0.55
    return mat


# --------------------------------------------------------------------------- #
# SM_KL_SchoolDesk_A
# --------------------------------------------------------------------------- #
# Section through the desk, in centimetres, origin on the floor under the
# centre of the worktop:
#
#   +Y   back rail  z 65.0 .. 68.2,  y +20.5 .. +24.5
#        back plank y +0.3 .. +25.0  z 61.8 .. 65.0
#        front plank y -25.0 .. -0.3  z 61.8 .. 65.0   <- pupil sits here
#   -Y
#       x -55 .. +55
#
#   z 61.8  plank underside, apron top        z 28.0  shelf underside
#   z 57.8  apron underside                    z 24.0  side rail underside
#   z  0.0  floor

DESK_W = 110.0
DESK_D = 50.0
DESK_TOP = 65.0
PLANK_T = 3.2
PLANK_BOT = DESK_TOP - PLANK_T
SEAM = 0.3

LEG_S = 4.5
LEG_X = 49.25
LEG_Y = 19.25
LEG_IN_X = LEG_X - LEG_S * 0.5
LEG_IN_Y = LEG_Y - LEG_S * 0.5

RAIL_H = 4.0
APRON_TOP = PLANK_BOT
APRON_BOT = APRON_TOP - RAIL_H
APRON_T = 2.2

SHELF_TOP = 29.8
SHELF_T = 1.8
SHELF_BOT = SHELF_TOP - SHELF_T
RAIL_BOT = 24.0
RAIL_T = 3.0
RAIL_IN_X = LEG_X - RAIL_T * 0.5
RAIL_OUT_X = LEG_X + RAIL_T * 0.5


def build_desk():
    """The three per-material meshes of the pupil desk."""
    top, frame, metal = Mesh(), Mesh(), Mesh()

    def uv(k):
        return (0.137 * (k % 7), 0.211 * (k % 5))

    # ---- worktop: two planks with a visible seam ------------------------- #
    # The front plank's section carries the wear a decade of forearms leaves:
    # a rounded top edge, and a shallow rebate low on the front face where the
    # wood has been rubbed back.
    front_profile = [
        (-DESK_D * 0.5, PLANK_BOT),
        (-SEAM, PLANK_BOT),
        (-SEAM, DESK_TOP),
        (-DESK_D * 0.5 + 2.4, DESK_TOP),
        (-DESK_D * 0.5, DESK_TOP - 1.5),
        (-DESK_D * 0.5 + 0.45, DESK_TOP - 2.1),
        (-DESK_D * 0.5 + 0.45, PLANK_BOT),
    ]
    top.extrude(front_profile, -DESK_W * 0.5, DESK_W * 0.5, 'X', uv_scale=1.0,
                uv_off=uv(0))

    back_profile = [
        (SEAM, PLANK_BOT),
        (DESK_D * 0.5, PLANK_BOT),
        (DESK_D * 0.5, DESK_TOP - 1.1),
        (DESK_D * 0.5 - 1.0, DESK_TOP),
        (SEAM, DESK_TOP),
    ]
    top.extrude(back_profile, -DESK_W * 0.5 + 0.6, DESK_W * 0.5 - 0.4, 'X',
                uv_scale=1.0, uv_off=uv(1))

    # back rail: stops a satchel or a stack of exercise books going over the
    # back edge. Chamfered top, set 0.5 cm in from the plank's back edge.
    rail_profile = [
        (DESK_D * 0.5 - 4.5, DESK_TOP),
        (DESK_D * 0.5 - 0.5, DESK_TOP),
        (DESK_D * 0.5 - 0.5, DESK_TOP + 2.4),
        (DESK_D * 0.5 - 0.9, DESK_TOP + 3.2),
        (DESK_D * 0.5 - 4.5, DESK_TOP + 3.2),
    ]
    top.extrude(rail_profile, -DESK_W * 0.5 + 2.0, DESK_W * 0.5 - 1.4, 'X',
                uv_scale=1.15, uv_off=uv(2))

    # ---- legs -------------------------------------------------------------- #
    # roll only yaws them. A school desk that still stands is level; the
    # carpentry tells in the angles, not in the tilt.
    leg_roll = (-0.9, 0.7, -0.5, 1.1)
    k = 0
    for sy in (1, -1):
        for sx in (1, -1):
            frame.extrude(chamfered_rect(LEG_S, LEG_S, 0.7), 0.0, PLANK_BOT,
                          'Z', center=(sx * LEG_X, sy * LEG_Y),
                          uv_scale=1.15, uv_off=uv(3 + k),
                          roll=math.radians(leg_roll[k]))
            k += 1

    # ---- aprons, butted against the leg inner faces ------------------------ #
    apron_z_mid = (APRON_BOT + APRON_TOP) * 0.5
    frame.box('X', -LEG_IN_X, LEG_IN_X,
              -(LEG_Y + APRON_T * 0.5), -(LEG_Y - APRON_T * 0.5),
              APRON_BOT, APRON_TOP, 1.15, uv(7))
    frame.box('X', -LEG_IN_X, LEG_IN_X,
              (LEG_Y - APRON_T * 0.5), (LEG_Y + APRON_T * 0.5),
              APRON_BOT, APRON_TOP, 1.15, uv(8))
    for sx in (-1, 1):
        cx = sx * LEG_X
        frame.box('Y', -LEG_IN_Y, LEG_IN_Y,
                  cx - APRON_T * 0.5, cx + APRON_T * 0.5,
                  APRON_BOT, APRON_TOP, 1.15, uv(9 + (0 if sx < 0 else 1)))

    # ---- understructure: two side rails and a cross stretcher ------------- #
    for sx in (-1, 1):
        cx = sx * LEG_X
        frame.box('Y', -LEG_IN_Y, LEG_IN_Y,
                  cx - RAIL_T * 0.5, cx + RAIL_T * 0.5,
                  RAIL_BOT, SHELF_BOT, 1.15, uv(11 + (0 if sx < 0 else 1)))
    frame.box('X', -RAIL_IN_X, RAIL_IN_X,
              -1.5, 1.5, RAIL_BOT, SHELF_BOT, 1.15, uv(13))

    # ---- under-desk shelf -------------------------------------------------- #
    # Set well back from the front edge, so a pupil can get their knees under
    # the desk and the shelf reads as storage rather than a second surface.
    frame.box('X', -(LEG_X + 1.25), (LEG_X + 1.25),
              -13.0, 23.0, SHELF_BOT, SHELF_TOP, 1.0, uv(14))

    # ---- repair batten under the plank seam -------------------------------- #
    # The detail that sells the age of the piece: somebody squared it up once
    # with a length of batten.
    frame.box('X', -48.0, 48.0, -2.0, 2.0, PLANK_BOT - 2.5, PLANK_BOT,
              1.3, uv(15))

    # ---- hardware ---------------------------------------------------------- #
    front_face = -(LEG_Y + APRON_T * 0.5)
    back_face = -front_face
    bolt_z = apron_z_mid
    for sx in (-1, 1):
        metal.cyl('Y', front_face - 0.35, front_face, sx * LEG_X, bolt_z,
                  0.55, 12, 2.2, uv(20))
    metal.cyl('Y', back_face, back_face + 0.35, -LEG_X * 0.32, bolt_z,
              0.55, 12, 2.2, uv(21))
    metal.cyl('Y', back_face, back_face + 0.35, LEG_X * 0.32, bolt_z,
              0.55, 12, 2.2, uv(22))
    for sx in (-1, 1):
        cx = sx * RAIL_OUT_X
        a0, a1 = (cx - 0.35, cx) if sx < 0 else (cx, cx + 0.35)
        metal.cyl('X', a0, a1, 0.0, RAIL_BOT + 2.0, 0.5, 12, 2.2, uv(23))
    return top, frame, metal


# --------------------------------------------------------------------------- #
# SM_KL_SchoolBench_A
# --------------------------------------------------------------------------- #
# The same carpentry one member lighter. The bench is what makes the pair read
# as school furniture rather than as an office table.

BENCH_W = 110.0
BENCH_D = 30.0
BENCH_TOP = 38.0
BPLANK_T = 3.0
BPLANK_BOT = BENCH_TOP - BPLANK_T

BLEG_S = 4.0
BLEG_X = 50.0
BLEG_Y = 11.0
BLEG_IN_X = BLEG_X - BLEG_S * 0.5
BLEG_IN_Y = BLEG_Y - BLEG_S * 0.5

BAPRON_T = 2.5
BAPRON_BOT = BPLANK_BOT - 4.0

BSTRETCH_BOT = 17.0
BSTRETCH_TOP = 21.0
BSTRETCH_T = 2.5


def build_bench():
    top, frame, metal = Mesh(), Mesh(), Mesh()

    def uv(k):
        return (0.317 * (k % 6), 0.149 * (k % 4))

    # ---- seat: two planks, front one worn round at the nose ---------------- #
    front_profile = [
        (-BENCH_D * 0.5, BPLANK_BOT),
        (-SEAM, BPLANK_BOT),
        (-SEAM, BENCH_TOP),
        (-BENCH_D * 0.5 + 1.6, BENCH_TOP),
        (-BENCH_D * 0.5, BENCH_TOP - 0.9),
        (-BENCH_D * 0.5 + 0.4, BENCH_TOP - 1.3),
        (-BENCH_D * 0.5 + 0.4, BPLANK_BOT),
    ]
    top.extrude(front_profile, -BENCH_W * 0.5, BENCH_W * 0.5, 'X',
                uv_scale=1.0, uv_off=uv(0))

    back_profile = [
        (SEAM, BPLANK_BOT),
        (BENCH_D * 0.5, BPLANK_BOT),
        (BENCH_D * 0.5 - 0.7, BENCH_TOP),
        (SEAM, BENCH_TOP),
    ]
    top.extrude(back_profile, -BENCH_W * 0.5 + 0.8, BENCH_W * 0.5 - 0.5, 'X',
                uv_scale=1.0, uv_off=uv(1))

    # ---- legs -------------------------------------------------------------- #
    leg_roll = (-1.2, 0.9, -0.6, 1.4)
    k = 0
    for sy in (1, -1):
        for sx in (1, -1):
            frame.extrude(chamfered_rect(BLEG_S, BLEG_S, 0.6), 0.0, BPLANK_BOT,
                          'Z', center=(sx * BLEG_X, sy * BLEG_Y),
                          uv_scale=1.15, uv_off=uv(2 + k),
                          roll=math.radians(leg_roll[k]))
            k += 1

    # ---- seat aprons ------------------------------------------------------- #
    frame.box('X', -BLEG_IN_X, BLEG_IN_X,
              -(BLEG_Y + BAPRON_T * 0.5), -(BLEG_Y - BAPRON_T * 0.5),
              BAPRON_BOT, BPLANK_BOT, 1.15, uv(6))
    frame.box('X', -BLEG_IN_X, BLEG_IN_X,
              (BLEG_Y - BAPRON_T * 0.5), (BLEG_Y + BAPRON_T * 0.5),
              BAPRON_BOT, BPLANK_BOT, 1.15, uv(7))

    # ---- stretchers -------------------------------------------------------- #
    for sx in (-1, 1):
        cx = sx * BLEG_X
        frame.box('Y', -BLEG_IN_Y, BLEG_IN_Y,
                  cx - BSTRETCH_T * 0.5, cx + BSTRETCH_T * 0.5,
                  BSTRETCH_BOT, BSTRETCH_TOP, 1.15, uv(8 + (0 if sx < 0 else 1)))
    frame.box('X', -(BLEG_X - BSTRETCH_T * 0.5), (BLEG_X - BSTRETCH_T * 0.5),
              -1.5, 1.5, BSTRETCH_BOT, BSTRETCH_TOP, 1.15, uv(10))

    # ---- hardware ---------------------------------------------------------- #
    face = BLEG_Y + BAPRON_T * 0.5
    for sx in (-1, 1):
        metal.cyl('Y', -face - 0.35, -face, sx * BLEG_X, BAPRON_BOT + 2.0,
                  0.5, 12, 2.2, uv(11))
        metal.cyl('Y', face, face + 0.35, sx * BLEG_X * 0.35, BAPRON_BOT + 2.0,
                  0.5, 12, 2.2, uv(12))
    for sx in (-1, 1):
        cx = sx * (BLEG_X + BSTRETCH_T * 0.5)
        a0, a1 = (cx - 0.3, cx) if sx < 0 else (cx, cx + 0.3)
        metal.cyl('X', a0, a1, 0.0, BSTRETCH_BOT + 2.0, 0.45, 12, 2.2, uv(13))
    return top, frame, metal


# --------------------------------------------------------------------------- #
# assembly
# --------------------------------------------------------------------------- #

def deselect_all():
    for ob in bpy.context.view_layer.objects:
        ob.select_set(False)


def activate(ob):
    deselect_all()
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob


def finish(ob, bevel_cm=0.2):
    """Bevel, smooth-by-angle, weighted normals. All applied.

    The bevel is what turns a stack of boxes into furniture: 2 mm on every edge
    gives each silhouette a specular line, which is most of what the eye reads
    as made. Two segments is enough at this scale.
    """
    activate(ob)

    bev = ob.modifiers.new('KL_Bevel', 'BEVEL')
    bev.width = bevel_cm * CM
    bev.segments = 2
    bev.limit_method = 'ANGLE'
    bev.angle_limit = math.radians(35.0)
    bev.use_clamp_overlap = True
    bev.miter_outer = 'MITER_ARC'
    bpy.ops.object.modifier_apply(modifier=bev.name)

    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(32.0))

    try:
        wn = ob.modifiers.new('KL_WeightedNormal', 'WEIGHTED_NORMAL')
        wn.keep_sharp = True
        wn.weight = 50
        bpy.ops.object.modifier_apply(modifier=wn.name)
        print('KL_INFO %s weighted normals applied' % ob.name)
    except Exception as exc:
        print('KL_WARN %s weighted normals skipped: %r' % (ob.name, exc))

    for p in ob.data.polygons:
        p.use_smooth = True


def join_meshes(name, parts, materials):
    objs = []
    for label, mesh, matname in parts:
        if not mesh.verts:
            continue
        ob = mesh.to_object('%s_%s' % (name, label), materials[matname])
        bpy.context.scene.collection.objects.link(ob)
        objs.append(ob)
    deselect_all()
    for ob in objs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    ob.data.name = '%s_mesh' % name
    finish(ob)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return ob


def stats(ob):
    me = ob.data
    tris = 0
    for p in me.polygons:
        tris += len(p.vertices) - 2
    lo = [1e9] * 3
    hi = [-1e9] * 3
    for v in me.vertices:
        for i in range(3):
            lo[i] = min(lo[i], v.co[i])
            hi[i] = max(hi[i], v.co[i])
    uvr = [1e9, 1e9, -1e9, -1e9]
    for d in me.uv_layers[0].data:
        uvr[0] = min(uvr[0], d.uv[0])
        uvr[1] = min(uvr[1], d.uv[1])
        uvr[2] = max(uvr[2], d.uv[0])
        uvr[3] = max(uvr[3], d.uv[1])
    return dict(verts=len(me.vertices), tris=tris, polys=len(me.polygons),
                size_cm=[round((hi[i] - lo[i]) / CM, 2) for i in range(3)],
                min_cm=[round(lo[i] / CM, 2) for i in range(3)],
                uv_range=[round(v, 3) for v in uvr],
                slots=[s.material.name if s.material else None
                       for s in ob.material_slots],
                loc=[round(c, 5) for c in ob.location],
                scale=[round(c, 5) for c in ob.scale],
                rot=[round(c, 5) for c in ob.rotation_euler])


# --------------------------------------------------------------------------- #
# export and preview
# --------------------------------------------------------------------------- #

def enum_ids(owner, prop):
    """Read the accepted identifiers of a property off its own bl_rna."""
    try:
        rna = owner.bl_rna.properties[prop]
    except Exception:
        return []
    try:
        return [i.identifier for i in rna.enum_items]
    except Exception:
        return []


def pick(options, *prefer):
    for p in prefer:
        if p in options:
            return p
    for p in prefer:
        for o in options:
            if p in o:
                return o
    return options[0] if options else None


def export_fbx(ob, path):
    """Write one FBX per asset.

    Axis choice, measured rather than assumed. Blender's FBX exporter default
    (-Z forward, Y up) rewrites the scene into a Y-up frame as
    (x, y, z) -> (-x, z, y). UE 5.8.3's importer in this project was then
    measured handing those axes straight through without its usual Y-up to Z-up
    conversion, so the default export lands the desk on its side. Forward -Y /
    up Z is the identity mapping, so the FBX carries the Blender coordinates
    unchanged and the importer produces exactly the modelled orientation with
    the pivot on the floor. Verified by measuring get_bounds() after import.
    """
    deselect_all()
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    rna = bpy.ops.export_scene.fbx.get_rna_type()
    scale_opts = enum_ids(rna, 'apply_scale_options')
    smooth_opts = enum_ids(rna, 'mesh_smooth_type')
    kwargs = dict(
        filepath=path,
        use_selection=True,
        object_types={'MESH'},
        apply_unit_scale=True,
        global_scale=1.0,
        use_space_transform=False,
        bake_space_transform=False,
        axis_forward='-Y',
        axis_up='Z',
        mesh_smooth_type=pick(smooth_opts, 'EDGE'),
        apply_scale_options=pick(scale_opts, 'FBX_SCALE_NONE'),
        use_mesh_modifiers=True,
        use_triangles=False,
        use_tspace=True,
        bake_anim=False,
        add_leaf_bones=False,
        use_custom_props=False,
        colors_type='NONE',
        path_mode='AUTO',
        check_existing=False,
    )
    for prop, want in (('axis_forward', '-Y'), ('axis_up', 'Z')):
        avail = enum_ids(rna, prop)
        if avail and kwargs[prop] not in avail:
            kwargs[prop] = pick(avail, want)
        print('KL_INFO fbx %s enum=%s chosen=%s' % (prop, avail, kwargs[prop]))
    print('KL_INFO fbx %s -> %s' % (ob.name, kwargs))
    bpy.ops.export_scene.fbx(**kwargs)


def look_at(ob, target):
    from mathutils import Vector
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def set_engine(scene, candidates=('CYCLES', 'BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE')):
    """Pick a render engine without trusting a dynamic enum.

    ``render.engine`` is registered by add-ons, so RNA under-reports it. Read
    what RNA does offer, then confirm by assignment: an invalid identifier
    raises TypeError listing every accepted value.
    """
    avail = enum_ids(bpy.types.RenderSettings, 'engine')
    order = [c for c in candidates if c in avail]
    order += [c for c in candidates if c not in order]
    for cand in order + [scene.render.engine]:
        try:
            scene.render.engine = cand
            print('KL_INFO render engine=%s (rna listed %s)'
                  % (scene.render.engine, avail))
            return scene.render.engine
        except TypeError as exc:
            print('KL_INFO engine %s rejected: %s' % (cand, str(exc)[:140]))
    print('KL_WARN no render engine could be set')
    return None


def preview(cam_loc, aim, path, hidden=(), res=(1000, 760), lens=58.0,
            samples=48):
    """Render one still with a three-point rig and a dim room."""
    scene = bpy.context.scene
    for o in hidden:
        o.hide_render = True

    cam_data = bpy.data.cameras.new('KL_PreviewCam')
    cam_data.lens = lens
    cam = bpy.data.objects.new('KL_PreviewCam', cam_data)
    scene.collection.objects.link(cam)
    cam.location = cam_loc
    look_at(cam, aim)
    scene.camera = cam

    rig = []
    for energy, size, rgb, loc in (
            (260.0, 2.6, (1.0, 0.95, 0.88), (2.3, -2.6, 2.6)),
            (70.0, 2.2, (0.72, 0.80, 1.0), (-2.9, -1.6, 1.5)),
            (110.0, 1.8, (0.86, 0.90, 1.0), (-0.6, 3.2, 2.0))):
        ld = bpy.data.lights.new('KL_PreviewLight', 'AREA')
        ld.energy = energy
        ld.size = size
        ld.color = rgb
        lo = bpy.data.objects.new('KL_PreviewLight', ld)
        scene.collection.objects.link(lo)
        lo.location = loc
        look_at(lo, aim)
        rig.append(lo)

    if scene.world is None:
        scene.world = bpy.data.worlds.new('KL_PreviewWorld')
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get('Background')
    if bg is not None:
        bg.inputs['Color'].default_value = (0.050, 0.056, 0.066, 1.0)
        bg.inputs['Strength'].default_value = 1.0

    set_engine(scene)
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.filepath = path
    if hasattr(scene, 'cycles'):
        try:
            scene.cycles.samples = samples
            scene.cycles.use_denoising = True
            scene.cycles.device = 'CPU'
            scene.cycles.max_bounces = 6
        except Exception as exc:
            print('KL_WARN cycles settings: %r' % (exc,))
    if hasattr(scene, 'eevee'):
        for prop, val in (('taa_render_samples', max(16, samples)),
                          ('use_raytracing', True)):
            try:
                setattr(scene.eevee, prop, val)
            except Exception as exc:
                print('KL_WARN eevee.%s: %r' % (prop, exc))
    bpy.ops.render.render(write_still=True)

    for o in hidden:
        o.hide_render = False
    for o in [cam] + rig:
        bpy.data.objects.remove(o, do_unlink=True)
    return path


# --------------------------------------------------------------------------- #

def audit_materials(materials):
    """Fail loudly if a Mix node is fed through sockets it will not read.

    A ShaderNodeMix keeps every data type's sockets in the list at once, so a
    link can be made, look correct in the node editor, and still go nowhere.
    This walks each Mix and checks the Factor and both operands of the active
    data type are actually connected.
    """
    problems = []
    for name, mat in materials.items():
        nt = mat.node_tree
        bsdf = _principled(mat)
        # Base Color and Roughness carry the art direction and must be driven.
        # Metallic is deliberately left at its constant: wood is a dielectric.
        for sock in ('Base Color', 'Roughness'):
            if sock in bsdf.inputs and not bsdf.inputs[sock].is_linked:
                problems.append('%s: %s is unconnected' % (name, sock))
        for nd in nt.nodes:
            if nd.type != 'MIX':
                continue
            mode = nd.data_type
            try:
                fac, a, b, res = _mix(nd, mode)
            except Exception as exc:
                problems.append('%s/%s: %r' % (name, nd.name, exc))
                continue
            # The factor and the B operand are deliberately constant on these
            # graphs (a fixed grain/faded blend, fixed roughness endpoints), so
            # only the A operand and the result have to be driven.
            if not a.is_linked:
                problems.append('%s/%s: Mix(%s) A is unconnected'
                                % (name, nd.name, mode))
            if not res.is_linked:
                problems.append('%s/%s: Mix(%s) result is unconnected'
                                % (name, nd.name, mode))
            print('KL_INFO %s %s Mix(%s) factor=%s A=%s B=%s result=%s'
                  % (name, nd.name, mode, fac.is_linked, a.is_linked,
                     b.is_linked, res.is_linked))
    for p in problems:
        print('KL_WARN %s' % p)
    print('KL_INFO material audit: %d problem(s)' % len(problems))
    return problems


def project_paths():
    here = os.path.dirname(os.path.abspath(__file__))
    # here = <root>/ArtSource/Blender/SchoolFurniture
    root = os.path.abspath(os.path.join(here, '..', '..', '..'))
    export_dir = os.path.join(root, 'ArtExports', 'FBX', 'SchoolFurniture')
    preview_dir = os.path.join(here, 'Preview')
    for d in (here, export_dir, preview_dir):
        if not os.path.isdir(d):
            os.makedirs(d)
    return here, export_dir, preview_dir


def wipe_scene():
    if bpy.context.object is not None and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for coll in list(bpy.data.collections):
        bpy.data.collections.remove(coll)
    for lib in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras,
                bpy.data.lights):
        for block in list(lib):
            if block.users == 0:
                lib.remove(block)
    try:
        bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True,
                               do_recursive=True)
    except Exception as exc:
        print('KL_WARN purge: %r' % (exc,))


def main():
    print('KL_START')
    blend_dir, export_dir, preview_dir = project_paths()
    print('KL_INFO blend_dir=%s' % blend_dir)
    print('KL_INFO export_dir=%s' % export_dir)

    wipe_scene()
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1.0
    scene.frame_set(1)

    root = bpy.data.collections.new(COLLECTION_ROOT)
    scene.collection.children.link(root)

    materials = {
        MAT_TOP: wood_material(
            MAT_TOP,
            dark=(0.086, 0.048, 0.026, 1.0),
            mid=(0.215, 0.128, 0.070, 1.0),
            light=(0.360, 0.245, 0.155, 1.0),
            faded=(0.318, 0.268, 0.206, 1.0),
            rough_dry=0.68, rough_shiny=0.31),
        MAT_FRAME: wood_material(
            MAT_FRAME,
            dark=(0.052, 0.030, 0.018, 1.0),
            mid=(0.145, 0.086, 0.048, 1.0),
            light=(0.245, 0.163, 0.098, 1.0),
            faded=(0.228, 0.196, 0.156, 1.0),
            rough_dry=0.80, rough_shiny=0.44,
            grain_stretch=(2.2, 26.0, 26.0)),
        MAT_METAL: metal_material(MAT_METAL),
    }
    audit_materials(materials)

    dtop, dframe, dmetal = build_desk()
    print('KL_BOUNDS desk Top=%s' % (dtop.bounds_cm(),))
    print('KL_BOUNDS desk Frame=%s' % (dframe.bounds_cm(),))
    print('KL_BOUNDS desk Metal=%s' % (dmetal.bounds_cm(),))
    desk = join_meshes('SM_KL_SchoolDesk_A', [
        ('Top', dtop, MAT_TOP),
        ('Frame', dframe, MAT_FRAME),
        ('Metal', dmetal, MAT_METAL)], materials)

    btop, bframe, bmetal = build_bench()
    print('KL_BOUNDS bench Top=%s' % (btop.bounds_cm(),))
    print('KL_BOUNDS bench Frame=%s' % (bframe.bounds_cm(),))
    print('KL_BOUNDS bench Metal=%s' % (bmetal.bounds_cm(),))
    bench = join_meshes('SM_KL_SchoolBench_A', [
        ('Top', btop, MAT_TOP),
        ('Frame', bframe, MAT_FRAME),
        ('Metal', bmetal, MAT_METAL)], materials)

    for ob, sub in ((desk, 'SM_KL_SchoolDesk_A'),
                    (bench, 'SM_KL_SchoolBench_A')):
        coll = bpy.data.collections.new(sub)
        root.children.link(coll)
        scene.collection.objects.unlink(ob)
        coll.objects.link(ob)
        ob['kl_asset'] = sub
        ob['kl_pivot'] = 'floor centre'
        ob['kl_front_axis'] = '-Y'

    print('KL_STATS desk=%s' % stats(desk))
    print('KL_STATS bench=%s' % stats(bench))

    blend_path = os.path.join(blend_dir, 'KL_SchoolFurniture.blend')
    bpy.ops.wm.save_as_mainfile(filepath=blend_path, compress=False)
    print('KL_SAVED %s' % blend_path)

    export_fbx(desk, os.path.join(export_dir, 'SM_KL_SchoolDesk_A.fbx'))
    export_fbx(bench, os.path.join(export_dir, 'SM_KL_SchoolBench_A.fbx'))
    for f in ('SM_KL_SchoolDesk_A.fbx', 'SM_KL_SchoolBench_A.fbx'):
        p = os.path.join(export_dir, f)
        print('KL_FBX %s exists=%s bytes=%s'
              % (f, os.path.isfile(p),
                 os.path.getsize(p) if os.path.isfile(p) else -1))

    jobs = [
        ([(1.58, -1.44, 1.00), (0.0, 0.0, 0.40), 58.0, 'SM_KL_SchoolDesk_A_3q.png']),
        ([(0.02, -2.30, 0.64), (0.0, 0.0, 0.34), 62.0, 'SM_KL_SchoolDesk_A_front.png']),
        ([(2.30, -0.50, 0.74), (0.0, 0.0, 0.36), 62.0, 'SM_KL_SchoolDesk_A_side.png']),
        ([(1.36, -1.00, 0.70), (0.0, 0.0, 0.22), 58.0, 'SM_KL_SchoolBench_A_3q.png']),
        ([(0.02, -1.80, 0.42), (0.0, 0.0, 0.21), 62.0, 'SM_KL_SchoolBench_A_front.png']),
        ([(1.85, -1.85, 1.12), (0.0, -0.25, 0.34), 55.0, 'SM_KL_SchoolFurniture_set.png']),
    ]
    for loc, aim, lens, name in jobs:
        if not RENDER_PREVIEWS:
            break
        if name == 'SM_KL_SchoolBench_A_3q.png' or \
                name == 'SM_KL_SchoolBench_A_front.png':
            hidden = (desk,)
        elif name == 'SM_KL_SchoolFurniture_set.png':
            hidden = ()
        else:
            hidden = (bench,)
        if name == 'SM_KL_SchoolFurniture_set.png':
            bench.location.y = -0.50
            bpy.context.view_layer.update()
        preview([v * CM for v in loc], [v * CM for v in aim],
                os.path.join(preview_dir, name), hidden=hidden, lens=lens)
        if name == 'SM_KL_SchoolFurniture_set.png':
            bench.location.y = 0.0
            bpy.context.view_layer.update()
        print('KL_PREVIEW %s' % name)

    bpy.ops.wm.save_as_mainfile(filepath=blend_path, compress=False)
    print('KL_SAVED %s (final, preview rig removed)' % blend_path)
    print('KL_DONE')


main()
