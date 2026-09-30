"""Khoang Lang 02:17 - art pass step 3: assemble Lvl_KL_School3_Art."""

import os
import sys

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import kl_core as K  # noqa: E402
import art_geo as G  # noqa: E402
from art_geo import (T, CEIL_HALL, CEIL_ROOM, CEIL_ENTRY, YARD_X0, YARD_X1,
                     YARD_Y0, YARD_Y1, YARD_Z, PORT_X0, PORT_X1, PORT_Y0,
                     PORT_Y1, PORT_Z, ENTRY_X0, ENTRY_X1, ENTRY_Y0, ENTRY_Y1,
                     CORR_X0, CORR_X1, CORR_Y0, CORR_Y1, ROOM_X0, ROOM_X1,
                     ROOM_Y0, ROOM_Y1, ROOM2_X0, ROOM2_X1, ROOM2_Y0,
                     ROOM2_Y1, DOOR_X0, DOOR_X1, DOOR_H, ROOF_Z0, ROOF_Z1,
                     BLD_X0, BLD_X1, BLD_Y0, BLD_Y1, PLAYER_START,
                     PLAYER_YAW, P_BOOK, P_ROSTER, P_TAPE, P_CORNER,
                     MAT, F_PROPS_ART, MAP, STATS, slab, panel, light,
                     place_class, place_asset, m, quat)
from kl_core import step, ok, warn, fail  # noqa: E402
from editor_toolset.toolsets import scene as SCENE  # noqa: E402

W_OCHRE = 'MI_ART_WallOchre'
W_CLASS = 'MI_ART_WallClassroom'
W_EXT = 'MI_ART_WallExt'
W_WAIN = 'MI_ART_WallWainscot'
FLOOR = 'MI_ART_Floor'
CEIL = 'MI_ART_Ceiling'
WOOD = 'MI_ART_Wood'
WOOD_DK = 'MI_ART_WoodDark'
DOOR = 'MI_ART_DoorGreen'
SHUT = 'MI_ART_ShutterBlue'
CHALK = 'MI_ART_Chalk'
METAL = 'MI_ART_Metal'
RUST = 'MI_ART_MetalRust'
PAPER = 'MI_ART_Paper'
STONE = 'MI_ART_Stone'
CONC = 'MI_ART_Concrete'
SIGN = 'MI_ART_Sign'
TUBE = 'MI_ART_Tube'
TUBE_COLD = 'MI_ART_TubeCold'
TUBE_DEAD = 'MI_ART_TubeDead'


# --------------------------------------------------------------------------- #
# exterior: yard, gate, facade
# --------------------------------------------------------------------------- #

def build_exterior():
    step('exterior: yard, gate wall, facade')
    slab('Ground', YARD_X0 - 400, BLD_X1, BLD_Y0 - 400, BLD_Y1 + 400,
         YARD_Z - 20, YARD_Z, STONE, shadow=False)
    # yard is lower than the building: a step + landing at the portico
    slab('YardStep', PORT_X0 - 45, PORT_X0, -150.0, 150.0,
         YARD_Z, PORT_Z, CONC)
    slab('PorticoFloor', PORT_X0, PORT_X1, PORT_Y0, PORT_Y1, PORT_Z - 20,
         PORT_Z, FLOOR)
    # gate wall with an opening, and the sign beside it
    slab('GateWallS', PORT_X0 - 30, PORT_X0, -1600.0, -150.0, YARD_Z, 240.0, W_EXT)
    slab('GateWallN', PORT_X0 - 30, PORT_X0, 150.0, 1600.0, YARD_Z, 240.0, W_EXT)
    slab('GatePostS', PORT_X0 - 45, PORT_X0 + 15, -175.0, -140.0, YARD_Z, 300.0, STONE)
    slab('GatePostN', PORT_X0 - 45, PORT_X0 + 15, 140.0, 175.0, YARD_Z, 300.0, STONE)
    # school sign, mounted on the wall south of the gate, facing the yard
    slab('SignPlate', PORT_X0 - 36, PORT_X0 - 32, -560.0, -310.0, 70.0, 196.0, SIGN)
    # gate leaves: one open, one closed
    slab('GateLeafS', PORT_X0 - 26, PORT_X0 - 22, -150.0, -10.0, YARD_Z + 10,
         YARD_Z + 170, RUST, rot=(0.0, 26.0, 0.0))

    # portico: six columns, beam, roof
    for i, yy in enumerate((-820.0, -500.0, -170.0, 170.0, 500.0, 820.0)):
        slab('PortCol%d' % i, PORT_X0 + 40, PORT_X0 + 80, yy - 17, yy + 17,
             PORT_Z, CEIL_ENTRY - 30, CONC, mesh='Cylinder')
    slab('PortBeam', PORT_X0 + 20, PORT_X1, PORT_Y0, PORT_Y1, CEIL_ENTRY - 30,
         CEIL_ENTRY, CONC)
    slab('PortRoof', PORT_X0 - 60, PORT_X1 + 20, PORT_Y0 - 60, PORT_Y1 + 60,
         ROOF_Z0, ROOF_Z1, W_EXT)
    # verandah railing between columns
    for i, (ya, yb) in enumerate(((-800.0, -520.0), (-480.0, -190.0),
                                  (190.0, 480.0), (520.0, 800.0))):
        slab('PortRail%d' % i, PORT_X0 + 45, PORT_X0 + 75, ya, yb,
             PORT_Z + 30, PORT_Z + 95, WOOD)

    # entry hall shell
    slab('EntryFloor', ENTRY_X0, ENTRY_X1, ENTRY_Y0, ENTRY_Y1, PORT_Z - 20,
         PORT_Z, FLOOR)
    slab('EntryCeil', ENTRY_X0, ENTRY_X1, ENTRY_Y0, ENTRY_Y1, CEIL_ENTRY,
         CEIL_ENTRY + 14, CEIL)
    slab('EntryWallS', ENTRY_X0, ENTRY_X1, ENTRY_Y0 - T, ENTRY_Y0, PORT_Z,
         CEIL_ENTRY, W_OCHRE)
    slab('EntryWallN', ENTRY_X0, ENTRY_X1, ENTRY_Y1, ENTRY_Y1 + T, PORT_Z,
         CEIL_ENTRY, W_OCHRE)
    slab('EntryWallW1', ENTRY_X0 - T, ENTRY_X0, ENTRY_Y0, -120.0, PORT_Z,
         CEIL_ENTRY, W_OCHRE)
    slab('EntryWallW2', ENTRY_X0 - T, ENTRY_X0, 120.0, ENTRY_Y1, PORT_Z,
         CEIL_ENTRY, W_OCHRE)
    slab('EntryWallWLintel', ENTRY_X0 - T, ENTRY_X0, -120.0, 120.0,
         PORT_Z + 230.0, CEIL_ENTRY, W_OCHRE)
    slab('EntryWainS', ENTRY_X0, ENTRY_X1, ENTRY_Y0, ENTRY_Y0 + 5, PORT_Z,
         PORT_Z + 110.0, W_WAIN)
    slab('EntryWainN', ENTRY_X0, ENTRY_X1, ENTRY_Y1 - 5, ENTRY_Y1, PORT_Z,
         PORT_Z + 110.0, W_WAIN)
    # entrance doors, standing open against the reveal
    slab('EntryDoorS', ENTRY_X0 + 10, ENTRY_X0 + 22, -118.0, -14.0, PORT_Z,
         PORT_Z + 228.0, DOOR, rot=(0.0, 22.0, 0.0))
    slab('EntryDoorN', ENTRY_X0 + 10, ENTRY_X0 + 22, 14.0, 118.0, PORT_Z,
         PORT_Z + 228.0, DOOR, rot=(0.0, -22.0, 0.0))
    # a step down into the yard from the entry
    slab('EntryStep', ENTRY_X0 - 60, ENTRY_X0, -160.0, 160.0, YARD_Z,
         YARD_Z + 40.0, CONC)

    # main roof over the classroom wings
    slab('RoofMain', BLD_X0, BLD_X1, BLD_Y0, BLD_Y1, ROOF_Z0, ROOF_Z1, W_EXT)
    slab('RoofFasciaS', BLD_X0, BLD_X1, BLD_Y0 - 12, BLD_Y0, ROOF_Z0 - 22,
         ROOF_Z1, W_EXT)
    slab('RoofFasciaN', BLD_X0, BLD_X1, BLD_Y1, BLD_Y1 + 12, ROOF_Z0 - 22,
         ROOF_Z1, W_EXT)
    slab('RoofParapetW', BLD_X0 - 12, BLD_X0, BLD_Y0, BLD_Y1, ROOF_Z1,
         ROOF_Z1 + 34, W_EXT)
    for i, yy in enumerate((-1700.0, -600.0, 600.0, 1700.0)):
        slab('Downpipe%d' % i, BLD_X1 - 10, BLD_X1 + 4, yy - 7, yy + 7,
             YARD_Z, ROOF_Z0, METAL, mesh='Cylinder')
    # water tank on the roof: unmistakably a Vietnamese school
    slab('TankPad', 900.0, 1220.0, -120.0, 120.0, ROOF_Z1, ROOF_Z1 + 14, CONC)
    slab('Tank', 940.0, 1180.0, -80.0, 80.0, ROOF_Z1 + 14, ROOF_Z1 + 150,
         RUST, mesh='Cylinder')


# --------------------------------------------------------------------------- #
# corridor
# --------------------------------------------------------------------------- #

def build_corridor():
    step('corridor')
    slab('CorrFloor', CORR_X0, CORR_X1, CORR_Y0, CORR_Y1, 0.0, 6.0, FLOOR)
    slab('CorrDrain', CORR_X0, CORR_X1, -14.0, 14.0, -4.0, 2.0, CONC)
    slab('CorrCeil', CORR_X0, CORR_X1, CORR_Y0, CORR_Y1, CEIL_HALL,
         CEIL_HALL + 12, CEIL)
    slab('CorrWallN', CORR_X0, CORR_X1, CORR_Y1, CORR_Y1 + T, 0.0, CEIL_HALL,
         W_OCHRE)
    slab('CorrWallS1', CORR_X0, DOOR_X0, CORR_Y0 - T, CORR_Y0, 0.0, CEIL_HALL,
         W_OCHRE)
    slab('CorrWallS2', DOOR_X1, CORR_X1, CORR_Y0 - T, CORR_Y0, 0.0, CEIL_HALL,
         W_OCHRE)
    slab('CorrWallSLintel', DOOR_X0, DOOR_X1, CORR_Y0 - T, CORR_Y0, DOOR_H,
         CEIL_HALL, W_OCHRE)
    slab('CorrWainN', CORR_X0, CORR_X1, CORR_Y1 - 5, CORR_Y1, 0.0, 110.0, W_WAIN)
    slab('CorrWainS1', CORR_X0, DOOR_X0, CORR_Y0, CORR_Y0 + 5, 0.0, 110.0, W_WAIN)
    slab('CorrWainS2', DOOR_X1, CORR_X1, CORR_Y0, CORR_Y0 + 5, 0.0, 110.0, W_WAIN)
    slab('CorrSkirtN', CORR_X0, CORR_X1, CORR_Y1 - 8, CORR_Y1, 0.0, 14.0, WOOD_DK)
    slab('CorrSkirtS', CORR_X0, DOOR_X0, CORR_Y0, CORR_Y0 + 8, 0.0, 14.0, WOOD_DK)
    # doorway frame + the door of room 3, standing open
    slab('DoorJambW', DOOR_X0 - 34, DOOR_X0, CORR_Y0 - T, CORR_Y0 + 6, 0.0,
         DOOR_H + 8, WOOD)
    slab('DoorJambE', DOOR_X1, DOOR_X1 + 34, CORR_Y0 - T, CORR_Y0 + 6, 0.0,
         DOOR_H + 8, WOOD)
    slab('DoorHead', DOOR_X0 - 34, DOOR_X1 + 34, CORR_Y0 - T, CORR_Y0 + 6,
         DOOR_H, DOOR_H + 26, WOOD)
    slab('Room3Door', DOOR_X0 + 6, DOOR_X0 + 18, CORR_Y0 + 4, CORR_Y0 + 130.0,
         0.0, DOOR_H - 6, DOOR, rot=(0.0, 28.0, 0.0))
    # two closed classroom doors further along, so the school reads as a school
    for i, (dx0, dx1, side) in enumerate(((1120.0, 1230.0, -1),
                                          (1620.0, 1730.0, 1))):
        yy = CORR_Y1 if side > 0 else CORR_Y0
        slab('ClosedDoor%d' % i, dx0, dx1, yy - 7, yy + 7, 0.0, DOOR_H - 6, DOOR)
        slab('ClosedJamb%d' % i, dx0 - 26, dx1 + 26, yy - T, yy + 4, 0.0,
             DOOR_H + 8, WOOD)
    # ceiling conduit and a lamp every other bay
    for i, yy in enumerate((-140.0, 140.0)):
        slab('Conduit%d' % i, CORR_X0, CORR_X1, yy - 4, yy + 4,
             CEIL_HALL - 10, CEIL_HALL - 4, METAL, mesh='Cylinder')
    for i, xx in enumerate((300.0, 700.0, 1100.0, 1500.0, 1900.0)):
        lit = 'TUBE_DEAD' if i in (1, 3) else TUBE
        slab('CorrTube%d' % i, xx - 8, xx + 8, -62.0, 62.0,
             CEIL_HALL - 12, CEIL_HALL - 8, lit, mesh='Cylinder',
             shadow=False, collision=False)
        slab('CorrTubeHousing%d' % i, xx - 16, xx + 16, -78.0, 78.0,
             CEIL_HALL - 14, CEIL_HALL - 4, METAL)
    # notice board, bench, broom, extinguisher bracket, chair stack
    slab('NoticeBoard', 520.0, 900.0, CORR_Y1 - 12, CORR_Y1 - 6, 110.0, 250.0,
         WOOD_DK)
    panel('NoticePaper', (710.0, CORR_Y1 - 13.0, 180.0), (360.0, 140.0), PAPER,
          rot=(-90.0, 0.0, 0.0))
    slab('CorrBench', 180.0, 420.0, CORR_Y0 + 30, CORR_Y0 + 110, 0.0, 44.0, WOOD)
    slab('CorrBenchLegA', 190.0, 220.0, CORR_Y0 + 36, CORR_Y0 + 104, 0.0, 40.0,
         WOOD_DK)
    slab('CorrBenchLegB', 380.0, 410.0, CORR_Y0 + 36, CORR_Y0 + 104, 0.0, 40.0,
         WOOD_DK)
    slab('Broom', 1500.0, 1512.0, CORR_Y0 + 40, CORR_Y0 + 52, 0.0, 138.0, WOOD,
         rot=(0.0, 12.0, 0.0))
    slab('Extinguisher', 1290.0, 1320.0, CORR_Y1 - 26, CORR_Y1 - 16, 96.0, 170.0,
         'MI_ART_Sign', mesh='Cylinder')
    # stacked chairs against the far wall
    for i in range(4):
        slab('ChairStack%d' % i, 1880.0, 1960.0, CORR_Y1 - 90, CORR_Y1 - 20,
             i * 22.0, i * 22.0 + 16.0, WOOD)
    # PA head + tape deck at the far end
    slab('PABracket', 990.0, 1000.0, -8.0, 8.0, 150.0, 210.0, METAL)
    slab('PAHorn', 1000.0, 1075.0, -46.0, 46.0, 172.0, 240.0, METAL,
         mesh='Cone', rot=(0.0, 90.0, 0.0))
    slab('PABody', 1000.0, 1030.0, -22.0, 22.0, 128.0, 172.0, RUST)
    slab('PAIndicator', 1002.0, 1006.0, -8.0, 8.0, 186.0, 194.0,
         'MI_ART_Indicator', shadow=False, collision=False)


# --------------------------------------------------------------------------- #
# classroom 3
# --------------------------------------------------------------------------- #

def build_classroom():
    step('classroom 3')
    slab('RoomFloor', ROOM_X0, ROOM_X1, ROOM_Y0, ROOM_Y1, 0.0, 6.0, FLOOR)
    slab('RoomCeil', ROOM_X0, ROOM_X1, ROOM_Y0, ROOM_Y1, CEIL_ROOM,
         CEIL_ROOM + 12, CEIL)
    slab('RoomWallW', ROOM_X0 - T, ROOM_X0, ROOM_Y0, ROOM_Y1, 0.0, CEIL_ROOM,
         W_CLASS)
    slab('RoomWallE1', ROOM_X1, ROOM_X1 + T, ROOM_Y0, 420.0, 0.0, CEIL_ROOM,
         W_CLASS)
    slab('RoomWallE2', ROOM_X1, ROOM_X1 + T, 1420.0, ROOM_Y1, 0.0, CEIL_ROOM,
         W_CLASS)
    slab('RoomWallE3', ROOM_X1, ROOM_X1 + T, 420.0, 1420.0, 260.0, CEIL_ROOM,
         W_CLASS)
    slab('RoomWallS', ROOM_X0, ROOM_X1, ROOM_Y1, ROOM_Y1 + T, 0.0, CEIL_ROOM,
         W_CLASS)
    slab('RoomWallN1', ROOM_X0, DOOR_X0, ROOM_Y0 - T, ROOM_Y0, 0.0, CEIL_ROOM,
         W_CLASS)
    slab('RoomWallN2', DOOR_X1, ROOM_X1, ROOM_Y0 - T, ROOM_Y0, 0.0, CEIL_ROOM,
         W_CLASS)
    slab('RoomWallNLintel', DOOR_X0, DOOR_X1, ROOM_Y0 - T, ROOM_Y0, DOOR_H,
         CEIL_ROOM, W_CLASS)
    slab('RoomWainW', ROOM_X0, ROOM_X0 + 5, ROOM_Y0, ROOM_Y1, 0.0, 110.0, W_WAIN)
    slab('RoomWainS', ROOM_X0, ROOM_X1, ROOM_Y1 - 5, ROOM_Y1, 0.0, 110.0, W_WAIN)
    slab('RoomSkirtW', ROOM_X0, ROOM_X0 + 8, ROOM_Y0, ROOM_Y1, 0.0, 14.0, WOOD_DK)
    slab('RoomSkirtS', ROOM_X0, ROOM_X1, ROOM_Y1 - 8, ROOM_Y1, 0.0, 14.0, WOOD_DK)

    # chalkboard on the far (south) wall, framed, with a chalk tray
    slab('BoardFrame', 920.0, 1280.0, ROOM_Y1 - 14, ROOM_Y1 - 6, 100.0, 250.0,
         WOOD_DK)
    panel('ChalkboardFace', (1100.0, ROOM_Y1 - 15.0, 175.0), (340.0, 140.0),
          CHALK, rot=(-90.0, 0.0, 0.0))
    slab('ChalkTray', 910.0, 1290.0, ROOM_Y1 - 30, ROOM_Y1 - 6, 88.0, 100.0,
         WOOD)
    slab('ChalkStick', 1200.0, 1230.0, ROOM_Y1 - 28, ROOM_Y1 - 20, 100.0,
         106.0, 'MI_ART_Paper')

    # teacher's platform and desk
    slab('Podium', 980.0, 1220.0, 1560.0, 1700.0, 0.0, 14.0, WOOD_DK)
    slab('TeacherTop', 1030.0, 1180.0, 1460.0, 1540.0, 74.0, 82.0, WOOD)
    slab('TeacherFront', 1030.0, 1180.0, 1456.0, 1462.0, 0.0, 74.0, WOOD)
    slab('TeacherLegA', 1036.0, 1050.0, 1464.0, 1534.0, 0.0, 74.0, WOOD_DK)
    slab('TeacherLegB', 1160.0, 1174.0, 1464.0, 1534.0, 0.0, 74.0, WOOD_DK)
    slab('ChairSeat', 1060.0, 1140.0, 1380.0, 1440.0, 42.0, 50.0, WOOD)
    slab('ChairBack', 1140.0, 1148.0, 1380.0, 1440.0, 50.0, 116.0, WOOD)
    for i, (lx, ly) in enumerate(((1068.0, 1388.0), (1124.0, 1388.0),
                                  (1068.0, 1424.0), (1124.0, 1424.0))):
        slab('ChairLeg%d' % i, lx, lx + 8, ly, ly + 8, 0.0, 42.0, WOOD_DK)

    # twelve double desks with benches, in three rows facing the board
    r = 0
    for yy in (640.0, 900.0, 1160.0):
        for xx in (780.0, 950.0, 1120.0, 1290.0):
            slab('DeskTop%d' % r, xx, xx + 130.0, yy, yy + 66.0, 70.0, 78.0, WOOD)
            slab('DeskRail%d' % r, xx + 8, xx + 122.0, yy + 4, yy + 12.0,
                 58.0, 70.0, WOOD_DK)
            slab('DeskLegA%d' % r, xx + 6, xx + 16, yy + 6, yy + 60.0, 0.0,
                 70.0, WOOD_DK)
            slab('DeskLegB%d' % r, xx + 114, xx + 124, yy + 6, yy + 60.0, 0.0,
                 70.0, WOOD_DK)
            slab('Bench%d' % r, xx + 12, xx + 118.0, yy - 46.0, yy - 6.0,
                 40.0, 48.0, WOOD)
            slab('BenchLegA%d' % r, xx + 18, xx + 28, yy - 42.0, yy - 10.0, 0.0,
                 40.0, WOOD_DK)
            slab('BenchLegB%d' % r, xx + 102, xx + 112, yy - 42.0, yy - 10.0,
                 0.0, 40.0, WOOD_DK)
            r += 1
    ok('classroom desks: %d' % r)

    # ceiling fan
    slab('FanRod', 1092.0, 1108.0, 992.0, 1008.0, CEIL_ROOM - 34,
         CEIL_ROOM, METAL, mesh='Cylinder')
    slab('FanHub', 1060.0, 1140.0, 972.0, 1028.0, CEIL_ROOM - 44,
         CEIL_ROOM - 30, METAL, mesh='Cylinder')
    for i, ang in enumerate((0.0, 45.0, 90.0, 135.0)):
        slab('FanBlade%d' % i, 1000.0, 1200.0, 994.0, 1006.0, CEIL_ROOM - 42,
             CEIL_ROOM - 38, WOOD, rot=(0.0, 0.0, ang))

    # east windows: frame, sill, and open blue shutters
    for i, (wy0, wy1) in enumerate(((460.0, 700.0), (780.0, 1020.0),
                                    (1100.0, 1340.0))):
        slab('WinFrame%d' % i, ROOM_X1 + T - 8, ROOM_X1 + T, wy0, wy1, 100.0,
             260.0, WOOD, shadow=False, collision=False)
        panel('WinNight%d' % i, (ROOM_X1 + T - 4.0, (wy0 + wy1) / 2.0, 180.0),
              (wy1 - wy0, 160.0), 'MI_ART_Metal', rot=(0.0, 90.0, 0.0))
        slab('WinSill%d' % i, ROOM_X1 - 16, ROOM_X1 + T, wy0 - 10, wy1 + 10,
             92.0, 100.0, WOOD)
        slab('Shutter%d' % i, ROOM_X1 + T, ROOM_X1 + T + 10, wy0 + 6, wy0 + 44,
             100.0, 260.0, SHUT, rot=(0.0, -26.0, 0.0), collision=False)
        slab('ShutterRb%d' % i, ROOM_X1 + T, ROOM_X1 + T + 10, wy1 - 44,
             wy1 - 6, 100.0, 260.0, SHUT, rot=(0.0, 26.0, 0.0), collision=False)

    # wall map, shelf, bin, coat hooks
    panel('WallMap', (ROOM_X0 + 4.0, 760.0, 190.0), (300.0, 220.0), PAPER,
          rot=(0.0, 90.0, 0.0))
    slab('Shelf', ROOM_X0 + 4, ROOM_X0 + 34, 1200.0, 1450.0, 0.0, 170.0, WOOD)
    for i in range(3):
        slab('ShelfPlank%d' % i, ROOM_X0 + 4, ROOM_X0 + 34, 1200.0, 1450.0,
             50.0 + i * 55.0, 58.0 + i * 55.0, WOOD)
    for i in range(6):
        slab('Book%d' % i, ROOM_X0 + 6, ROOM_X0 + 30, 1210.0 + i * 38.0,
             1240.0 + i * 38.0, 58.0, 96.0, SHUT if i % 2 else DOOR)
    slab('Bin', 770.0, 830.0, 400.0, 460.0, 0.0, 46.0, METAL, mesh='Cylinder')
    for i in range(4):
        slab('Hook%d' % i, ROOM_X0 + 4, ROOM_X0 + 18, 400.0 + i * 40.0,
             408.0 + i * 40.0, 160.0, 168.0, METAL)

    # the corner: stacked desks, and the stain that explains it
    for i in range(3):
        slab('CornerStack%d' % i, 740.0, 800.0, 1620.0, 1700.0,
             i * 46.0, i * 46.0 + 12.0, WOOD, rot=(0.0, 0.0, 90.0 * i))
    panel('CeilStain', (830.0, 1660.0, CEIL_ROOM - 1.0), (260.0, 220.0),
          'MI_ART_WoodDark', rot=(90.0, 0.0, 0.0))
    panel('WallStainS', (900.0, ROOM_Y1 - 1.0, 150.0), (240.0, 190.0),
          'MI_ART_Concrete', rot=(-90.0, 0.0, 0.0))
    panel('WallStainW', (ROOM_X0 + 1.0, 1560.0, 130.0), (200.0, 170.0),
          'MI_ART_Concrete', rot=(0.0, 90.0, 0.0))

    # classroom 2, north wing: a closed shell so the corridor has depth
    slab('Room2WallS', ROOM2_X0, ROOM2_X1, ROOM2_Y1, ROOM2_Y1 + T, 0.0,
         CEIL_ROOM, W_OCHRE)
    slab('Room2WallN', ROOM2_X0, ROOM2_X1, ROOM2_Y0 - T, ROOM2_Y0, 0.0,
         CEIL_ROOM, W_OCHRE)
    slab('Room2WallW', ROOM2_X0 - T, ROOM2_X0, ROOM2_Y0, ROOM2_Y1, 0.0,
         CEIL_ROOM, W_OCHRE)
    slab('Room2WallE', ROOM2_X1, ROOM2_X1 + T, ROOM2_Y0, ROOM2_Y1, 0.0,
         CEIL_ROOM, W_OCHRE)
    slab('Room2Floor', ROOM2_X0, ROOM2_X1, ROOM2_Y0, ROOM2_Y1, 0.0, 6.0, FLOOR)
    slab('Room2Ceil', ROOM2_X0, ROOM2_X1, ROOM2_Y0, ROOM2_Y1, CEIL_ROOM,
         CEIL_ROOM + 12, CEIL)


# --------------------------------------------------------------------------- #
# lighting + atmosphere
# --------------------------------------------------------------------------- #

def build_lighting():
    step('lighting')
    # one directional moon, shadowed, everything else fills
    light('Directional', 'Moon', (-600.0, -400.0, 1200.0), 0.35,
          (0.52, 0.63, 0.95), rot=(-38.0, 24.0, 0.0), shadows=True)
    light('Point', 'FillYard', (-1500.0, 0.0, 320.0), 45.0, (0.30, 0.40, 0.62),
          radius=2600.0)
    light('Point', 'FillPortico', (-550.0, 0.0, 300.0), 70.0, (0.55, 0.60, 0.78),
          radius=1100.0)
    light('Point', 'EntryLight', (-150.0, 0.0, 290.0), 60.0, (1.0, 0.90, 0.72),
          radius=1100.0)
    # corridor: only three of the five tubes get a real light
    for i, (xx, inten) in enumerate(((300.0, 55.0), (1100.0, 45.0),
                                     (1900.0, 40.0))):
        light('Point', 'CorrL%d' % i, (xx, 0.0, 296.0), inten,
              (1.0, 0.93, 0.78), radius=1000.0, shadows=(i == 0))
    light('Point', 'DoorLight', (890.0, 240.0, 290.0), 34.0, (1.0, 0.90, 0.74),
          radius=900.0)
    # classroom: two tubes plus two moon shafts through the windows
    light('Point', 'RoomL0', (1100.0, 700.0, 296.0), 62.0, (1.0, 0.93, 0.80),
          radius=1400.0, shadows=True)
    light('Point', 'RoomL1', (1100.0, 1300.0, 296.0), 44.0, (1.0, 0.91, 0.76),
          radius=1300.0)
    light('Spot', 'MoonShaft0', (ROOM_X1 + 260.0, 580.0, 220.0), 900.0,
          (0.58, 0.70, 1.0), rot=(0.0, 118.0, 0.0), shadows=False,
          atten=2600.0, cone=(24.0, 52.0))
    light('Spot', 'MoonShaft1', (ROOM_X1 + 260.0, 1220.0, 220.0), 800.0,
          (0.58, 0.70, 1.0), rot=(0.0, 118.0, 0.0), shadows=False,
          atten=2600.0, cone=(24.0, 52.0))
    # the PA end of the corridor gets a faint practical so the tape deck reads
    light('Point', 'PALight', (1000.0, 0.0, 240.0), 26.0, (0.95, 0.88, 0.72),
          radius=700.0)
    # a very low cool bounce in the back corner: the anomaly is lit by moonlight
    # that should not be there, not by a horror light
    light('Point', 'CornerMoon', (760.0, 1660.0, 250.0), 14.0, (0.55, 0.68, 0.95),
          radius=620.0)
    ok('lights placed: %d' % STATS['lights'])


def build_atmosphere():
    step('atmosphere + post process')
    # height fog: cheap depth cue, no volumetrics
    for cls_name in ('ExponentialHeightFog',):
        cls = getattr(unreal, cls_name, None)
        if cls is None:
            warn('%s unavailable' % cls_name)
            continue
        a = place_class(cls.static_class(), 'ART_Fog', (0.0, 0.0, 200.0))
        if a is None:
            continue
        c = K.find_comp(a, 'ExponentialHeightFogComponent')
        if c is None:
            continue
        for prop, val in (('fog_density', 0.022),
                      ('start_distance', 300.0),
                      ('fog_height_falloff', 0.22),
                      ('fog_cutoff_distance', 0.0)):
        try:
            c.set_editor_property(prop, val)
        except Exception as exc:
            warn('fog.%s: %r' % (prop, str(exc)[:60]))
    for prop in ('fog_height_offset', 'fog_inscattering_color', 'volumetric_fog',
                 'volumetric_fog_extinction_scale'):
        if c.get_editor_property.__doc__ is not None and prop in dir(c):
            pass
    for prop, val in (('volumetric_fog', False),):
        try:
            c.set_editor_property(prop, val)
            ok('fog.%s set (volumetric off)' % prop)
        except Exception:
            pass
        ok('height fog added (non volumetric)')

    cls = getattr(unreal, 'PostProcessVolume', None)
    if cls is None:
        warn('PostProcessVolume unavailable')
        return
    a = place_class(cls.static_class(), 'ART_Grade', (0.0, 0.0, 150.0))
    if a is None:
        return
    c = K.find_comp(a, 'PostProcessVolume') or K.find_comp(a, 'BrushComponent')
    comp = None
    for cc in K.ACT.ActorTools.get_components(a):
        if 'PostProcess' in cc.get_class().get_name() or 'Brush' in cc.get_class().get_name():
            comp = cc
            break
    if comp is None:
        warn('no post process component on the volume')
        return
    s = unreal.PostProcessSettings()
    applied, missing = 0, []

    def aem(name):
        for attr in dir(unreal.AutoExposureMethod):
            if name in attr.upper():
                return getattr(unreal.AutoExposureMethod, attr)
        raise RuntimeError('AutoExposureMethod.' + name)

    for prop, val in (('b_override_eye_adaptation_method', True),
                      ('auto_exposure_method', aem('MANUAL')),
                      ('b_override_auto_exposure_min_brightness', True),
                      ('auto_exposure_min_brightness', 0.55),
                      ('b_override_auto_exposure_max_brightness', True),
                      ('auto_exposure_max_brightness', 1.35),
                      ('b_override_auto_exposure_bias', True),
                      ('auto_exposure_bias', 0.4),
                      ('b_override_auto_exposure_apply_physical_camera_exposure',
                       True),
                      ('auto_exposure_apply_physical_camera_exposure', False),
                      ('b_override_camera_motion_blur', True),
                      ('camera_motion_blur_amount', 0.0),
                      ('b_override_depth_of_field', True),
                      ('depth_of_field_enabled', False),
                      ('b_override_motion_blur', True),
                      ('motion_blur_amount', 0.0),
                      ('b_override_lens_flare', True),
                      ('lens_flare_bloom_intensity', 0.0),
                      ('b_override_chromatic_aberration', True),
                      ('chromatic_aberration_intensity', 0.0),
                      ('b_override_color_contrast', True),
                      ('color_contrast', 1.12),
                      ('b_override_color_saturation', True),
                      ('color_saturation', 0.86),
                      ('b_override_color_gamma', True),
                      ('color_gamma', 1.05),
                      ('b_override_color_offset', True),
                      ('color_offset', (0.008, 0.012, 0.022, 0.0)),
                      ('b_override_color_gain', True),
                      ('color_gain', (0.98, 0.99, 1.03, 1.0)),
                      ('b_override_vignette_intensity', True),
                      ('vignette_intensity', 0.32),
                      ('b_override_bloom_intensity', True),
                      ('bloom_intensity', 0.55),
                      ('b_override_bloom_threshold', True),
                      ('bloom_threshold', 1.05),
                      ('b_override_ambient_occlusion_intensity', True),
                      ('ambient_occlusion_intensity', 0.85),
                      ('b_override_ambient_occlusion_radius', True),
                      ('ambient_occlusion_radius', 55.0),
                      ('b_override_motion_blur', True),
                      ('b_override_local_exposure', True),
                      ('b_override_lens_flare', True),
                      ('b_override_screen_space_reflections', True),
                      ('screen_space_reflections_intensity', 18.0),
                      ('b_override_ambient_occlusion_power', True),
                      ('ambient_occlusion_power', 1.4),
                      ('b_override_ambient_occlusion_static_fraction', True),
                      ('ambient_occlusion_static_fraction', 0.35)):
        try:
            s.set_editor_property(prop, val)
            applied += 1
        except Exception:
            missing.append(prop)
    try:
        comp.set_editor_property('settings', s)
        ok('post process applied (%d settings, %d unsupported)' % (applied, len(missing)))
        if missing:
            warn('unsupported post process settings: %s' % ', '.join(missing[:12]))
    except Exception as exc:
        fail('assign post process settings: %r' % (exc,))
    try:
        comp.set_editor_property('blend_weight', 1.0)
        comp.set_editor_property('blend_radius', 0.0)
        comp.set_editor_property('unbound', True)
    except Exception as exc:
        warn('post process volume flags: %r' % (exc,))
    # keep the moon out of the fully black parts of the yard
    light('Point', 'FillYard2', (-900.0, 900.0, 300.0), 30.0, (0.32, 0.42, 0.62),
          radius=2200.0)


# --------------------------------------------------------------------------- #
# interactables + start
# --------------------------------------------------------------------------- #

def build_interactables():
    step('interactables + player start')
    place_asset(F_PROPS_ART + '/BP_KL_Prop_ART_AttBook', 'AttBook', P_BOOK,
                (0.0, 0.0, 14.0))
    place_asset(F_PROPS_ART + '/BP_KL_Prop_ART_Roster', 'Roster', P_ROSTER)
    place_asset(F_PROPS_ART + '/BP_KL_Prop_ART_TapeDeck', 'TapeDeck', P_TAPE,
                (0.0, 0.0, 90.0))
    place_asset(F_PROPS_ART + '/BP_KL_Prop_ART_Corner', 'Corner', P_CORNER)
    t = unreal.Transform()
    t.set_editor_property('translation', unreal.Vector(*PLAYER_START))
    t.set_editor_property('rotation', quat(0.0, PLAYER_YAW, 0.0))
    t.set_editor_property('scale3d', unreal.Vector(1, 1, 1))
    ps = SCENE.SceneTools.add_to_scene_from_class(
        unreal.PlayerStart.static_class(), 'ART_PlayerStart', t)
    STATS['actors'] += 1
    if ps is None:
        fail('player start')
    else:
        ok('player start at %s' % (PLAYER_START,))


def configure_world():
    world = unreal.EditorLevelLibrary.get_editor_world()
    ws = world.get_world_settings()
    for prop, val in (('kill_z', -400.0), ('default_fog_mode', unreal.FogMode.FOGMODE_HeightFog)):
        try:
            ws.set_editor_property(prop, val)
            ok('WorldSettings %s set' % prop)
        except Exception as exc:
            warn('WorldSettings %s: %r' % (prop, str(exc)[:60]))


# --------------------------------------------------------------------------- #

def main():
    K.make_folders()
    K.eas().make_directory(K.ROOT + '/Maps')
    step('create %s' % MAP)
    if unreal.load_asset(MAP) is not None:
        unreal.EditorLevelLibrary.load_level(MAP)
        world = unreal.EditorLevelLibrary.get_editor_world()
        from editor_toolset.toolsets import actor as ACT
        doomed = [a for a in unreal.GameplayStatics.get_all_actors_of_class(
            world, unreal.Actor)
            if str(ACT.ActorTools.get_label(a)).startswith('ART_')]
        for a in doomed:
            SCENE.SceneTools.remove_from_scene(a)
        ok('cleared %d previous ART_ actors' % len(doomed))
    elif not unreal.EditorLevelLibrary.new_level(MAP):
        fail('new_level %s' % MAP)
        return
    ok('level %s ready' % MAP)
    build_exterior()
    build_corridor()
    build_classroom()
    build_lighting()
    build_atmosphere()
    build_interactables()
    configure_world()
    step('totals')
    for k in ('actors', 'meshes', 'lights', 'deco'):
        ok('%s: %d' % (k, STATS[k]))
    K.save(MAP)


K.run(main)
