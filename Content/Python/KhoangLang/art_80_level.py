"""Khoang Lang 02:17 - hallway + classroom art pass (art pass step 4).

Builds /Game/KhoangLang/Maps/Lvl_KL_School3_Art from the modular kit.

Gameplay is preserved, not recreated. The plan keeps the Milestone 1
coordinates exactly, so the four interactables, the player start and the
game mode all sit where build_30_level.py put them and the existing
BP_KL_Prop_ART_* props keep working. Lvl_KL_School3 is left untouched as the
known-good fallback.

One deliberate fix: Milestone 1 punched the classroom doorway into the hall's
-Y wall while classroom 3 is on the +Y side, so the room was unreachable. The
opening is placed in the shared wall here. See docs/tech/ARTPASS_NOTES.md.

Performance budget, because this machine has an integrated GPU with ~2 GB:

  * 9 dynamic lights, of which only 3 cast shadows
  * no volumetrics, no SSR, motion blur and DOF off
  * exposure fixed rather than auto, so the grade does not pump
  * small clutter does not cast shadows

Run:  run_ue_script.ps1 -Script art_80_level.py
"""

import math
import os
import sys

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import kl_core as K          # noqa: E402
import kl_mesh as M          # noqa: E402
import kl_kit as KIT         # noqa: E402
from editor_toolset.toolsets import scene as SCENE  # noqa: E402
from editor_toolset.toolsets import actor as ACT     # noqa: E402

MAP = K.ROOT + '/Maps/Lvl_KL_School3_Art'
F_PROPS_ART = K.F_CORE + '/PropsArt'
ARCH = '/Game/KhoangLang/Meshes/Arch'
FURN = '/Game/KhoangLang/Meshes/Furniture'

# --------------------------------------------------------------------------- #
# plan - identical to the Milestone 1 graybox
# --------------------------------------------------------------------------- #

CORR_X0, CORR_X1 = -1000.0, -400.0        # entry corridor
CORR_Y0, CORR_Y1 = -110.0, 110.0
HALL_X0, HALL_X1 = -400.0, 2000.0         # main hall
HALL_Y0, HALL_Y1 = -200.0, 200.0
ROOM_X0, ROOM_X1 = 550.0, 1550.0          # classroom 3
ROOM_Y0, ROOM_Y1 = 200.0, 900.0
H = KIT.H                                  # 320
T = KIT.T                                  # 20

DOOR_X0, DOOR_X1 = 800.0, 940.0           # classroom doorway, 140 wide
DOOR_H = 220.0

WIN_Y = (350.0, 640.0)                    # classroom window centres
WIN_W = 140.0
WIN_Z0, WIN_Z1 = 90.0, 230.0

PLAYER_START = (-960.0, 0.0, 0.0)

# evidence placements, unchanged from Milestone 1
P_BOOK = (1050.0, 830.0, 82.0)
P_ROSTER = (1050.0, 884.0, 178.0)
P_TAPE = (1930.0, 0.0, 120.0)
P_CORNER = (1450.0, 790.0, 0.0)

STATS = {'meshes': 0, 'lights': 0, 'deco': 0, 'tris': 0}


# --------------------------------------------------------------------------- #
# placement helpers
# --------------------------------------------------------------------------- #

def quat(pitch, yaw, roll):
    sp, cp = math.sin(math.radians(pitch) / 2), math.cos(math.radians(pitch) / 2)
    sy, cy = math.sin(math.radians(yaw) / 2), math.cos(math.radians(yaw) / 2)
    sr, cr = math.sin(math.radians(roll) / 2), math.cos(math.radians(roll) / 2)
    return unreal.Quat(x=cr * sp * cy - sr * cp * sy,
                       y=-cr * sp * sy - sr * cp * cy,
                       z=cr * sp * cy - sr * sp * cy,
                       w=cr * cp * cy + sr * sp * sy)


def xform(loc, rot=(0.0, 0.0, 0.0)):
    t = unreal.Transform()
    t.set_editor_property('translation', unreal.Vector(*loc))
    t.set_editor_property('rotation', quat(*rot))
    t.set_editor_property('scale3d', unreal.Vector(1.0, 1.0, 1.0))
    return t


def put(name, mesh_path, loc, rot=(0.0, 0.0, 0.0), collision=True,
        shadow=True, scale=(1.0, 1.0, 1.0), mat=None):
    """Place one kit mesh as a StaticMeshActor.

    Collision is enabled per actor rather than baked into the asset so the same
    mesh can be used as a wall (solid) and as a piece of clutter (not solid)
    without duplicating the asset.
    """
    mesh = unreal.load_asset(mesh_path)
    if mesh is None:
        M.warn('missing mesh %s for %s' % (mesh_path, name))
        return None
    a = SCENE.SceneTools.add_to_scene_from_class(
        unreal.StaticMeshActor.static_class(), 'ART_' + name, xform(loc, rot))
    if a is None:
        M.warn('spawn failed: %s' % name)
        return None
    c = None
    for cc in ACT.ActorTools.get_components(a):
        if 'StaticMesh' in cc.get_class().get_name():
            c = cc
            break
    if c is None:
        M.warn('no mesh component on %s' % name)
        return a
    c.set_editor_property('static_mesh', mesh)
    if scale != (1.0, 1.0, 1.0):
        c.set_editor_property('relative_scale3d', unreal.Vector(*scale))
    if mat:
        m = unreal.load_asset(mat)
        if m:
            n = c.get_num_materials()
            c.set_editor_property('override_materials', [m] * max(1, n))
    for prop, val in (('cast_shadow', shadow),
                      ('can_ever_affect_navigation', False)):
        try:
            c.set_editor_property(prop, val)
        except Exception:
            pass
    try:
        c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS
                                if collision else
                                unreal.CollisionEnabled.NO_COLLISION)
    except Exception as exc:
        M.warn('%s collision: %r' % (name, str(exc)[:60]))
    ACT.ActorTools.set_label(a, 'ART_' + name)
    STATS['meshes'] += 1
    if not collision:
        STATS['deco'] += 1
    return a


def light(kind, name, loc, intensity, rgb, radius=900.0, rot=(0.0, 0.0, 0.0),
          shadows=False, cone=(28.0, 60.0)):
    cls = {'Point': unreal.PointLight, 'Spot': unreal.SpotLight,
           'Directional': unreal.DirectionalLight}[kind]
    a = SCENE.SceneTools.add_to_scene_from_class(cls.static_class(),
                                                 'ART_' + name, xform(loc, rot))
    if a is None:
        M.warn('light spawn failed: %s' % name)
        return None
    c = None
    for cc in ACT.ActorTools.get_components(a):
        if 'Light' in cc.get_class().get_name():
            c = cc
            break
    if c is None:
        return a
    for prop, val in (('intensity', intensity),
                      ('light_color', unreal.Color(*rgb)),
                      ('cast_shadows', shadows), ('visible', True)):
        try:
            c.set_editor_property(prop, val)
        except Exception as exc:
            M.warn('%s.%s: %r' % (name, prop, str(exc)[:50]))
    try:
        if kind == 'Point':
            c.set_editor_property('attenuation_radius', radius)
        elif kind == 'Spot':
            c.set_editor_property('attenuation_radius', radius)
            c.set_editor_property('inner_cone_angle', cone[0])
            c.set_editor_property('outer_cone_angle', cone[1])
            c.set_editor_property('source_radius', 12.0)
    except Exception:
        pass
    ACT.ActorTools.set_label(a, 'ART_' + name)
    STATS['lights'] += 1
    return a


# --------------------------------------------------------------------------- #
# shell
# --------------------------------------------------------------------------- #

def build_shell():
    M.log('--- shell ---')

    # ---- floors ---------------------------------------------------------- #
    put('Floor_Corr', '%s/%s' % (ARCH, KIT.floor(CORR_X1 - CORR_X0,
                                                 CORR_Y1 - CORR_Y0)),
        ((CORR_X0 + CORR_X1) / 2, 0, 0), shadow=False, collision=True)
    put('Floor_Hall', '%s/%s' % (ARCH, KIT.floor(HALL_X1 - HALL_X0,
                                                 HALL_Y1 - HALL_Y0)),
        ((HALL_X0 + HALL_X1) / 2, 0, 0), shadow=False)
    put('Floor_Room', '%s/%s' % (ARCH, KIT.floor(ROOM_X1 - ROOM_X0,
                                                 ROOM_Y1 - ROOM_Y0)),
        ((ROOM_X0 + ROOM_X1) / 2, (ROOM_Y0 + ROOM_Y1) / 2, 0), shadow=False)

    # ---- ceilings -------------------------------------------------------- #
    put('Ceil_Corr', '%s/%s' % (ARCH, KIT.ceiling(CORR_X1 - CORR_X0,
                                                  CORR_Y1 - CORR_Y0)),
        ((CORR_X0 + CORR_X1) / 2, 0, H), shadow=False, collision=False)
    put('Ceil_Hall', '%s/%s' % (ARCH, KIT.ceiling(HALL_X1 - HALL_X0,
                                                  HALL_Y1 - HALL_Y0)),
        ((HALL_X0 + HALL_X1) / 2, 0, H), shadow=False, collision=False)
    put('Ceil_Room', '%s/%s' % (ARCH, KIT.ceiling(ROOM_X1 - ROOM_X0,
                                                  ROOM_Y1 - ROOM_Y0)),
        ((ROOM_X0 + ROOM_X1) / 2, (ROOM_Y0 + ROOM_Y1) / 2, H),
        shadow=False, collision=False)

    # ---- hall south wall (y = -200), full run, no openings --------------- #
    run = HALL_X1 - HALL_X0
    put('Wall_HallS', '%s/%s' % (ARCH, KIT.wall(run)), ((HALL_X0 + HALL_X1) / 2,
                                                        HALL_Y0, 0))

    # ---- hall north wall (y = +200): the shared wall with classroom 3 ----- #
    # it carries the doorway, and behind x 550..1550 it is the classroom's own
    # north wall, so it is a classroom wall inside and a hall wall outside
    # 800..1200 of the run holds the 140 opening hard against its -X end
    before = DOOR_X0 - HALL_X0                       # 1200
    after = HALL_X1 - DOOR_X1                        # 1060
    put('Wall_HallN_A', '%s/%s' % (ARCH, KIT.wall(before)),
        ((HALL_X0 + DOOR_X0) / 2, HALL_Y1, 0))
    put('Wall_HallN_Door', '%s/%s' % (ARCH, KIT.wall_door(DOOR_X1 - DOOR_X0)),
        ((DOOR_X0 + DOOR_X1) / 2, HALL_Y1, 0))
    put('Wall_HallN_B', '%s/%s' % (ARCH, KIT.wall(after)),
        ((DOOR_X1 + HALL_X1) / 2, HALL_Y1, 0))

    # ---- hall west end, with the corridor opening ------------------------- #
    put('Wall_HallW_N', '%s/%s' % (ARCH, KIT.wall(HALL_Y1 - CORR_Y1)),
        (HALL_X0, (CORR_Y1 + HALL_Y1) / 2, 0), rot=(0.0, 90.0, 0.0))
    put('Wall_HallW_S', '%s/%s' % (ARCH, KIT.wall(CORR_Y0 - HALL_Y0)),
        (HALL_X0, (HALL_Y0 + CORR_Y0) / 2, 0), rot=(0.0, 90.0, 0.0))
    # header over the corridor opening, so the join is not a full-height slot
    put('Wall_HallW_Head', '%s/%s' % (ARCH, KIT.header(CORR_Y1 - CORR_Y0,
                                                       z0=DOOR_H)),
        (HALL_X0, 0, 0), rot=(0.0, 90.0, 0.0))

    # ---- hall east end ----------------------------------------------------- #
    put('Wall_HallE', '%s/%s' % (ARCH, KIT.wall(HALL_Y1 - HALL_Y0)),
        (HALL_X1, 0, 0), rot=(0.0, 90.0, 0.0))

    # ---- corridor --------------------------------------------------------- #
    put('Wall_CorrN', '%s/%s' % (ARCH, KIT.wall(CORR_X1 - CORR_X0)),
        ((CORR_X0 + CORR_X1) / 2, CORR_Y1, 0))
    put('Wall_CorrS', '%s/%s' % (ARCH, KIT.wall(CORR_X1 - CORR_X0)),
        ((CORR_X0 + CORR_X1) / 2, CORR_Y0, 0), rot=(0.0, 180.0, 0.0))
    put('Wall_CorrW', '%s/%s' % (ARCH, KIT.wall(CORR_Y1 - CORR_Y0)),
        (CORR_X0, 0, 0), rot=(0.0, 90.0, 0.0))

    # ---- classroom 3 ------------------------------------------------------ #
    put('Wall_RoomW', '%s/%s' % (ARCH, KIT.wall(ROOM_Y1 - ROOM_Y0, mat=KIT.W_CLASS)),
        (ROOM_X0, (ROOM_Y0 + ROOM_Y1) / 2, 0), rot=(0.0, 90.0, 0.0))
    put('Wall_RoomS', '%s/%s' % (ARCH, KIT.wall(ROOM_X1 - ROOM_X0, mat=KIT.W_CLASS)),
        ((ROOM_X0 + ROOM_X1) / 2, ROOM_Y1, 0), rot=(0.0, 180.0, 0.0))

    # east wall: alternate solid spans and window spans along Y
    cursor = ROOM_Y0
    for i, wy in enumerate(WIN_Y):
        a0 = wy - WIN_W / 2
        a1 = wy + WIN_W / 2
        if a0 - cursor > 6.0:
            put('Wall_RoomE_S%d' % i,
                '%s/%s' % (ARCH, KIT.wall(a0 - cursor, mat=KIT.W_CLASS)),
                (ROOM_X1, (cursor + a0) / 2, 0), rot=(0.0, 90.0, 0.0))
        put('Wall_RoomE_W%d' % i,
            '%s/%s' % (ARCH, KIT.wall(WIN_W, mat=KIT.W_CLASS, tag='WallWin',
                                      open_y0=WIN_Z0, open_y1=WIN_Z1)),
            (ROOM_X1, wy, 0), rot=(0.0, 90.0, 0.0))
        cursor = a1
    if ROOM_Y1 - cursor > 6.0:
        put('Wall_RoomE_SN', '%s/%s' % (ARCH, KIT.wall(ROOM_Y1 - cursor,
                                                      mat=KIT.W_CLASS)),
            (ROOM_X1, (cursor + ROOM_Y1) / 2, 0), rot=(0.0, 90.0, 0.0))


# --------------------------------------------------------------------------- #
# openings: doors, windows, shutters
# --------------------------------------------------------------------------- #

def build_openings():
    M.log('--- openings ---')
    dcx = (DOOR_X0 + DOOR_X1) / 2.0

    # classroom door: frame, threshold, leaf standing open into the room
    put('Door3_Frame', ARCH + '/SM_KL_Door_Frame', (dcx, HALL_Y1, 0))
    put('Door3_Leaf', ARCH + '/SM_KL_Door_Leaf',
        (DOOR_X0 + 4, HALL_Y1 + T - 2, 1.0), rot=(0.0, -68.0, 0.0))

    # corridor entrance: a pair of leaves standing open in the header opening
    put('DoorEntry_FrameW', ARCH + '/SM_KL_Door_Frame', (-400.0, 62.0, 0),
        rot=(0.0, -90.0, 0.0))
    put('DoorEntry_FrameE', ARCH + '/SM_KL_Door_Frame', (-400.0, -62.0, 0),
        rot=(0.0, 90.0, 0.0))
    put('DoorEntry_LeafN', ARCH + '/SM_KL_Door_Leaf', (-394.0, 8.0, 1.0),
        rot=(0.0, 74.0, 0.0))
    put('DoorEntry_LeafS', ARCH + '/SM_KL_Door_Leaf', (-394.0, -8.0, 1.0),
        rot=(0.0, -74.0, 0.0))

    # classroom windows: frame, glass, sill and two open shutter leaves
    for i, wy in enumerate(WIN_Y):
        put('Win%d_Frame' % i, ARCH + '/SM_KL_Window_Frame', (ROOM_X1 + T, wy,
                                                              WIN_Z0),
            rot=(0.0, 90.0, 0.0))
        put('Win%d_Glass' % i, ARCH + '/SM_KL_Window_Glass', (ROOM_X1 + T, wy,
                                                              WIN_Z0),
            rot=(0.0, 90.0, 0.0), collision=False, shadow=False)
        # shutters folded back against the reveal
        put('Win%d_ShutN' % i, ARCH + '/SM_KL_Shutter_Leaf',
            (ROOM_X1 + T, wy + WIN_W / 2 + 4, WIN_Z0), rot=(0.0, 118.0, 0.0),
            collision=False, shadow=False)
        put('Win%d_ShutS' % i, ARCH + '/SM_KL_Shutter_Leaf',
            (ROOM_X1 + T, wy - WIN_W / 2 - 4, WIN_Z0), rot=(0.0, -118.0, 0.0),
            collision=False, shadow=False)

    # corridor windows, high and small, on the south wall
    for i, cx in enumerate((-900.0, -700.0, -500.0)):
        put('WinCorr%d_Frame' % i, ARCH + '/SM_KL_Window_Frame', (cx, CORR_Y0 - 2,
                                                                 200.0),
            rot=(0.0, 180.0, 0.0), scale=(0.62, 1.0, 0.62), collision=False)
        put('WinCorr%d_Glass' % i, ARCH + '/SM_KL_Window_Glass', (cx, CORR_Y0 - 2,
                                                                 200.0),
            rot=(0.0, 180.0, 0.0), scale=(0.62, 1.0, 0.62), collision=False,
            shadow=False)


# --------------------------------------------------------------------------- #
# classroom furniture
# --------------------------------------------------------------------------- #

def build_classroom():
    M.log('--- classroom furniture ---')
    cx = (ROOM_X0 + ROOM_X1) / 2.0

    # teacher's platform and desk at the board end
    put('Room_Platform', FURN + '/SM_KL_Platform', (cx, 800.0, 0), shadow=False)
    put('Teacher_Desk', FURN + '/SM_KL_Desk_Teacher', (1050.0, 800.0, 14.0),
        rot=(0.0, 180.0, 0.0))
    put('Teacher_Chair', FURN + '/SM_KL_Chair_Teacher', (1050.0, 720.0, 14.0),
        rot=(0.0, 180.0, 0.0), shadow=False)
    put('Podium', FURN + '/SM_KL_Podium', (800.0, 830.0, 14.0),
        rot=(0.0, 12.0, 0.0))

    # chalkboard on the far wall, with the roster beside it
    put('Chalkboard', FURN + '/SM_KL_Chalkboard', (1080.0, ROOM_Y1 - 4, 175.0),
        rot=(0.0, 180.0, 0.0))
    put('WallMap', FURN + '/SM_KL_Wall_Map', (700.0, ROOM_Y1 - 4, 190.0),
        rot=(0.0, 180.0, 0.0), scale=(0.8, 1.0, 0.8), collision=False)

    # three rows of four double desks, facing the board
    r = 0
    for yy in (600.0, 460.0, 320.0):
        for xx in (700.0, 880.0, 1060.0, 1240.0):
            put('Desk%d_%d' % (r % 4, r // 4), FURN + '/SM_KL_Desk_Pupil',
                (xx, yy, 0), rot=(0.0, 180.0, 0.0))
            put('Bench%d_%d' % (r % 4, r // 4), FURN + '/SM_KL_Bench_Pupil',
                (xx, yy - 46.0, 0), rot=(0.0, 180.0, 0.0), shadow=False)
            r += 1
    M.log('  pupil desks: %d' % r)

    # a few chairs left on some of the desks' benches, and one fallen
    for (xx, yy, rz) in ((700.0, 300.0, 8.0), (1060.0, 440.0, -14.0),
                         (1240.0, 300.0, 22.0)):
        put('Chair_%d' % int(xx), FURN + '/SM_KL_Chair_Pupil', (xx, yy, 0),
            rot=(0.0, 180.0 + rz, 0.0), shadow=False)
    put('Chair_Fallen', FURN + '/SM_KL_Chair_Pupil', (940.0, 250.0, 20.0),
        rot=(0.0, -96.0, 0.0), shadow=False)

    # wall furniture
    put('Bookcase', FURN + '/SM_KL_Bookcase', (ROOM_X0 + 20, 640.0, 0),
        rot=(0.0, 90.0, 0.0))
    put('CoatHook', FURN + '/SM_KL_Coat_Hook', (ROOM_X0 + 4, 350.0, 160.0),
        rot=(0.0, 90.0, 0.0), collision=False, shadow=False)
    put('Bin', FURN + '/SM_KL_Waste_Bin', (ROOM_X1 - 40, 260.0, 0), shadow=False)
    put('Fan', FURN + '/SM_KL_Ceiling_Fan', (cx, 500.0, H - 2.0),
        collision=False, shadow=False)

    # the corner: stacked desks beside the seat, which is the reveal
    for i in range(3):
        put('CornerStack%d' % i, FURN + '/SM_KL_Desk_Pupil',
            (ROOM_X0 + 46, 856.0, i * 44.0), rot=(0.0, 84.0 + i * 4.0, 0.0),
            shadow=(i == 0))


# --------------------------------------------------------------------------- #
# corridor and hall dressing
# --------------------------------------------------------------------------- #

def build_corridor():
    M.log('--- corridor + hall dressing ---')
    # ceiling beams and the fluorescent run
    for i in range(6):
        x = -200.0 + i * 400.0
        put('Beam%d' % i, ARCH + '/SM_KL_Corridor_Beam', (x, 0, H - 34.0),
            shadow=False)
    for i, (x, dead) in enumerate(((-200.0, False), (200.0, True),
                                   (600.0, False), (1000.0, True),
                                   (1400.0, False), (1800.0, True))):
        put('Tube%d' % i, ARCH + '/SM_KL_Fluorescent', (x, 0, H - 12.0),
            rot=(0.0, 90.0, 0.0), collision=False,
            shadow=False, mat=KIT.MAT + ('MI_ART_TubeDead' if dead
                                         else 'MI_ART_Tube'))
    for i, x in enumerate((-800.0, -600.0, -450.0)):
        put('TubeCorr%d' % i, ARCH + '/SM_KL_Fluorescent', (x, 0, H - 12.0),
            collision=False, shadow=False,
            mat=KIT.MAT + ('MI_ART_TubeCold' if i == 1 else 'MI_ART_TubeDead'))

    # notice board, benches, the PA head at the east end
    put('NoticeBoard', ARCH + '/SM_KL_Notice_Board', (350.0, HALL_Y0 + 4, 180.0),
        rot=(0.0, 180.0, 0.0), collision=False)
    for i, x in enumerate((100.0, 700.0, 1500.0)):
        put('Bench%d' % i, ARCH + '/SM_KL_Bench_Hall', (x, HALL_Y0 + 40.0, 0),
            rot=(0.0, 180.0, 0.0), shadow=False)
    put('PA', ARCH + '/SM_KL_PA_Speaker', (1975.0, 0, 250.0),
        rot=(0.0, 90.0, 0.0))
    put('CoatHook_Hall', FURN + '/SM_KL_Coat_Hook', (1150.0, HALL_Y0 + 4, 160.0),
        rot=(0.0, 180.0, 0.0), collision=False, shadow=False)

    # stacked chairs against the east wall
    for i in range(3):
        put('ChairStack%d' % i, FURN + '/SM_KL_Chair_Pupil', (1900.0, 150.0,
                                                              i * 26.0),
            rot=(0.0, 90.0, 0.0), shadow=(i == 0))


# --------------------------------------------------------------------------- #
# lighting and grade
# --------------------------------------------------------------------------- #

def build_lighting():
    M.log('--- lighting ---')
    # Intensities are in the editor's physical-ish units. A corridor fitting
    # sits around 3000-6000 and a directional light around 0.1-0.3 for
    # moonlight; the first pass used values an order of magnitude too low and
    # the screenshots came back almost black.
    light('Directional', 'Moon', (0.0, 0.0, 1200.0), 0.22, (0.52, 0.64, 1.0),
          rot=(-46.0, 28.0, 0.0), shadows=True)

    # corridor: one working fitting at the far end only
    light('Point', 'L_Corr', (-560.0, 0.0, H - 24.0), 2600.0,
          (0.84, 0.90, 1.0), radius=1100.0)

    # hall: three fittings, the middle one shadowed
    for i, (x, inten, sh) in enumerate(((-150.0, 4200.0, True),
                                        (700.0, 3400.0, False),
                                        (1550.0, 2600.0, False))):
        light('Point', 'L_Hall%d' % i, (x, 0.0, H - 24.0), inten,
              (1.0, 0.90, 0.74), radius=1200.0, shadows=sh)

    # doorway spill, so the classroom reads as a lit room from the hall
    light('Point', 'L_Door', (870.0, HALL_Y1 + 40.0, 190.0), 1400.0,
          (1.0, 0.90, 0.76), radius=900.0)

    # classroom: two fittings
    for i, (y, inten, sh) in enumerate(((420.0, 4600.0, True),
                                        (740.0, 3800.0, False))):
        light('Point', 'L_Room%d' % i, (cx_room(), y, H - 24.0), inten,
              (1.0, 0.91, 0.78), radius=1400.0, shadows=sh)

    # moonlight through the two classroom windows, raking across the desks
    for i, wy in enumerate(WIN_Y):
        light('Spot', 'L_Shaft%d' % i, (ROOM_X1 + 220.0, wy, 190.0), 9000.0,
              (0.54, 0.66, 1.0), radius=2400.0, rot=(0.0, 118.0, 0.0),
              shadows=False, cone=(22.0, 50.0))

    # corridor windows
    light('Spot', 'L_ShaftCorr', (CORR_X0 + 60.0, 0.0, 200.0), 2200.0,
          (0.52, 0.64, 1.0), radius=1600.0, rot=(0.0, 62.0, 0.0),
          shadows=False, cone=(30.0, 66.0))

    # the corner. This is the whole reveal: a very low, very cold source that
    # should not be there. The prop Blueprint carries its own ART_CornerGlow
    # light, which the interact component switches on, so the figure appears
    # from nothing rather than fading in.
    light('Point', 'L_CornerHint', (1400.0, 760.0, 60.0), 260.0,
          (0.50, 0.62, 0.92), radius=520.0)


def cx_room():
    return (ROOM_X0 + ROOM_X1) / 2.0


def build_atmosphere():
    M.log('--- atmosphere ---')
    # height fog: a cheap depth cue, no volumetrics on this GPU
    a = SCENE.SceneTools.add_to_scene_from_class(
        unreal.ExponentialHeightFog.static_class(), 'ART_Fog', xform((0, 0, 150)))
    if a is not None:
        c = K.find_comp(a, 'ExponentialHeightFogComponent')
        if c is not None:
            for prop, val in (('fog_density', 0.010),
                              ('start_distance', 400.0),
                              ('fog_height_falloff', 0.18),
                              ('fog_cutoff_distance', 0.0)):
                try:
                    c.set_editor_property(prop, val)
                except Exception as exc:
                    M.warn('fog.%s: %r' % (prop, str(exc)[:60]))
            for prop, val in (('enable_volumetric_fog', False),):
                try:
                    c.set_editor_property(prop, val)
                except Exception:
                    pass
            try:
                c.set_fog_inscattering_color(unreal.LinearColor(0.10, 0.13, 0.22,
                                                                0.0))
            except Exception:
                pass
        ACT.ActorTools.set_label(a, 'ART_Fog')
        M.log('  height fog added, volumetrics off')

    # grade. Exposure is pinned rather than automatic: on this machine a fixed
    # exposure is both cheaper and more stable, and it stops the whole image
    # pumping when the player walks under a fitting.
    a = SCENE.SceneTools.add_to_scene_from_class(
        unreal.PostProcessVolume.static_class(), 'ART_Grade', xform((0, 0, 150)))
    if a is None:
        M.warn('post process volume spawn failed')
        return
    # APostProcessVolume keeps blend_weight / blend_radius / unbound and the
    # FPostProcessSettings block on the actor itself, not on a component.
    s = unreal.PostProcessSettings()
    applied, missing = 0, []

    def aem(name):
        for attr in dir(unreal.AutoExposureMethod):
            if name in attr.upper():
                return getattr(unreal.AutoExposureMethod, attr)
        raise RuntimeError('AutoExposureMethod.' + name)

    def try_set(prop, val):
        """Set a post-process property, tolerating the 5.8 type changes.

        UE 5.8 made color contrast/saturation/gamma Vector4 and vignette_size a
        Vector2f, so a scalar is tried first, then a single-component rewrite of
        whatever the property already holds. Only the first component is moved
        so the rest of each vector keeps its default.
        """
        nonlocal applied
        try:
            s.set_editor_property(prop, val)
            applied += 1
            return True
        except Exception:
            pass
        try:
            cur = s.get_editor_property(prop)
            if isinstance(cur, unreal.Vector4):
                s.set_editor_property(prop, unreal.Vector4(
                    val, cur.y, cur.z, cur.w))
                applied += 1
                return True
            if isinstance(cur, unreal.Vector2D):
                s.set_editor_property(prop, unreal.Vector2D(val, cur.y))
                applied += 1
                return True
        except Exception as exc:
            missing.append('%s (%s)' % (prop, str(exc)[:90]))
            return False
        missing.append(prop)
        return False

    # Value properties only. Exposure is left on manual in DefaultEngine.ini.
    SETTINGS = (
        ('color_offset', (0.006, 0.010, 0.020, 0.0)),
        ('color_gain', (0.97, 0.99, 1.04, 1.0)),
        ('color_contrast', 1.14),
        ('color_saturation', 0.80),
        ('color_gamma', 1.06),
        ('vignette_intensity', 0.38),
        ('vignette_size', 1.4),
        ('bloom_intensity', 0.45),
        ('bloom_threshold', 1.15),
        ('ambient_occlusion_intensity', 0.90),
        ('ambient_occlusion_radius', 60.0),
        ('ambient_occlusion_power', 1.5),
        ('ambient_occlusion_static_fraction', 0.40),
        ('motion_blur_amount', 0.0),
        ('depth_of_field_enabled', False),
        ('lens_flare_intensity', 0.0),
        ('auto_exposure_method', aem('HISTOGRAM')),
        ('auto_exposure_min_brightness', 0.02),
        ('auto_exposure_max_brightness', 2.50),
        ('auto_exposure_bias', 0.0),
        ('auto_exposure_apply_physical_camera_exposure', False),
        ('film_grain_intensity', 0.0),
    )
    for prop, val in SETTINGS:
        try_set(prop, val)
    try:
        a.set_editor_property('settings', s)
        ACT.ActorTools.set_label(a, 'ART_Grade')
        for prop, val in (('blend_weight', 1.0), ('blend_radius', 0.0),
                          ('unbound', True)):
            try:
                a.set_editor_property(prop, val)
            except Exception as exc:
                M.warn('  volume.%s: %r' % (prop, str(exc)[:60]))
        M.log('  post process: %d applied, %d unsupported' % (applied, len(missing)))
        if missing:
            M.warn('  unsupported: %s' % ', '.join(missing[:10]))
    except Exception as exc:
        M.warn('  assign post process: %r' % str(exc)[:120])


# --------------------------------------------------------------------------- #
# gameplay
# --------------------------------------------------------------------------- #

def build_gameplay():
    M.log('--- gameplay: props + player start ---')
    for asset, name, loc, rot in (
            (F_PROPS_ART + '/BP_KL_Prop_ART_AttBook', 'AttBook', P_BOOK,
             (0.0, 0.0, 12.0)),
            (F_PROPS_ART + '/BP_KL_Prop_ART_Roster', 'Roster', P_ROSTER,
             (0.0, 0.0, 0.0)),
            (F_PROPS_ART + '/BP_KL_Prop_ART_TapeDeck', 'TapeDeck', P_TAPE,
             (0.0, 0.0, 90.0)),
            (F_PROPS_ART + '/BP_KL_Prop_ART_Corner', 'Corner', P_CORNER,
             (0.0, 0.0, -28.0))):
        cls = K.bp_class(asset)
        if cls is None:
            M.warn('prop class missing: %s' % asset)
            continue
        a = SCENE.SceneTools.add_to_scene_from_class(cls, 'ART_' + name,
                                                     xform(loc, rot))
        if a is None:
            M.warn('place %s failed' % name)
        else:
            ACT.ActorTools.set_label(a, 'ART_' + name)
            M.log('  %s at %s' % (name, loc))

    ps = SCENE.SceneTools.add_to_scene_from_class(
        unreal.PlayerStart.static_class(), 'ART_PlayerStart',
        xform(PLAYER_START, (0.0, 0.0, 0.0)))
    if ps is None:
        M.warn('player start failed')
    else:
        ACT.ActorTools.set_label(ps, 'ART_PlayerStart')
        M.log('  player start %s' % (PLAYER_START,))

    # the figure must start hidden; the interact component reveals it
    world = unreal.EditorLevelLibrary.get_editor_world()
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if str(ACT.ActorTools.get_label(a)) == 'ART_Corner':
            for c in ACT.ActorTools.get_components(a):
                if 'StaticMesh' in c.get_class().get_name():
                    for prop, val in (('hidden_in_game', True),
                                      ('visible', False)):
                        try:
                            c.set_editor_property(prop, val)
                        except Exception:
                            pass
            M.log('  corner figure hidden at start')


def configure_world():
    M.log('--- world settings ---')
    world = unreal.EditorLevelLibrary.get_editor_world()
    ws = world.get_world_settings()
    for prop, val in (('default_game_mode', K.bp_class(K.F_PLAYER +
                                                      '/BP_KL_GameMode')),
                      ('kill_z', -400.0),
                      ('default_ambient_occlusion', 0.5)):
        try:
            ws.set_editor_property(prop, val)
            M.log('  %s set' % prop)
        except Exception as exc:
            M.warn('  %s: %r' % (prop, str(exc)[:70]))


# --------------------------------------------------------------------------- #

def main():
    M.log('=== art_80_level: hallway + classroom ===')
    K.make_folders()
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.make_directory(K.ROOT + '/Maps')

    if unreal.load_asset(MAP) is not None:
        unreal.EditorLevelLibrary.load_level(MAP)
        world = unreal.EditorLevelLibrary.get_editor_world()
        doomed = [a for a in unreal.GameplayStatics.get_all_actors_of_class(
            world, unreal.Actor)
            if str(ACT.ActorTools.get_label(a)).startswith('ART_')]
        for a in doomed:
            SCENE.SceneTools.remove_from_scene(a)
        M.log('cleared %d previous ART_ actors' % len(doomed))
    elif not unreal.EditorLevelLibrary.new_level(MAP):
        M.log('FAIL new_level %s' % MAP)
        return
    M.log('level %s ready' % MAP)

    build_shell()
    build_openings()
    build_classroom()
    build_corridor()
    build_lighting()
    build_atmosphere()
    build_gameplay()
    configure_world()

    KIT.report()
    M.log('totals: %d mesh actors, %d lights, %d non-colliding'
          % (STATS['meshes'], STATS['lights'], STATS['deco']))
    unreal.EditorAssetLibrary.save_asset(MAP)
    M.log('saved %s' % MAP)
    M.log('=== art_80_level done ===')


main()
