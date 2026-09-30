"""Khoang Lang 02:17 - Milestone 1, pass 3: interactable props + school graybox.

Creates
  BP_KL_Prop_AttBook   - the attendance book (inspect + collect document)
  BP_KL_Prop_TapeDeck  - the hall PA head + tape deck (collect recording)
  BP_KL_Prop_Roster    - the class board note (flavour read)
  BP_KL_Prop_Corner    - the back corner of room 3 (the supernatural beat)
  /Game/KhoangLang/Maps/Lvl_KL_School3

Run headless:  run_ue_script.ps1 build_30_level.py
"""

import math
import os
import sys

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import kl_core as K  # noqa: E402
from kl_core import BP, BPT, ContainerType  # noqa: E402
from kl_core import step, ok, warn, fail  # noqa: E402
from editor_toolset.toolsets import scene as SCENE  # noqa: E402
from editor_toolset.toolsets import actor as ACT  # noqa: E402

INT = K.F_CORE + '/BP_KL_InteractComponent'
GM = K.F_PLAYER + '/BP_KL_GameMode'
MAT = K.F_MAT

PROPS = [
    dict(name='BP_KL_Prop_AttBook', prompt='Đọc sổ điểm danh',
         mesh='Cube', size=(28, 36, 7), mats='M_KL_Paper',
         flags={}, light=None, audio=None),
    dict(name='BP_KL_Prop_TapeDeck', prompt='Nghe băng nối loa',
         mesh='Cube', size=(46, 34, 26), mats='M_KL_Metal',
         flags={'bTapeMode': True}, light=None, audio='TapeOut'),
    dict(name='BP_KL_Prop_Roster', prompt='Đọc bảng danh sách lớp 3',
         mesh='Cube', size=(120, 3, 84), mats='M_KL_Paper',
         flags={'bNoteMode': True}, light=None, audio=None),
    dict(name='BP_KL_Prop_Corner', prompt='Có ai ngồi ở đây',
         mesh='Sphere', size=(34, 34, 62), mats='M_KL_Figure',
         flags={'bCornerMode': True, 'bHiddenAtStart': True},
         light='CornerGlow', audio=None),
]

# --------------------------------------------------------------------------- #
# props
# --------------------------------------------------------------------------- #


def build_props():
    step('interactable props')
    made = []
    for spec in PROPS:
        # A blueprint cannot be deleted and recreated inside one editor
        # session, so re-runs strip the components and rebuild them instead
        # (an earlier build may have stacked duplicates).
        bp, path = K.new_bp(K.F_PROPS, spec['name'], 'Actor')
        for c in list(K.cdo_components(bp)):
            try:
                ACT.ActorTools.remove_component(c)
            except Exception as exc:
                warn('remove_component %s: %r' % (c.get_name(), exc))
        BPT.compile_blueprint(bp)
        mesh = K.add_comp(bp, 'StaticMeshComponent', 'PropMesh')
        ic = K.add_comp(bp, INT, 'KL_Interact')
        if spec['light']:
            K.add_comp(bp, 'PointLightComponent', spec['light'])
        if spec['audio']:
            K.add_comp(bp, 'AudioComponent', spec['audio'])
        BPT.compile_blueprint(bp)
        cdo = K.cdo(bp)
        sx, sy, sz = spec['size']
        mesh.set_editor_property('static_mesh',
                                 unreal.load_asset('/Engine/BasicShapes/' + spec['mesh']))
        mesh.set_editor_property('relative_scale3d',
                                 unreal.Vector(sx / 100.0, sy / 100.0, sz / 100.0))
        try:
            mesh.set_editor_property('override_materials',
                                     [unreal.load_asset('%s/%s' % (MAT, spec['mats']))])
        except Exception as exc:
            warn('%s override_materials: %r' % (spec['name'], exc))
        if spec['light']:
            light = K.find_comp(cdo, 'PointLightComponent')
            if light is not None:
                K.comp_set(light, 'light_color', unreal.Color(0.70, 0.85, 1.0), spec['name'])
                K.comp_set(light, 'attenuation_radius', 260.0, spec['name'])
                K.comp_set(light, 'intensity', 0.0, spec['name'])
                K.comp_set(light, 'cast_shadows', False, spec['name'])
        if spec['audio']:
            aud = K.find_comp(cdo, 'AudioComponent')
            if aud is not None:
                for prop in ('auto_activate', 'b_auto_activate'):
                    try:
                        aud.set_editor_property(prop, False)
                        break
                    except Exception:
                        continue
        icdo = None
        for c in K.cdo_components(bp):
            if 'Interact' in c.get_class().get_name():
                icdo = c
                break
        if icdo is not None:
            icdo.set_editor_property('PromptText', unreal.Text(spec['prompt']))
            for k, v in spec['flags'].items():
                icdo.set_editor_property(k, v)
        BPT.compile_blueprint(bp)
        made.append(path)
        ok('%-34s prompt=%r flags=%s' % (path, spec['prompt'], spec['flags'] or '{}'))
    K.save(K.F_PROPS)
    return made


# --------------------------------------------------------------------------- #
# graybox
# --------------------------------------------------------------------------- #
# All units are centimetres. Hall runs along +X; classroom 3 is south (+Y).

WALL_T = 20          # wall thickness
HALL_Y0, HALL_Y1 = -200.0, 200.0     # hall interior 4 m wide
HALL_X0, HALL_X1 = -400.0, 2000.0    # hall interior
HALL_H = 340.0
CORR_X0, CORR_X1 = -1000.0, -400.0
CORR_Y0, CORR_Y1 = -110.0, 110.0
DOOR_X0, DOOR_X1 = 800.0, 940.0      # classroom 3 doorway in the hall's south wall
ROOM_X0, ROOM_X1 = 550.0, 1550.0
ROOM_Y0, ROOM_Y1 = 200.0, 900.0
ROOM_H = 340.0

PLAYER_START = (-1000.0, 0.0, 120.0)
PLAYER_YAW = 0.0


def quat_from_euler(pitch, yaw, roll):
    """UE FQuat(FRotator) formula, degrees in."""
    sp, cp = math.sin(math.radians(pitch) / 2), math.cos(math.radians(pitch) / 2)
    sy, cy = math.sin(math.radians(yaw) / 2), math.cos(math.radians(yaw) / 2)
    sr, cr = math.sin(math.radians(roll) / 2), math.cos(math.radians(roll) / 2)
    return unreal.Quat(
        x=cr * sp * cy - sr * cp * sy,
        y=-cr * sp * sy - sr * cp * cy,
        z=cr * cp * sy - sr * sp * cy,
        w=cr * cp * cy + sr * sp * sy)


def xform(loc, rot=(0.0, 0.0, 0.0)):
    """Transform from a location and a (pitch, yaw, roll) triple."""
    t = unreal.Transform()
    t.set_editor_property('translation', unreal.Vector(*loc))
    try:
        t.set_editor_property('rotation', quat_from_euler(*rot))
    except Exception as exc:
        if any(rot):
            warn('rotation %r ignored: %r' % (rot, exc))
    t.set_editor_property('scale3d', unreal.Vector(1, 1, 1))
    return t


def box(label, center, size, mat, rot=(0.0, 0.0, 0.0)):
    """One graybox slab."""
    t = xform(center, rot)
    t.set_editor_property('scale3d', unreal.Vector(size[0] / 100.0, size[1] / 100.0,
                                                  size[2] / 100.0))
    a = SCENE.SceneTools.add_to_scene_from_class(unreal.StaticMeshActor.static_class(),
                                                 'KL_' + label, t)
    if a is None:
        fail('spawn slab %s' % label)
        return None
    sm = K.find_comp(a, 'StaticMeshComponent')
    if sm is not None:
        sm.set_editor_property('static_mesh', unreal.load_asset(K.MESH_CUBE))
        try:
            sm.set_editor_property('override_materials', [unreal.load_asset(mat)])
        except Exception as exc:
            warn('%s material: %r' % (label, exc))
    return a


def slab(label, x0, x1, y0, y1, z0, z1, mat, rot=(0.0, 0.0, 0.0)):
    return box(label, ((x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0),
               (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)), mat, rot)


def light(kind, name, loc, intensity, rgb, radius=900.0, rot=(0, 0, 0), shadows=False):
    cls = {'PointLight': unreal.PointLight.static_class(),
           'SpotLight': unreal.SpotLight.static_class(),
           'DirectionalLight': unreal.DirectionalLight.static_class()}[kind]
    t = xform(loc, rot)
    try:
        a = SCENE.SceneTools.add_to_scene_from_class(cls, 'KL_' + name, t)
    except Exception as exc:
        fail('spawn light %s: %r' % (name, exc))
        return None
    if a is None:
        fail('spawn light %s (None)' % name)
        return None
    c = K.find_comp(a, cls.__name__ if False else kind + 'Component')
    if c is None:
        for cc in K.ACT.ActorTools.get_components(a):
            if 'Light' in cc.get_class().get_name():
                c = cc
                break
    if c is None:
        warn('no light component on %s' % name)
        return a
    for prop, val in (('intensity', intensity), ('light_color', unreal.Color(*rgb)),
                      ('cast_shadows', shadows), ('visible', True)):
        try:
            c.set_editor_property(prop, val)
        except Exception as exc:
            warn('%s.%s: %r' % (name, prop, exc))
    if kind == 'PointLight':
        K.comp_set(c, 'attenuation_radius', radius, name)
    if kind == 'SpotLight':
        K.comp_set(c, 'attenuation_radius', radius, name)
        K.comp_set(c, 'inner_cone_angle', 30.0, name)
        K.comp_set(c, 'outer_cone_angle', 60.0, name)
    ACT.ActorTools.set_label(a, 'KL_' + name)
    return a


def place(asset_path, name, loc, rot=(0.0, 0.0, 0.0), scale=(1, 1, 1)):
    t = xform(loc, rot)
    # add_to_scene_from_asset() returns None for Blueprint assets in this
    # toolset build, so the generated class is spawned directly.
    try:
        a = SCENE.SceneTools.add_to_scene_from_class(K.bp_class(asset_path),
                                                     'KL_' + name, t)
    except Exception as exc:
        fail('place %s (%s): %r' % (name, asset_path, exc))
        return None
    if a is None:
        fail('place %s (%s) returned None' % (name, asset_path))
        return None
    ACT.ActorTools.set_label(a, 'KL_' + name)
    return a


def build_graybox():
    step('graybox geometry')
    walls = '%s/M_KL_WallUpper' % MAT
    wains = '%s/M_KL_Wainscot' % MAT
    floor = '%s/M_KL_Floor' % MAT
    ceil = '%s/M_KL_Ceiling' % MAT
    wood = '%s/M_KL_Wood' % MAT
    board = '%s/M_KL_Board' % MAT
    metal = '%s/M_KL_Metal' % MAT
    desk = '%s/M_KL_Desk' % MAT
    out = '%s/M_KL_Outside' % MAT

    made = []

    def add(*a, **kw):
        r = slab(*a, **kw)
        if r is not None:
            made.append(r)

    # ---- ground and sky --------------------------------------------------- #
    add('Ground', -3000, 3000, -3000, 3000, -30, 0, floor)
    add('Sky', -4000, 4000, -4000, 4000, 1200, 1300, out)

    # ---- entry corridor ---------------------------------------------------- #
    add('CorrFloor', CORR_X0 - 20, CORR_X1, CORR_Y0 - 20, CORR_Y1 + 20, 0, 8, floor)
    add('CorrCeil', CORR_X0 - 20, CORR_X1, CORR_Y0, CORR_Y1, HALL_H, HALL_H + 12, ceil)
    add('CorrWallS', CORR_X0 - 20, CORR_X1, CORR_Y0 - WALL_T, CORR_Y0, 0, HALL_H, walls)
    add('CorrWallN', CORR_X0 - 20, CORR_X1, CORR_Y1, CORR_Y1 + WALL_T, 0, HALL_H, walls)
    add('CorrWainS', CORR_X0 - 20, CORR_X1, CORR_Y0, CORR_Y0 + 4, 0, 110, wains)
    add('CorrWainN', CORR_X0 - 20, CORR_X1, CORR_Y1 - 4, CORR_Y1, 0, 110, wains)

    # ---- main hall ---------------------------------------------------------- #
    add('HallFloor', HALL_X0, HALL_X1, HALL_Y0, HALL_Y1, 0, 8, floor)
    add('HallCeil', HALL_X0, HALL_X1, HALL_Y0, HALL_Y1, HALL_H, HALL_H + 12, ceil)
    add('HallWallN', HALL_X0, HALL_X1, HALL_Y1, HALL_Y1 + WALL_T, 0, HALL_H, walls)
    add('HallWainN', HALL_X0, HALL_X1, HALL_Y1 - 4, HALL_Y1, 0, 110, wains)
    add('HallWallS1', HALL_X0, DOOR_X0, HALL_Y0 - WALL_T, HALL_Y0, 0, HALL_H, walls)
    add('HallWallS2', DOOR_X1, HALL_X1, HALL_Y0 - WALL_T, HALL_Y0, 0, HALL_H, walls)
    add('HallWallSDoor', DOOR_X0, DOOR_X1, HALL_Y0 - WALL_T, HALL_Y0, 240, HALL_H, walls)
    add('HallWainS1', HALL_X0, DOOR_X0, HALL_Y0, HALL_Y0 + 4, 0, 110, wains)
    add('HallWainS2', DOOR_X1, HALL_X1, HALL_Y0, HALL_Y0 + 4, 0, 110, wains)
    add('HallEndW', HALL_X1, HALL_X1 + WALL_T, HALL_Y0, HALL_Y1, 0, HALL_H, walls)
    add('HallJambW', HALL_X1 - 20, HALL_X1, HALL_Y0, HALL_Y0 + 40, 0, HALL_H, wood)
    add('HallJambE', HALL_X1 - 20, HALL_X1, HALL_Y1 - 40, HALL_Y1, 0, HALL_H, wood)
    # classroom 3 doorway frame
    add('DoorJambW', DOOR_X0 - 30, DOOR_X0, HALL_Y0 - WALL_T, HALL_Y0 + 10, 0, 250, wood)
    add('DoorJambE', DOOR_X1, DOOR_X1 + 30, HALL_Y0 - WALL_T, HALL_Y0 + 10, 0, 250, wood)
    add('DoorLintel', DOOR_X0 - 30, DOOR_X1 + 30, HALL_Y0 - WALL_T, HALL_Y0, 250, 280, wood)

    # ---- classroom 3 ---------------------------------------------------------- #
    add('RoomFloor', ROOM_X0, ROOM_X1, ROOM_Y0, ROOM_Y1, 0, 8, floor)
    add('RoomCeil', ROOM_X0, ROOM_X1, ROOM_Y0, ROOM_Y1, ROOM_H, ROOM_H + 12, ceil)
    add('RoomWallW', ROOM_X0 - WALL_T, ROOM_X0, ROOM_Y0, ROOM_Y1, 0, ROOM_H, walls)
    add('RoomWallE', ROOM_X1, ROOM_X1 + WALL_T, ROOM_Y0, ROOM_Y1, 0, ROOM_H, walls)
    add('RoomWallS', ROOM_X0, ROOM_X1, ROOM_Y1, ROOM_Y1 + WALL_T, 0, ROOM_H, walls)
    add('RoomWallSN', ROOM_X0, ROOM_X0 + 60, ROOM_Y0, ROOM_Y1, 0, ROOM_H, walls)
    add('RoomWallSS', ROOM_X1 - 60, ROOM_X1, ROOM_Y0, ROOM_Y1, 0, ROOM_H, walls)
    add('RoomWainS', ROOM_X0, ROOM_X1, ROOM_Y1 - 4, ROOM_Y1, 0, 110, wains)
    # chalkboard on the south wall
    add('ChalkBoard', 800, 1300, ROOM_Y1 - 12, ROOM_Y1 - 8, 110, 240, board)
    add('ChalkTray', 790, 1310, ROOM_Y1 - 24, ROOM_Y1 - 8, 100, 110, wood)
    # window frames on the east wall
    for i, (yy0, yy1) in enumerate(((300.0, 470.0), (600.0, 770.0))):
        add('Window%d' % i, ROOM_X1, ROOM_X1 + WALL_T, yy0, yy1, 130, 250, out)
    # teacher desk + student desks
    add('TeacherDesk', 900, 1200, 780, 880, 0, 75, desk)
    for r, yy in enumerate((520.0, 660.0)):
        for c, xx in enumerate((720.0, 950.0, 1180.0)):
            add('Desk%d%d' % (r, c), xx, xx + 120, yy, yy + 70, 0, 72, desk)
            add('Bench%d%d' % (r, c), xx + 20, xx + 100, yy - 40, yy - 30, 0, 45, desk)
    # stacked chairs in the far corner (dressing for the reveal)
    add('ChairStack', 1440, 1520, 760, 840, 0, 60, desk)
    add('ChairStack2', 1440, 1520, 760, 840, 60, 110, desk)
    # hall benches
    for i, xx in enumerate((-200.0, 400.0, 1200.0, 1700.0)):
        add('HallBench%d' % i, xx, xx + 160, -180, -120, 0, 45, desk)
    # notice board in the hall
    add('NoticeBoard', 100, 340, HALL_Y0 + 4, HALL_Y0 + 10, 120, 230, board)

    ok('slabs: %d' % len(made))
    return made


def build_lights():
    step('lighting')
    n = 0
    specs = [
        ('PointLight', 'HallLight0', (-150.0, 0.0, 300.0), 240.0, (1.0, 0.88, 0.70), 900.0),
        ('PointLight', 'HallLight1', (600.0, 0.0, 300.0), 190.0, (1.0, 0.86, 0.68), 900.0),
        ('PointLight', 'HallLight2', (1400.0, 0.0, 300.0), 190.0, (1.0, 0.86, 0.68), 900.0),
        ('PointLight', 'HallLight3', (1900.0, 0.0, 300.0), 150.0, (1.0, 0.84, 0.66), 800.0),
        ('PointLight', 'CorrLight', (-700.0, 0.0, 290.0), 120.0, (0.95, 0.92, 0.86), 700.0),
        ('PointLight', 'RoomLight', (1000.0, 520.0, 300.0), 150.0, (1.0, 0.90, 0.74), 1100.0),
        ('SpotLight', 'WindowShaft0', (1500.0, 385.0, 250.0), 900.0,
         (0.62, 0.74, 1.0), 1600.0, (-18.0, 0.0, 200.0)),
        ('SpotLight', 'WindowShaft1', (1500.0, 685.0, 250.0), 900.0,
         (0.62, 0.74, 1.0), 1600.0, (-18.0, 0.0, 200.0)),
        ('DirectionalLight', 'Moon', (0.0, 0.0, 900.0), 0.22, (0.55, 0.66, 0.95), 0.0,
         (-42.0, 26.0, 0.0)),
    ]
    for spec in specs:
        if light(*spec) is not None:
            n += 1
    ok('lights: %d' % n)


def build_props_and_start():
    step('place interactables + player start')
    place(K.F_PROPS + '/BP_KL_Prop_AttBook', 'AttBook', (1050.0, 830.0, 82.0),
          (0.0, 0.0, 12.0))
    place(K.F_PROPS + '/BP_KL_Prop_Roster', 'Roster', (1050.0, 880.0, 178.0))
    place(K.F_PROPS + '/BP_KL_Prop_TapeDeck', 'TapeDeck', (1930.0, 0.0, 120.0),
          (0.0, 0.0, -90.0))
    place(K.F_PROPS + '/BP_KL_Prop_Corner', 'Corner', (1470.0, 800.0, 150.0))
    t = xform(PLAYER_START, (0.0, PLAYER_YAW, 0.0))
    ps = SCENE.SceneTools.add_to_scene_from_class(unreal.PlayerStart.static_class(), 'KL_PlayerStart', t)
    if ps is None:
        fail('player start')
    else:
        ok('player start at %s' % (PLAYER_START,))


def configure_world():
    step('world settings')
    world = unreal.EditorLevelLibrary.get_editor_world()
    ws = world.get_world_settings()
    for prop, val in (('default_game_mode', K.bp_class(GM)),
                      ('kill_z', -400.0),
                      ('default_ambient_occlusion', 0.4)):
        try:
            ws.set_editor_property(prop, val)
            ok('WorldSettings %s = %s' % (prop, val if prop != 'default_game_mode'
                                          else GM))
        except Exception as exc:
            warn('WorldSettings %s: %r' % (prop, exc))
    K.save(K.MAP_PATH)


# --------------------------------------------------------------------------- #

def main():
    K.make_folders()
    build_props()
    step('create level %s' % K.MAP_PATH)
    # new_level() cannot overwrite, so an existing graybox is loaded and the
    # actors this build owns (label prefix KL_) are removed first.
    if unreal.load_asset(K.MAP_PATH) is not None:
        unreal.EditorLevelLibrary.load_level(K.MAP_PATH)
        world = unreal.EditorLevelLibrary.get_editor_world()
        doomed = [a for a in unreal.GameplayStatics.get_all_actors_of_class(
            world, unreal.Actor)
            if str(ACT.ActorTools.get_label(a)).startswith('KL_')]
        for a in doomed:
            SCENE.SceneTools.remove_from_scene(a)
        ok('cleared %d previous KL_ actors' % len(doomed))
    else:
        if not unreal.EditorLevelLibrary.new_level(K.MAP_PATH):
            fail('new_level %s' % K.MAP_PATH)
            return
    ok('level %s ready' % K.MAP_PATH)
    build_graybox()
    build_lights()
    build_props_and_start()
    configure_world()
    K.save(K.MAP_PATH)


K.run(main)
