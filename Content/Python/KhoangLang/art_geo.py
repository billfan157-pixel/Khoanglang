"""Khoang Lang 02:17 - art pass step 3: the rebuilt school.

Builds /Game/KhoangLang/Maps/Lvl_KL_School3_Art.  Lvl_KL_School3 is left
untouched as the known-good fallback.

Layout reads as a rural Vietnamese primary school rather than a corridor box:
  yard + gate + sign  ->  raised portico with columns  ->  entry hall
  ->  open corridor with classroom doors  ->  classroom 3 (the playable room)

All dimensions are centimetres.  Floor finish level is Z = 0; the yard sits
40 cm lower, the portico 45 cm higher, exactly as these buildings are built.
"""

import math
import os
import sys

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import kl_core as K  # noqa: E402
from kl_core import step, ok, warn, fail  # noqa: E402
from editor_toolset.toolsets import scene as SCENE  # noqa: E402
from editor_toolset.toolsets import actor as ACT  # noqa: E402

MAT = K.ROOT + '/MaterialsArt'
F_PROPS_ART = K.F_CORE + '/PropsArt'
MAP = K.ROOT + '/Maps/Lvl_KL_School3_Art'

MESH = {'Cube': '/Engine/BasicShapes/Cube',
        'Cylinder': '/Engine/BasicShapes/Cylinder',
        'Cone': '/Engine/BasicShapes/Cone',
        'Sphere': '/Engine/BasicShapes/Sphere',
        'Plane': '/Engine/BasicShapes/Plane'}

# --------------------------------------------------------------------------- #
# dimensions
# --------------------------------------------------------------------------- #

T = 20                       # wall thickness
CEIL_HALL = 320.0
CEIL_ROOM = 320.0
CEIL_ENTRY = 340.0

YARD_X0, YARD_X1 = -2400.0, -700.0
YARD_Y0, YARD_Y1 = -1600.0, 1600.0
YARD_Z = -40.0

PORT_X0, PORT_X1 = -700.0, -400.0
PORT_Y0, PORT_Y1 = -900.0, 900.0
PORT_Z = 45.0

ENTRY_X0, ENTRY_X1 = -400.0, 100.0
ENTRY_Y0, ENTRY_Y1 = -350.0, 350.0

CORR_X0, CORR_X1 = 100.0, 1000.0
CORR_Y0, CORR_Y1 = -260.0, 260.0

ROOM_X0, ROOM_X1 = 700.0, 1500.0
ROOM_Y0, ROOM_Y1 = 260.0, 1760.0

ROOM2_X0, ROOM2_X1 = 700.0, 1500.0
ROOM2_Y0, ROOM2_Y1 = -1760.0, -260.0

DOOR_X0, DOOR_X1 = 820.0, 960.0     # classroom 3 doorway
DOOR_H = 220.0

ROOF_Z0, ROOF_Z1 = 340.0, 380.0
BLD_X0, BLD_X1 = -760.0, 1560.0
BLD_Y0, BLD_Y1 = -1860.0, 1860.0

PLAYER_START = (-1750.0, 0.0, 60.0)
PLAYER_YAW = 0.0

# key evidence placements (inside classroom 3)
P_BOOK = (1100.0, 1500.0, 86.0)      # on the teacher's desk top
P_ROSTER = (1100.0, 1752.0, 178.0)   # pinned to the chalkboard
P_TAPE = (1010.0, 0.0, 150.0)        # PA head + deck at the corridor's far end
P_CORNER = (800.0, 1670.0, 120.0)     # the figure, revealed by NGHE LOC

STATS = {'actors': 0, 'meshes': 0, 'lights': 0, 'deco': 0}


# --------------------------------------------------------------------------- #
# placement helpers
# --------------------------------------------------------------------------- #

def quat(pitch, yaw, roll):
    sp, cp = math.sin(math.radians(pitch) / 2), math.cos(math.radians(pitch) / 2)
    sy, cy = math.sin(math.radians(yaw) / 2), math.cos(math.radians(yaw) / 2)
    sr, cr = math.sin(math.radians(roll) / 2), math.cos(math.radians(roll) / 2)
    return unreal.Quat(x=cr * sp * cy - sr * cp * sy,
                       y=-cr * sp * sy - sr * cp * cy,
                       z=cr * cp * sy - sr * sp * cy,
                       w=cr * cp * cy + sr * sp * sy)


def place_class(cls, name, loc, rot=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0)):
    t = unreal.Transform()
    t.set_editor_property('translation', unreal.Vector(*loc))
    t.set_editor_property('rotation', quat(*rot))
    t.set_editor_property('scale3d', unreal.Vector(*scale))
    a = SCENE.SceneTools.add_to_scene_from_class(cls, name, t)
    STATS['actors'] += 1
    if a is None:
        fail('spawn %s' % name)
    return a


def m(name):
    return '%s/%s' % (MAT, name)


def slab(name, x0, x1, y0, y1, z0, z1, mat, mesh='Cube', rot=(0.0, 0.0, 0.0),
         shadow=True, collision=True):
    a = place_class(unreal.StaticMeshActor.static_class(), 'ART_' + name,
                    ((x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0), rot,
                    (abs(x1 - x0) / 100.0, abs(y1 - y0) / 100.0, abs(z1 - z0) / 100.0))
    if a is None:
        return None
    c = K.find_comp(a, 'StaticMeshComponent')
    if c is None:
        return a
    c.set_editor_property('static_mesh', unreal.load_asset(MESH[mesh]))
    try:
        c.set_editor_property('override_materials', [unreal.load_asset(m(mat))])
    except Exception as exc:
        warn('%s material: %r' % (name, str(exc)[:60]))
    for prop, val in (('cast_shadow', shadow),
                      ('collision_enabled',
                       unreal.CollisionEnabled.QUERY_AND_PHYSICS if collision
                       else unreal.CollisionEnabled.NO_COLLISION),
                      ('can_ever_affect_navigation', False)):
        try:
            c.set_editor_property(prop, val)
        except Exception:
            pass
    STATS['meshes'] += 1
    if not collision:
        STATS['deco'] += 1
    ACT.ActorTools.set_label(a, 'ART_' + name)
    return a


def panel(name, center, size, mat, rot=(0.0, 0.0, 0.0), mesh='Plane', shadow=False):
    """A thin decorative quad: stains, glass, posters. No collision, no shadow."""
    a = place_class(unreal.StaticMeshActor.static_class(), 'ART_' + name, center,
                    rot, (size[0] / 100.0, size[1] / 100.0, 1.0))
    if a is None:
        return None
    c = K.find_comp(a, 'StaticMeshComponent')
    if c is None:
        return a
    c.set_editor_property('static_mesh', unreal.load_asset(MESH[mesh]))
    for prop, val in (('override_materials', [unreal.load_asset(m(mat))]),
                      ('cast_shadow', shadow),
                      ('collision_enabled', unreal.CollisionEnabled.NO_COLLISION),
                      ('can_ever_affect_navigation', False)):
        try:
            c.set_editor_property(prop, val)
        except Exception as exc:
            warn('%s.%s: %r' % (name, prop, str(exc)[:60]))
    if not shadow:
        try:
            c.set_editor_property('b_cast_dynamic_shadow', False)
        except Exception:
            pass
    STATS['meshes'] += 1
    STATS['deco'] += 1
    ACT.ActorTools.set_label(a, 'ART_' + name)
    return a


def light(kind, name, loc, intensity, rgb, radius=900.0, rot=(0, 0, 0),
          shadows=False, atten=2000.0, cone=(28.0, 60.0)):
    cls = {'Point': unreal.PointLight, 'Spot': unreal.SpotLight,
           'Directional': unreal.DirectionalLight}[kind]
    a = place_class(cls.static_class(), 'ART_' + name, loc, rot)
    if a is None:
        return None
    c = None
    for cc in ACT.ActorTools.get_components(a):
        if 'Light' in cc.get_class().get_name():
            c = cc
            break
    if c is None:
        warn('no light component on %s' % name)
        return a
    for prop, val in (('intensity', intensity),
                      ('light_color', unreal.Color(rgb[0], rgb[1], rgb[2])),
                      ('cast_shadows', shadows), ('visible', True),
                      ('affect_translucent_lighting', False)):
        try:
            c.set_editor_property(prop, val)
        except Exception as exc:
            warn('%s.%s: %r' % (name, prop, str(exc)[:50]))
    if kind == 'Point':
        K.comp_set(c, 'attenuation_radius', radius, name)
    elif kind == 'Spot':
        K.comp_set(c, 'attenuation_radius', atten, name)
        K.comp_set(c, 'inner_cone_angle', cone[0], name)
        K.comp_set(c, 'outer_cone_angle', cone[1], name)
    STATS['lights'] += 1
    ACT.ActorTools.set_label(a, 'ART_' + name)
    return a


def place_asset(asset_path, name, loc, rot=(0.0, 0.0, 0.0)):
    a = place_class(K.bp_class(asset_path), 'ART_' + name, loc, rot)
    if a is not None:
        ACT.ActorTools.set_label(a, 'ART_' + name)
    return a
