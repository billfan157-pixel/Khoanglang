"""Khoang Lang 02:17 - parameterized architecture builders.

The level needs walls and floors of whatever width the plan happens to be, not
just one nominal size. Scaling a 400 cm kit panel to fit a 260 cm gap would
stretch its UVs and break texel density, which is the thing that makes tiling
materials look wrong.

So the shell pieces are generated to exact size on demand and cached as assets.
Re-running is idempotent: the same width always produces the same asset.

Each piece is modelled with its origin at the centre of its base edge, running
along +X, with thickness along +Y and height along +Z. That makes a wall run
readable as: place a piece at (centre_x, wall_y, floor_z).

Note on materials: a school corridor has three distinct surfaces, not one. The
upper wall is lime plaster, the dado below 110 cm is oil paint over the same
plaster, and the skirting is timber. Painting the whole wall with one material
is the single biggest reason a school corridor looks like an unfinished box.
"""

import unreal

import kl_mesh as M

MAT = '/Game/KhoangLang/MaterialsArt/'
FOLDER = '/Game/KhoangLang/Meshes/Arch'

W_OGRE = MAT + 'MI_ART_WallOchre'
W_CLASS = MAT + 'MI_ART_WallClassroom'
W_EXT = MAT + 'MI_ART_WallExt'
W_WAIN = MAT + 'MI_ART_WallWainscot'
FLOOR = MAT + 'MI_ART_Floor'
CEIL = MAT + 'MI_ART_Ceiling'
WOOD = MAT + 'MI_ART_Wood'
WOOD_DK = MAT + 'MI_ART_WoodDark'
CONC = MAT + 'MI_ART_Concrete'
STONE = MAT + 'MI_ART_Stone'
METAL = MAT + 'MI_ART_Metal'

T = 20.0          # wall thickness
DADO = 110.0      # top of the painted dado
H = 320.0         # clear interior height

_CACHE = {}
TRI_TOTAL = 0


def cache_get(name):
    return _CACHE.get(name)


def _run(name, mats, fn, collision=True):
    global TRI_TOTAL
    sm, tris = M.make_mesh(name, FOLDER, mats, fn, collision=collision)
    TRI_TOTAL += tris
    _CACHE[name] = sm
    return sm


# --------------------------------------------------------------------------- #
# interior wall, any width
# --------------------------------------------------------------------------- #

def wall(w, h=H, mat=W_OGRE, dado=True, skirt=True, joints=True,
         exterior=False, tag='Wall', open_y0=None, open_y1=None):
    """Interior wall of exactly ``w`` cm, ``h`` cm tall.

    exterior=True gives an outside leaf with no dado, which is what the
    classroom and corridor outer walls use. Passing ``open_y0``/``open_y1``
    produces the window variant: one 140 cm opening centred on the piece.
    """
    if open_y0 is not None:
        return wall_window(w, h, open_y0, open_y1, mat, tag)
    name = 'SM_KL_%s_%d' % (tag, int(round(w)))
    if cache_get(name):
        return name
    hw = w / 2.0

    def b(mb, s):
        upper = s[W_EXT] if exterior else s[mat]
        if exterior:
            mb.box(upper, -hw, 0, 0, hw, T, h, 0.42)
            return
        # upper wall: lime plaster
        mb.box(upper, -hw, 0, DADO, hw, T, h, 0.45)
        if dado:
            # painted dado, standing 1.5 cm proud of the plaster
            mb.box(s[W_WAIN], -hw, -1.5, 0, hw, 0, DADO, 0.45)
            # cap rail closing the dado
            mb.box(s[W_WAIN], -hw, -2.6, DADO, hw, 1.5, DADO + 9, 0.5)
        if skirt:
            mb.box(s[WOOD_DK], -hw, -2.2, 0, hw, 0.5, 14, 0.6)
        if joints:
            # vertical panel joints, spaced so the rhythm is even
            n = max(0, int(round(w / 100.0)) - 1)
            for i in range(1, n + 1):
                x = -hw + w * i / float(n + 1)
                if abs(x) > 4.0:
                    mb.box(s[W_WAIN], x - 1.2, -1.9, 14, x + 1.2, 0.2, DADO, 0.6)
    _run(name, [mat, W_WAIN, WOOD_DK, W_EXT], b)
    return name


def wall_door(w, h=H, tag='WallDoor'):
    """Wall of width ``w`` carrying a 140 x 220 opening on its left.

    The opening sits hard against the -X end so a run of these tiles into a
    straight wall with a door punched through it.
    """
    name = 'SM_KL_%s_%d' % (tag, int(round(w)))
    if cache_get(name):
        return name
    dw = 70.0        # half the 140 opening
    dh = 220.0
    hw = w / 2.0

    def b(mb, s):
        right = -hw + dw + (w - 2 * dw)   # x of the right-hand pier start
        # solid right of the opening
        mb.box(s[W_OGRE], right, 0, 0, hw, T, h, 0.45)
        mb.box(s[W_WAIN], right, -1.5, 0, hw, 0, DADO, 0.45)
        mb.box(s[W_WAIN], right, -2.6, DADO, hw, 1.5, DADO + 9, 0.5)
        mb.box(s[WOOD_DK], right, -2.2, 0, hw, 0.5, 14, 0.6)
        # header over the opening
        mb.box(s[W_OGRE], -hw, 0, dh, right, T, h, 0.45)
        # the reveal, so the opening is lined rather than a hole
        mb.box(s[WOOD_DK], -hw, T - 1.5, 0, -hw + dw, T, dh, 0.7)
        mb.box(s[WOOD_DK], -hw, 0, dh - 1.5, right, T, dh, 0.7)
    _run(name, [W_OGRE, W_WAIN, WOOD_DK], b)
    return name


def wall_window(w, h=H, open_y0=90.0, open_y1=230.0, mat=W_CLASS,
                tag='WallWin'):
    """Wall of width ``w`` with a window opening centred on it.

    ``open_y0``/``open_y1`` are measured from the floor.
    """
    name = 'SM_KL_%s_%d' % (tag, int(round(w)))
    if cache_get(name):
        return name
    hw = w / 2.0
    ow = 70.0                      # half the 140 opening
    z0, z1 = open_y0, open_y1

    def b(mb, s):
        for (a, bb) in ((-hw, -ow), (ow, hw)):
            mb.box(s[W_CLASS], a, 0, 0, bb, T, h, 0.45)
            mb.box(s[W_WAIN], a, -1.5, 0, bb, 0, DADO, 0.45)
            mb.box(s[W_WAIN], a, -2.6, DADO, bb, 1.5, DADO + 9, 0.5)
            mb.box(s[WOOD_DK], a, -2.2, 0, bb, 0.5, 14, 0.6)
        # below and above the opening
        mb.box(s[W_CLASS], -ow, 0, 0, ow, T, z0, 0.45)
        mb.box(s[W_WAIN], -ow, -1.5, 0, ow, 0, min(DADO, z0), 0.45)
        mb.box(s[W_CLASS], -ow, 0, z1, ow, T, h, 0.45)
        # reveal lining
        mb.box(s[WOOD_DK], -ow, T - 1.5, z0, ow, T, z0 + 1.5, 0.7)
        mb.box(s[WOOD_DK], -ow, T - 1.5, z1 - 1.5, ow, T, z1, 0.7)
        mb.box(s[WOOD_DK], -ow, T - 1.5, z0, -ow + 1.5, T, z1, 0.7)
        mb.box(s[WOOD_DK], ow - 1.5, T - 1.5, z0, ow, T, z1, 0.7)
    _run(name, [W_CLASS, W_WAIN, WOOD_DK], b)
    return name


def header(w, z0=220.0, h=100.0, mat=W_OGRE, tag='Header'):
    """Wall band sitting above an opening, from z0 up to z0 + h.

    Needed wherever a run is broken by a doorway: without it the opening is a
    full-height slot and the sky shows through above the door.
    """
    name = 'SM_KL_%s_%d' % (tag, int(round(w)))
    if cache_get(name):
        return name
    hw = w / 2.0

    def b(mb, s):
        mb.box(s[mat], -hw, 0, z0, hw, T, min(z0 + h, H), 0.45)
    _run(name, [mat], b)
    return name


# --------------------------------------------------------------------------- #
# floor and ceiling, any size
# --------------------------------------------------------------------------- #

def floor(w, d, tag='Floor'):
    """Floor slab of exactly ``w`` x ``d`` with a tile joint grid at 50 cm."""
    name = 'SM_KL_%s_%d_%d' % (tag, int(round(w)), int(round(d)))
    if cache_get(name):
        return name
    hw, hd = w / 2.0, d / 2.0

    def b(mb, s):
        mb.box(s[FLOOR], -hw, -hd, -8, hw, hd, 0, 0.34)
        # joints, only where the tile grid actually lands
        x = -hw + 50.0
        while x < hw - 4.0:
            mb.box(s[CONC], x - 0.6, -hd, -8, x + 0.6, hd, -0.2, 0.6)
            x += 50.0
        y = -hd + 50.0
        while y < hd - 4.0:
            mb.box(s[CONC], -hw, y - 0.6, -8, hw, y + 0.6, -0.2, 0.6)
            y += 50.0
    _run(name, [FLOOR, CONC], b)
    return name


def ceiling(w, d, tag='Ceil'):
    """Ceiling slab with a shallow coffer grid, so the ceiling is not a plane."""
    name = 'SM_KL_%s_%d_%d' % (tag, int(round(w)), int(round(d)))
    if cache_get(name):
        return name
    hw, hd = w / 2.0, d / 2.0

    def b(mb, s):
        mb.box(s[CEIL], -hw, -hd, 0, hw, hd, 10, 0.4)
        mb.box(s[CEIL], -hw + 12, -hd + 12, 10, hw - 12, hd - 12, 18, 0.4)
    _run(name, [CEIL], b)
    return name


# --------------------------------------------------------------------------- #
# report
# --------------------------------------------------------------------------- #

def report():
    M.log('kl_kit: %d generated shell pieces, %d triangles' % (len(_CACHE),
                                                               TRI_TOTAL))
