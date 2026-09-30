"""Khoang Lang 02:17 - modular architecture kit (step 1 of the art pass).

Builds the reusable shell pieces the hallway and classroom are assembled from.
The point of this file is reuse: a wall, a door and a window are authored once
and instanced everywhere, so the school reads as one building and later levels
cost nothing extra to dress.

Every piece is modelled around its own origin with a fixed nominal size, which
is how a modular kit has to work if it is going to tile.

Run:  run_ue_script.ps1 -Script art_70_kit.py
"""

import math
import os
import sys

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import kl_mesh as M  # noqa: E402

FOLDER = '/Game/KhoangLang/Meshes/Arch'
MAT = '/Game/KhoangLang/MaterialsArt/'

W_OGRE = MAT + 'MI_ART_WallOchre'
W_CLASS = MAT + 'MI_ART_WallClassroom'
W_EXT = MAT + 'MI_ART_WallExt'
W_WAIN = MAT + 'MI_ART_WallWainscot'
FLOOR = MAT + 'MI_ART_Floor'
CEIL = MAT + 'MI_ART_Ceiling'
WOOD = MAT + 'MI_ART_Wood'
WOOD_DK = MAT + 'MI_ART_WoodDark'
DOOR = MAT + 'MI_ART_DoorGreen'
SHUT = MAT + 'MI_ART_ShutterBlue'
METAL = MAT + 'MI_ART_Metal'
RUST = MAT + 'MI_ART_MetalRust'
STONE = MAT + 'MI_ART_Stone'
CONC = MAT + 'MI_ART_Concrete'
CHALK = MAT + 'MI_ART_Chalk'

# nominal module, centimetres
T = 20            # wall thickness
H = 320           # clear interior height
BAY = 400         # horizontal module
DOOR_W = 140
DOOR_H = 220

BUILT = []
NO_COLLISION = {
    # decoration only: the level marks these actors non-colliding too, so
    # generating a BodySetup for them would just waste memory
    'SM_KL_Window_Glass', 'SM_KL_Shutter_Leaf', 'SM_KL_Notice_Board',
    'SM_KL_Fluorescent', 'SM_KL_Downpipe',
}


def add(name, mats, fn):
    sm, tris = M.make_mesh(name, FOLDER, mats, fn,
                           collision=name not in NO_COLLISION)
    BUILT.append((name, tris))
    return sm


# --------------------------------------------------------------------------- #
# walls
# --------------------------------------------------------------------------- #

def wall_panel():
    """Blank wall module: 400 wide, 320 high, 20 thick. Origin at the centre
    of the base edge, running along +X, thickness along +Y."""
    def b(mb, s):
        w, wo = s[W_OGRE], s[W_WAIN]
        # upper wall
        mb.box(wo, -BAY / 2.0, 0, 110, BAY / 2.0, T, H, 0.5)
        # wainscot panelling below: a proud band plus a cap rail. This is the
        # detail that stops a school corridor reading as a cardboard box.
        mb.box(wo, -BAY / 2.0, -1.5, 0, BAY / 2.0, 0, 100, 0.5)
        mb.box(wo, -BAY / 2.0, -2.6, 100, BAY / 2.0, 1.5, 110, 0.5)
        # skirting
        mb.box(s[WOOD_DK], -BAY / 2.0, -2.2, 0, BAY / 2.0, 0.5, 14, 0.6)
        # vertical panel joints every 100 cm on the wainscot
        for x in (-100.0, 100.0):
            mb.box(wo, x - 1.2, -1.8, 14, x + 1.2, 0.2, 100, 0.6)
    return b


def wall_pier():
    """Narrow pier between openings (door jamb / window jamb filler)."""
    def b(mb, s):
        w, wo = s[W_OGRE], s[W_WAIN]
        mb.box(wo, -60, 0, 0, 60, T, H, 0.5)
        mb.box(wo, -60, -1.5, 0, 60, 0, 100, 0.5)
        mb.box(wo, -60, -2.6, 100, 60, 1.5, 110, 0.5)
        mb.box(s[WOOD_DK], -60, -2.2, 0, 60, 0.5, 14, 0.6)
    return b


def wall_lintel():
    """Header panel spanning above a door or window opening."""
    def b(mb, s):
        mb.box(s[W_OGRE], -BAY / 2.0, 0, 0, BAY / 2.0, T, 80, 0.5)
    return b


def wall_exterior():
    """Outer wall leaf: rendered plaster both sides, no wainscot."""
    def b(mb, s):
        mb.box(s[W_EXT], -BAY / 2.0, 0, 0, BAY / 2.0, T, H + 40, 0.42)
    return b


# --------------------------------------------------------------------------- #
# floor + ceiling
# --------------------------------------------------------------------------- #

def floor_tile():
    """400x400 floor module with a shallow recess so the joints read."""
    def b(mb, s):
        mb.box(s[FLOOR], -200, -200, -6, 200, 200, 0, 0.34)
        # the joint line: a very slightly darker inset frame
        mb.box(s[CONC], -200, -200, -6, 200, -192, 0, 0.6)
        mb.box(s[CONC], -200, 192, -6, 200, 200, 0, 0.6)
        mb.box(s[CONC], -200, -192, -6, -192, 192, 0, 0.6)
        mb.box(s[CONC], 192, -192, -6, 200, 192, 0, 0.6)
    return b


def ceiling_panel():
    """Ceiling module with a shallow coffer, plus a beam edge."""
    def b(mb, s):
        mb.box(s[CEIL], -200, -200, 0, 200, 200, 12, 0.4)
        mb.box(s[CEIL], -186, -186, 12, 186, 186, 20, 0.4)
    return b


def corridor_beam():
    """Cross beam under the corridor ceiling: reads as a real structure and
    gives the fluorescent tubes something to hang from."""
    def b(mb, s):
        mb.chamfer_box(s[CONC], -200, -26, 0, 200, 26, 34, 1.5, 0.5)
    return b


# --------------------------------------------------------------------------- #
# doors
# --------------------------------------------------------------------------- #

def door_frame():
    """Casing around a 140x220 opening. Origin at the floor, opening centre."""
    def b(mb, s):
        w = 12.0
        h = DOOR_W / 2.0
        wd = s[WOOD]
        # jambs, chamfered so the opening edge catches light
        mb.chamfer_box(wd, -h - w, -2, 0, -h, T + 2, DOOR_H + w, 1.2, 0.7)
        mb.chamfer_box(wd, h, -2, 0, h + w, T + 2, DOOR_H + w, 1.2, 0.7)
        # head
        mb.chamfer_box(wd, -h - w, -2, DOOR_H, h + w, T + 2, DOOR_H + w, 1.2, 0.7)
        # reveal lining so the opening is not a hole in a plane
        mb.box(s[WOOD_DK], -h, T, 0, h, T + 1.5, DOOR_H, 0.7)
        # threshold
        mb.box(s[STONE], -h, -2, 0, h, T + 2, 2.0, 0.6)
    return b


def door_leaf():
    """Panelled door leaf, 136 x 216 x 4.5, hinged at the -X edge.

    Four recessed panels plus a moulded rail, because a flat slab is the single
    most obvious giveaway that a door is a placeholder.
    """
    def b(mb, s):
        wd, dk = s[WOOD], s[WOOD_DK]
        W, Hh, Tt = 136.0, 216.0, 4.5
        mb.chamfer_box(wd, 0, 0, 0, W, Tt, Hh, 1.0, 0.8)
        # stiles down each side
        mb.box(dk, 0, Tt, 0, 16, Tt + 1.0, Hh, 0.9)
        mb.box(dk, W - 16, Tt, 0, W, Tt + 1.0, Hh, 0.9)
        # three panels, recessed
        spans = ((24.0, 84.0), (94.0, 132.0), (142.0, Hh - 24.0))
        for (z0, z1) in spans:
            mb.box(dk, 16, Tt, z0, W - 16, Tt + 1.0, z1, 0.9)
            # sunken field inside the raised panel border
            mb.box(wd, 24, Tt + 1.0, z0 + 8, W - 24, Tt - 0.2, z1 - 8, 0.9)
        # handle + backplate
        mb.cylinder(s[RUST], W - 34, Tt + 5.0, 96.0, 104.0, 3.0, 8, 1.0,
                    axis='x')
        mb.box(s[RUST], W - 42, Tt, 92.0, W - 32, Tt + 1.2, 108.0, 1.2)
    return b


def vent_grille():
    """Wall vent: louvred metal, for corridor and classroom detail."""
    def b(mb, s):
        mt = s[RUST]
        mb.box(mt, -30, 0, -20, 30, 4, 20, 1.0)
        for i in range(5):
            z = -16 + i * 8
            mb.box(mt, -27, 0, z, 27, 4, z + 4.5, 1.2)
    return b


# --------------------------------------------------------------------------- #
# windows
# --------------------------------------------------------------------------- #

def window_frame():
    """Timber window frame for a 140 x 150 opening, with a mullion cross and a
    projecting sill. Origin at the opening centre, sill at Z=0."""
    def b(mb, s):
        wd = s[WOOD]
        ow, oh, w = 140.0, 150.0, 9.0
        hw = ow / 2.0
        mb.box(wd, -hw - w, 0, 0, hw + w, 8, oh + w, 0.9)
        # the reveal, so daylight has an edge to die against
        mb.box(s[WOOD_DK], -hw, 8, 0, hw, T, oh, 0.8)
        # mullion cross
        mb.box(wd, -3, 3, 0, 3, 8, oh, 0.9)
        mb.box(wd, -hw, 3, oh / 2.0 - 3, hw, 8, oh / 2.0 + 3, 0.9)
        # sill, projecting into the room and sloping water off
        mb.chamfer_box(wd, -hw - 14, -8, -6, hw + 14, 8, 0, 1.0, 0.9)
        mb.box(s[WOOD_DK], -hw - 14, -8, -8, hw + 14, 6, -6, 0.9)
    return b


def window_glass():
    """Single dusty pane. Kept as its own mesh so the material can be a
    separate translucent surface."""
    def b(mb, s):
        mb.plate(s[METAL], -68, 4, 2, 68, 4, 148, 0.5)
    return b


def shutter_leaf():
    """Blue louvred timber shutter, one leaf, 70 wide x 150 high."""
    def b(mb, s):
        sh = s[SHUT]
        W, Hh, Tt = 70.0, 150.0, 3.0
        mb.box(sh, 0, 0, 0, W, Tt, Hh, 0.9)
        # louvres, angled so they catch a highlight
        n = 9
        for i in range(n):
            z = 6 + i * ((Hh - 12) / float(n))
            mb.box(sh, 5, Tt, z, W - 5, Tt + 2.4, z + 7, 1.0)
        # ledges
        mb.box(sh, 0, Tt, 0, W, Tt + 3.0, 5, 1.0)
        mb.box(sh, 0, Tt, Hh - 5, W, Tt + 3.0, Hh, 1.0)
    return b


# --------------------------------------------------------------------------- #
# trim and fittings
# --------------------------------------------------------------------------- #

def pa_speaker():
    """Wall-mounted PA horn on a bracket: the tape-deck landmark."""
    def b(mb, s):
        mt, ru = s[METAL], s[RUST]
        mb.box(mt, -6, -6, -40, 6, 6, 0, 1.0)                 # bracket
        mb.cylinder(mt, 0, 0, 0, 46, 9, 12, 1.0, axis='x', r_top=34)
        mb.cylinder(ru, 46, 0, 0, 8, 34, 16, 1.0, axis='x', r_top=30)
        mb.box(ru, -22, -22, -74, 22, 22, -40, 0.8)           # the amp body
        mb.cylinder(s[WOOD_DK], 0, 0, -84, -74, 2.5, 8, 1.0)  # aerial
    return b


def notice_board():
    """Cork notice board with a timber frame and a paper layer."""
    def b(mb, s):
        wd, pa = s[WOOD_DK], s[MAT + 'MI_ART_Paper']
        mb.box(wd, -90, 0, -45, 90, 5, 45, 0.9)
        mb.box(pa, -82, 4, -37, 82, 5.5, 37, 0.9)
        mb.box(wd, -90, -2, 43, 90, 6, 47, 0.9)               # top rail
    return b


def bench_hall():
    """Corridor bench: timber slats on a steel frame."""
    def b(mb, s):
        wd, mt = s[WOOD], s[WOOD_DK]
        for i in range(3):
            y = -22 + i * 18
            mb.box(wd, -90, y, 40, 90, y + 14, 46, 0.9)
        for x in (-78.0, 78.0):
            mb.box(mt, x - 4, -24, 0, x + 4, 24, 42, 0.9)
        mb.box(mt, -82, -4, 6, 82, 4, 12, 0.9)
    return b


def fluorescent_tube():
    """Corridor luminaire: steel channel plus a glass tube."""
    def b(mb, s):
        mt, ru = s[METAL], s[MAT + 'MI_ART_Tube']
        mb.box(mt, -60, -9, -7, 60, 9, 0, 1.0)
        mb.cylinder(ru, 0, 0, -6, 6, 4.0, 10, 1.0, axis='x')
        for x in (-58.0, 58.0):
            mb.box(mt, x - 3, -7, -12, x + 3, 7, -6, 1.0)
    return b


def water_tank():
    """Roof water tank - the detail that says 'Vietnamese school' instantly."""
    def b(mb, s):
        ru, mt = s[RUST], s[METAL]
        mb.cylinder(ru, 0, 0, 0, 130, 95, 16, 0.5)
        mb.cylinder(ru, 0, 0, 130, 142, 95, 16, 0.5, r_top=70)
        mb.box(mt, -105, -5, 0, 105, 5, 10, 0.8)               # base frame
    return b


def downpipe():
    """Rainwater downpipe with a hopper head and a shoe."""
    def b(mb, s):
        mt = s[METAL]
        mb.cylinder(mt, 0, 0, 0, 300, 6.0, 10, 1.0, caps=False)
        mb.box(mt, -11, -9, 296, 11, 9, 312, 0.9)
        mb.box(mt, -8, -8, 0, 8, 8, 16, 0.9)
    return b


def main():
    M.log('=== art_70_kit: modular architecture ===')
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.make_directory(FOLDER)
    M.log('folder: %s' % FOLDER)

    add('SM_KL_Wall_Panel', [W_OGRE, W_WAIN, WOOD_DK], wall_panel())
    add('SM_KL_Wall_Pier', [W_OGRE, W_WAIN, WOOD_DK], wall_pier())
    add('SM_KL_Wall_Lintel', [W_OGRE], wall_lintel())
    add('SM_KL_Wall_Exterior', [W_EXT], wall_exterior())
    add('SM_KL_Floor_Tile', [FLOOR, CONC], floor_tile())
    add('SM_KL_Ceiling_Panel', [CEIL], ceiling_panel())
    add('SM_KL_Corridor_Beam', [CONC], corridor_beam())
    add('SM_KL_Door_Frame', [WOOD, WOOD_DK, STONE], door_frame())
    add('SM_KL_Door_Leaf', [WOOD, WOOD_DK, RUST], door_leaf())
    add('SM_KL_Window_Frame', [WOOD, WOOD_DK], window_frame())
    add('SM_KL_Window_Glass', [METAL], window_glass())
    add('SM_KL_Shutter_Leaf', [SHUT], shutter_leaf())
    add('SM_KL_PA_Speaker', [METAL, RUST, WOOD_DK], pa_speaker())
    add('SM_KL_Notice_Board', [WOOD_DK, MAT + 'MI_ART_Paper'], notice_board())
    add('SM_KL_Bench_Hall', [WOOD, WOOD_DK], bench_hall())
    add('SM_KL_Fluorescent', [METAL, MAT + 'MI_ART_Tube'], fluorescent_tube())
    add('SM_KL_Water_Tank', [RUST, METAL], water_tank())
    add('SM_KL_Downpipe', [METAL], downpipe())

    total = sum(t for _, t in BUILT)
    M.log('kit: %d meshes, %d triangles total' % (len(BUILT), total))
    M.log('=== art_70_kit done ===')


main()
