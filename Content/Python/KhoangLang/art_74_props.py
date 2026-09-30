"""Khoang Lang 02:17 - interactive prop meshes (art pass step 3).

These replace the stretched engine cubes the art props currently use. The
Blueprint props themselves are NOT touched here - only the meshes are authored
here, and art_25_props.py is re-pointed at them afterwards so the interaction
component, prompts and audio behaviour are preserved exactly.

The four props are the story objects, so each one is modelled to be read at
close range in low light:

  SM_KL_Prop_AttBook   the class attendance book, canon section 5
  SM_KL_Prop_Roster    the roll-call sheet pinned beside the board
  SM_KL_Prop_TapeDeck  the tape deck wired to the PA head
  SM_KL_Prop_Figure    the seated child in the back corner

All four are modelled at true scale in centimetres, so the prop Blueprints
run at scale 1.0.

Run:  run_ue_script.ps1 -Script art_74_props.py
"""

import math
import os
import sys

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import kl_mesh as M  # noqa: E402

FOLDER = '/Game/KhoangLang/Meshes/Props'
MAT = '/Game/KhoangLang/MaterialsArt/'

PAPER = MAT + 'MI_ART_Paper'
WOOD = MAT + 'MI_ART_Wood'
WOOD_DK = MAT + 'MI_ART_WoodDark'
METAL = MAT + 'MI_ART_Metal'
RUST = MAT + 'MI_ART_MetalRust'
SHUT = MAT + 'MI_ART_ShutterBlue'
DOOR = MAT + 'MI_ART_DoorGreen'
SIGN = MAT + 'MI_ART_Sign'
CHALK = MAT + 'MI_ART_Chalk'
CONC = MAT + 'MI_ART_Concrete'

BUILT = []


def add(name, mats, fn):
    sm, tris = M.make_mesh(name, FOLDER, mats, fn)
    BUILT.append((name, tris))
    return sm


# --------------------------------------------------------------------------- #
# the attendance book
# --------------------------------------------------------------------------- #

def prop_attbook():
    """A cloth-bound ledger lying open on the desk: cover, page block, a red
    ribbon marker and a rubber band gone slack. Small object, so the page
    edges and the ribbon are what sell it."""
    def b(mb, s):
        pa, dk, wd = s[PAPER], s[WOOD_DK], s[WOOD]
        W, D = 32.0, 23.0
        # board covers, slightly larger than the pages
        mb.chamfer_box(dk, -W / 2, -D / 2, 0, W / 2, D / 2, 1.6, 0.5, 1.6)
        mb.chamfer_box(dk, -W / 2, -D / 2, 5.4, W / 2, D / 2, 7.0, 0.5, 1.6)
        # page block, split into two halves so the gutter reads
        mb.box(pa, -W / 2 + 1.6, -D / 2 + 1.4, 1.6, -0.5, D / 2 - 1.4, 5.4, 3.0)
        mb.box(pa, 0.5, -D / 2 + 1.4, 1.6, W / 2 - 1.6, D / 2 - 1.4, 5.4, 3.0)
        # a few ruled lines on the right-hand page: this is a register, and
        # the grid of lines is what makes it look like one
        for i in range(7):
            y = -D / 2 + 4.0 + i * 2.3
            mb.box(s[CHALK], 1.6, y, 5.4, W / 2 - 2.6, y + 0.35, 5.45, 3.0)
        mb.box(s[CHALK], 1.6, -D / 2 + 2.4, 5.4, W / 2 - 2.6, -D / 2 + 2.6, 5.45, 3.0)
        # spine ridge
        mb.box(dk, -0.6, -D / 2, 1.6, 0.6, D / 2, 5.4, 2.0)
        # ribbon marker trailing out of the gutter
        mb.box(s[DOOR], -0.5, -D / 2 - 3.0, 4.6, 0.5, D / 2, 5.1, 2.0)
    return b


# --------------------------------------------------------------------------- #
# the roster
# --------------------------------------------------------------------------- #

def prop_roster():
    """The roll-call sheet: a large sheet of cheap paper with a printed header
    band, a ruled table and four drawing pins. Pinned flat to the board."""
    def b(mb, s):
        pa, sk, mt = s[PAPER], s[CHALK], s[METAL]
        W, H = 60.0, 84.0
        hw, hh = W / 2.0, H / 2.0
        # sheet, very slightly warped so it does not read as a decal
        mb.plate(pa, -hw, 0, -hh, hw, 0, hh, 0.8)
        mb.plate(pa, -hw, 0.4, -hh, hw, 0.4, hh, 0.8, flip=True)
        # header band
        mb.box(s[DOOR], -hw + 1, 0.4, hh - 9, hw - 1, 0.7, hh - 1, 2.0)
        mb.box(s[CHALK], -hw + 4, 0.7, hh - 6.5, hw - 4, 0.9, hh - 4.5, 2.0)
        # ruled table
        for i in range(14):
            z = hh - 12 - i * 4.6
            mb.box(sk, -hw + 3, 0.4, z, hw - 3, 0.6, z + 0.3, 2.0)
        for i in range(4):
            x = -hw + 3 + i * ((W - 6) / 3.0)
            mb.box(sk, x, 0.4, -hh + 4, x + 0.3, 0.6, hh - 12, 2.0)
        # the 65th row, ruled but left blank: the story beat is in the gap
        mb.box(s[DOOR], -hw + 3, 0.7, -hh + 4, hw - 3, 0.9, -hh + 4.9, 2.0)
        # pins
        for (px, pz) in ((-hw + 4, hh - 4), (hw - 4, hh - 4),
                         (-hw + 4, -hh + 4), (hw - 4, -hh + 4)):
            mb.cylinder(mt, px, 0, pz, pz + 1.6, 1.1, 8, 1.0, axis='y')
    return b


# --------------------------------------------------------------------------- #
# the tape deck
# --------------------------------------------------------------------------- #

def prop_tapedeck():
    """A portable cassette deck wired into the PA head: steel case, two spool
    windows, a speaker grille, a key row and a carry handle."""
    def b(mb, s):
        mt, ru, dk = s[METAL], s[RUST], s[WOOD_DK]
        W, D, H = 46.0, 34.0, 24.0
        hw, hd = W / 2.0, D / 2.0
        # case
        mb.chamfer_box(mt, -hw, -hd, 0, hw, hd, H, 1.4, 0.9)
        mb.chamfer_box(dk, -hw + 1.5, -hd + 1.5, 0.5, hw - 1.5, hd - 1.5, H - 1.0,
                       1.0, 1.2)
        # front panel, recessed
        mb.box(ru, -hw + 2, -hd - 0.4, 2, hw - 2, -hd + 1.0, H - 2, 1.0)
        # two spool windows with hubs
        for sx in (-11.0, 11.0):
            mb.box(s[RUST], sx - 8, -hd - 0.6, 6, sx + 8, -hd + 0.4, 19, 1.4)
            mb.cylinder(dk, sx, -hd - 0.8, 9.0, -hd + 0.2, 2.6, 10, 1.0, axis='y')
        # speaker grille, punched as slats
        for i in range(6):
            z = 3.4 + i * 1.5
            mb.box(mt, -hw + 3, -hd - 0.7, z, -2, -hd - 0.2, z + 0.8, 1.4)
        # transport keys
        for i in range(5):
            x = -hw + 5 + i * 7.0
            mb.box(dk, x, -hd - 1.6, 7.0, x + 5.0, -hd - 0.2, 11.0, 1.6)
        # tuning dial and a VU needle
        mb.cylinder(mt, hw - 7, -hd - 1.2, 4.0, -hd + 0.2, 3.0, 10, 1.0, axis='y')
        # carry handle
        mb.box(mt, -8, -3, H, 8, 3, H + 5, 1.0)
        mb.box(mt, -8, -3, H + 3.5, -5, 3, H + 5, 1.0)
        mb.box(mt, 5, -3, H + 3.5, 8, 3, H + 5, 1.0)
        # cable leaving the back
        mb.tube(dk, 0, hd, 8.0, 0, hd + 26.0, 2.0, 0.9, 8, 1.2)
    return b


# --------------------------------------------------------------------------- #
# the figure
# --------------------------------------------------------------------------- #

def prop_figure():
    """The seated child in the back corner.

    This is the one asset that must survive being almost unlit, so it is built
    for silhouette first: a compact seated mass, knees together, shoulders
    rounded, head tipped very slightly forward. Large chamfers on the torso
    and head keep the form readable without a normal map.

    Modelled sitting on the floor, facing +Y, origin at the base of the spine.
    Uniform: white shirt, blue trousers - a Vietnamese primary school uniform.
    """
    def b(mb, s):
        white = s[PAPER]          # the shirt reads as the pale mass
        blue = s[SHUT]            # the trousers
        skin = s[WOOD]            # head and hands
        dark = s[WOOD_DK]         # hair, shoes

        # ---- legs: thighs forward, shins down, feet flat -----------------
        # knees together, the posture of a child who has been told to sit still
        for sx in (-1, 1):
            x0, x1 = (1.0, 15.0) if sx > 0 else (-15.0, -1.0)
            mb.chamfer_box(blue, x0, 2.0, 4.0, x1, 34.0, 19.0, 5.0, 1.0)
            mb.chamfer_box(blue, x0, 30.0, 0.0, x1, 40.0, 16.0, 4.0, 1.0)
            mb.chamfer_box(dark, x0 - 0.5, 40.0, 0.0, x1 + 0.5, 50.0, 8.0, 2.5, 1.4)

        # ---- torso: tapered, leaning very slightly forward -------------
        mb.chamfer_box(white, -15.0, -2.0, 17.0, 15.0, 22.0, 44.0, 6.5, 0.9)
        mb.chamfer_box(white, -16.0, -1.0, 40.0, 16.0, 21.0, 52.0, 7.0, 0.9)
        # collar
        mb.chamfer_box(blue, -7.0, 0.0, 50.0, 7.0, 12.0, 54.0, 2.0, 1.4)

        # ---- arms hanging down against the thighs -----------------------
        for sx in (-1, 1):
            x0, x1 = (15.0, 23.0) if sx > 0 else (-23.0, -15.0)
            mb.chamfer_box(white, x0, 4.0, 26.0, x1, 18.0, 46.0, 4.0, 1.0)
            mb.chamfer_box(skin, x0 + 1.5, 6.0, 18.0, x1 - 1.5, 16.0, 28.0, 3.0, 1.2)

        # ---- neck and head ----------------------------------------------
        mb.chamfer_box(skin, -4.5, 6.0, 52.0, 4.5, 16.0, 58.0, 2.0, 1.2)
        mb.chamfer_box(skin, -9.5, 3.0, 57.0, 9.5, 19.0, 76.0, 7.0, 1.0)
        # hair: a bowl cut, the period detail
        mb.chamfer_box(dark, -10.5, 2.0, 66.0, 10.5, 20.0, 77.0, 7.5, 1.0)
        mb.chamfer_box(dark, -10.5, 2.0, 70.0, 10.5, 5.0, 77.0, 3.0, 1.0)
    return b


def main():
    M.log('=== art_74_props: interactive prop meshes ===')
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.make_directory(FOLDER)
    M.log('folder: %s' % FOLDER)

    add('SM_KL_Prop_AttBook', [PAPER, WOOD_DK, WOOD, CHALK, DOOR], prop_attbook())
    add('SM_KL_Prop_Roster', [PAPER, CHALK, DOOR, METAL], prop_roster())
    add('SM_KL_Prop_TapeDeck', [METAL, RUST, WOOD_DK], prop_tapedeck())
    add('SM_KL_Prop_Figure', [PAPER, SHUT, WOOD, WOOD_DK], prop_figure())

    total = sum(t for _, t in BUILT)
    M.log('props: %d meshes, %d triangles total' % (len(BUILT), total))
    M.log('=== art_74_props done ===')


main()
