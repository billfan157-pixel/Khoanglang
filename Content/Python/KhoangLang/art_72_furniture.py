"""Khoang Lang 02:17 - classroom furniture kit (art pass step 2).

Furniture for a rural Vietnamese primary school, c. 2002. The two pieces that
must be right are the pupil desk and the teacher's desk, because a Vietnamese
classroom is defined by them: a two-seat timber-top desk on a welded steel
frame, and a heavy teacher's desk with a raised lid and a knee hole.

Everything is modelled as a real object with legs, rails, aprons and a
worktop, because a desk built from one stretched cube is the clearest possible
signal that a level is a placeholder.

Run:  run_ue_script.ps1 -Script art_72_furniture.py
"""

import math
import os
import sys

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import kl_mesh as M  # noqa: E402

FOLDER = '/Game/KhoangLang/Meshes/Furniture'
MAT = '/Game/KhoangLang/MaterialsArt/'

WOOD = MAT + 'MI_ART_Wood'
WOOD_DK = MAT + 'MI_ART_WoodDark'
METAL = MAT + 'MI_ART_Metal'
RUST = MAT + 'MI_ART_MetalRust'
SHUT = MAT + 'MI_ART_ShutterBlue'
DOOR = MAT + 'MI_ART_DoorGreen'
PAPER = MAT + 'MI_ART_Paper'
CHALK = MAT + 'MI_ART_Chalk'
W_CLASS = MAT + 'MI_ART_WallClassroom'
STONE = MAT + 'MI_ART_Stone'
CONC = MAT + 'MI_ART_Concrete'
FLOOR = MAT + 'MI_ART_Floor'
SIGN = MAT + 'MI_ART_Sign'

BUILT = []


def add(name, mats, fn):
    sm, tris = M.make_mesh(name, FOLDER, mats, fn)
    BUILT.append((name, tris))
    return sm


# --------------------------------------------------------------------------- #
# pupil desk
# --------------------------------------------------------------------------- #

def desk_pupil():
    """Two-seat desk. 120 x 60 worktop at 70 cm, welded angle-iron frame,
    with a sloped book rest, an under-shelf and a pen groove.

    Origin at the floor, centred on the worktop.
    """
    def b(mb, s):
        wd, dk, mt = s[WOOD], s[WOOD_DK], s[METAL]
        hw, hd = 60.0, 30.0
        top = 70.0
        # worktop with a slight overhang and a rounded front edge
        mb.chamfer_box(wd, -hw, -hd, top - 5, hw, hd, top, 1.2, 0.75)
        # book rest: a shallow slope along the back
        mb.box(wd, -hw + 4, hd - 20, top, hw - 4, hd - 2, top + 3.0, 0.8)
        # pencil groove
        mb.box(dk, -hw + 6, hd - 22, top - 0.5, hw - 6, hd - 20, top + 0.4, 1.2)
        # frame: four legs, connected by an apron and a lower shelf
        for sx in (-1, 1):
            for sy in (-1, 1):
                lx = sx * (hw - 8)
                ly = sy * (hd - 7)
                mb.box(mt, lx - 2.2, ly - 2.2, 0, lx + 2.2, ly + 2.2, top - 5, 1.0)
        # apron rails
        for sy in (-1, 1):
            ly = sy * (hd - 7)
            mb.box(mt, -hw + 8, ly - 1.8, top - 16, hw - 8, ly + 1.8, top - 5, 1.0)
        for sx in (-1, 1):
            lx = sx * (hw - 8)
            mb.box(mt, lx - 1.8, -hd + 7, top - 16, lx + 1.8, hd - 7, top - 5, 1.0)
        # under-shelf, the detail that stops the desk looking like a table
        mb.box(dk, -hw + 10, -hd + 9, 24, hw - 10, hd - 9, 28, 0.9)
        # cross brace
        mb.box(mt, -hw + 10, -1.6, 14, hw - 10, 1.6, 20, 1.0)
    return b


def bench_pupil():
    """Companion bench: a plain timber plank on a steel frame, 100 x 28 at
    40 cm, with the ends turned down."""
    def b(mb, s):
        wd, mt = s[WOOD], s[METAL]
        hw, hd, top = 50.0, 14.0, 40.0
        mb.chamfer_box(wd, -hw, -hd, top - 4, hw, hd, top, 1.0, 0.8)
        for sx in (-1, 1):
            for sy in (-1, 1):
                lx = sx * (hw - 9)
                ly = sy * (hd - 5)
                mb.box(mt, lx - 2.0, ly - 2.0, 0, lx + 2.0, ly + 2.0, top - 4, 1.0)
        for sy in (-1, 1):
            ly = sy * (hd - 5)
            mb.box(mt, -hw + 9, ly - 1.6, 14, hw - 9, ly + 1.6, top - 4, 1.0)
    return b


def chair_pupil():
    """Timber classroom chair: slatted back, four tapered legs."""
    def b(mb, s):
        wd, dk = s[WOOD], s[WOOD_DK]
        seat = 44.0
        mb.chamfer_box(wd, -19, -19, seat - 3, 19, 19, seat, 1.0, 0.9)
        for (lx, ly) in ((-15, -15), (15, -15), (-15, 15), (15, 15)):
            mb.box(dk, lx - 1.8, ly - 1.8, 0, lx + 1.8, ly + 1.8, seat - 3, 1.0)
        # back posts continued upward
        for lx in (-15.0, 15.0):
            mb.box(wd, lx - 1.8, 13.0, seat - 3, lx + 1.8, 16.8, 82.0, 1.0)
        # back slats
        for z in (58.0, 70.0):
            mb.box(wd, -15, 13.2, z, 15, 16.6, z + 8, 0.9)
        # stretchers
        for sy in (-1, 1):
            mb.box(dk, -15, sy * 15 - 1.4, 16, 15, sy * 15 + 1.4, 19, 1.0)
    return b


# --------------------------------------------------------------------------- #
# teacher's desk
# --------------------------------------------------------------------------- #

def desk_teacher():
    """Teacher's desk: heavy timber carcase, a raised lid at the back, a knee
    hole, a drawer bank and a plinth. This is the room's focal object."""
    def b(mb, s):
        wd, dk = s[WOOD], s[WOOD_DK]
        W, D = 55.0, 30.0
        top = 76.0
        # worktop, overhanging
        mb.chamfer_box(wd, -W, -D, top - 4, W, D, top, 1.2, 0.7)
        # raised lid at the back with a lip
        mb.box(wd, -W, D - 12, top, W, D, top + 26, 0.7)
        mb.box(dk, -W, D - 13, top + 24, W, D - 12, top + 26, 1.0)
        # side panels
        for sx in (-1, 1):
            mb.box(wd, sx * W - sx * 3, -D + 2, 0, sx * W, D - 12, top - 4, 0.7)
        # drawer bank on the left, knee hole on the right
        mb.box(dk, -W + 3, -D + 4, top - 30, -12, D - 14, top - 4, 0.9)
        for i in range(3):
            z = top - 12 - i * 8.4
            mb.box(wd, -W + 4.5, -D + 3, z, -12 - 0.5, -D + 4.2, z + 6.6, 1.4)
            mb.cylinder(s[RUST], -24.0, -D + 3.6, z + 2.4, z + 4.2, 1.0, 6, 1.0,
                        axis='x')
        # modesty panel at the front
        mb.box(wd, -W + 3, -D + 1, 12, W - 3, -D + 3, top - 4, 0.7)
        # plinth
        mb.box(dk, -W + 4, -D + 5, 0, W - 4, D - 13, 8, 0.8)
    return b


def chair_teacher():
    """Teacher's chair: a padded vinyl seat on a steel tube frame."""
    def b(mb, s):
        mt, dk = s[METAL], s[WOOD_DK]
        seat = 46.0
        mb.chamfer_box(dk, -22, -22, seat - 5, 22, 22, seat, 1.6, 1.0)
        mb.box(s[DOOR], -22, -22, seat - 6, 22, 22, seat - 5, 1.0)
        for (lx, ly) in ((-18, -18), (18, -18), (-18, 18), (18, 18)):
            mb.box(mt, lx - 1.8, ly - 1.8, 0, lx + 1.8, ly + 1.8, seat - 5, 1.0)
        # back frame
        for lx in (-18.0, 18.0):
            mb.box(mt, lx - 1.8, 16, seat - 5, lx + 1.8, 19.6, 92, 1.0)
        mb.box(dk, -20, 16, 70, 20, 19.6, 92, 1.0)
        for sy in (-1, 1):
            mb.box(mt, -18, sy * 18 - 1.4, 18, 18, sy * 18 + 1.4, 21, 1.0)
    return b


def podium():
    """Teacher's podium: a raked timber reading stand on a panel base."""
    def b(mb, s):
        wd, dk = s[WOOD], s[WOOD_DK]
        mb.chamfer_box(dk, -28, -20, 0, 28, 20, 12, 1.2, 0.8)
        mb.box(wd, -28, -20, 12, 28, -12, 96, 0.7)
        # the raked top
        mb.box(wd, -28, -22, 96, 28, 14, 104, 0.7)
        mb.box(dk, -28, 14, 96, 28, 20, 108, 0.8)
        # paper stop
        mb.box(dk, -26, -20, 104, 26, -18, 106, 1.2)
    return b


# --------------------------------------------------------------------------- #
# classroom fittings
# --------------------------------------------------------------------------- #

def chalkboard():
    """Chalkboard: slate panel, timber surround, chalk tray, chalk stubs.
    340 x 140 on the wall, origin at the board centre."""
    def b(mb, s):
        wd, dk, ck = s[WOOD], s[WOOD_DK], s[CHALK]
        mb.box(dk, -178, 0, -78, 178, 4, 78, 0.8)          # backing board
        mb.box(ck, -168, 4, -66, 168, 6, 66, 0.7)           # slate
        for (x0, x1) in ((-178, -168), (168, 178)):        # stiles
            mb.box(wd, x0, 0, -78, x1, 7, 78, 0.9)
        for (z0, z1) in ((-78, -66), (66, 78)):            # rails
            mb.box(wd, -178, 0, z0, 178, 7, z1, 0.9)
        # chalk tray with a lip
        mb.box(wd, -180, 2, -88, 180, 16, -78, 0.9)
        mb.box(dk, -180, 13, -88, 180, 16, -82, 1.2)
        # chalk stubs and a duster
        for i in range(3):
            mb.box(ck, -120 + i * 26, 5, -86, -108 + i * 26, 9, -82, 2.0)
        mb.box(dk, 60, 5, -86, 96, 13, -78, 1.2)
    return b


def bookcase():
    """Open shelf unit with a few books, for the classroom wall."""
    def b(mb, s):
        wd, dk = s[WOOD], s[WOOD_DK]
        W, D, Hh = 80.0, 18.0, 170.0
        mb.box(wd, -W, 0, 0, W, D, 4, 0.8)                 # bottom
        for sx in (-1, 1):                                  # sides
            mb.box(wd, sx * W - sx * 3, 0, 0, sx * W, D, Hh, 0.8)
        mb.box(wd, -W, 0, Hh - 3, W, D, Hh, 0.8)            # top
        for i in range(3):                                  # shelves
            z = 52 + i * 52
            mb.box(wd, -W + 3, 0, z, W - 3, D - 1, z + 3, 0.8)
        # books, a couple of them leaning: a shelf of perfectly upright spines
        # is the giveaway that nobody ever looked at the asset
        lean = {1: 7.0, 4: -9.0, 5: 5.0}
        for i, x in enumerate((-60, -50, -40, 20, 30, 40)):
            z = 55 if i < 3 else 107
            c = s[SHUT] if i % 2 else s[DOOR]
            if i in lean:
                mb.box_rot_z(c, x + 4.5, D / 2.0, z, z + 30, 4.5, (D - 3) / 2.0,
                             lean[i], 1.4)
            else:
                mb.box(c, x, 2, z, x + 9, D - 3, z + 30, 1.4)
    return b


def coat_hook():
    """Wall rail with hooks, and one hanging apron."""
    def b(mb, s):
        wd, mt = s[WOOD], s[METAL]
        mb.box(wd, -45, 0, 0, 45, 4, 10, 0.9)
        for i in range(4):
            x = -34 + i * 22
            mb.cylinder(mt, x, 0, -12, 2, 1.2, 6, 1.0, axis='z', r_top=1.6)
        mb.box(s[DOOR], 12, 4, -46, 26, 7, -12, 0.9)        # a hung apron
    return b


def waste_bin():
    """Galvanised bin with a rolled rim."""
    def b(mb, s):
        mt = s[METAL]
        mb.cylinder(mt, 0, 0, 0, 44, 18, 12, 0.8, caps=False)
        mb.cylinder(mt, 0, 0, 0, 3, 18, 12, 0.8)
        mb.cylinder(mt, 0, 0, 44, 48, 19, 12, 0.8, caps=False, r_top=20)
    return b


def ceiling_fan():
    """Four-blade fan on a drop rod. Dead still, but its shadow is the point."""
    def b(mb, s):
        mt, wd = s[METAL], s[WOOD_DK]
        mb.cylinder(mt, 0, 0, -40, 0, 3.0, 8, 1.0)            # drop rod
        mb.cylinder(mt, 0, 0, -54, -40, 9.0, 12, 1.0)         # canopy
        mb.cylinder(mt, 0, 0, -47, -40, 3.5, 8, 1.0)          # motor boss
        for i in range(4):
            deg = 90.0 * i + 18.0
            r = 31.0
            cx = math.cos(math.radians(deg)) * r
            cy = math.sin(math.radians(deg)) * r
            mb.box_rot_z(wd, cx, cy, -48.0, -45.0, 22.0, 7.0, deg, 1.0)
    return b


def wall_map():
    """Framed map of Vietnam on the classroom wall."""
    def b(mb, s):
        wd, pa = s[WOOD_DK], s[PAPER]
        mb.box(wd, -80, 0, -60, 80, 4, 60, 0.8)
        mb.box(pa, -74, 4, -54, 74, 5, 54, 0.7)
    return b


def platform():
    """Teacher's platform step at the front of the room."""
    def b(mb, s):
        wd, dk = s[WOOD_DK], s[WOOD]
        mb.chamfer_box(wd, -130, -60, 0, 130, 60, 14, 1.5, 0.7)
        mb.box(dk, -130, -60, 14, 130, 60, 16, 0.8)
    return b


def main():
    M.log('=== art_72_furniture: classroom furniture ===')
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.make_directory(FOLDER)
    M.log('folder: %s' % FOLDER)

    add('SM_KL_Desk_Pupil', [WOOD, WOOD_DK, METAL], desk_pupil())
    add('SM_KL_Bench_Pupil', [WOOD, METAL], bench_pupil())
    add('SM_KL_Chair_Pupil', [WOOD, WOOD_DK], chair_pupil())
    add('SM_KL_Desk_Teacher', [WOOD, WOOD_DK, RUST], desk_teacher())
    add('SM_KL_Chair_Teacher', [METAL, WOOD_DK, DOOR], chair_teacher())
    add('SM_KL_Podium', [WOOD, WOOD_DK], podium())
    add('SM_KL_Chalkboard', [WOOD, WOOD_DK, CHALK, RUST], chalkboard())
    add('SM_KL_Bookcase', [WOOD, WOOD_DK, SHUT, DOOR], bookcase())
    add('SM_KL_Coat_Hook', [WOOD, METAL, DOOR], coat_hook())
    add('SM_KL_Waste_Bin', [METAL], waste_bin())
    add('SM_KL_Ceiling_Fan', [METAL, WOOD_DK], ceiling_fan())
    add('SM_KL_Wall_Map', [WOOD_DK, PAPER], wall_map())
    add('SM_KL_Platform', [WOOD_DK, WOOD], platform())

    total = sum(t for _, t in BUILT)
    M.log('furniture: %d meshes, %d triangles total' % (len(BUILT), total))
    M.log('=== art_72_furniture done ===')


main()
