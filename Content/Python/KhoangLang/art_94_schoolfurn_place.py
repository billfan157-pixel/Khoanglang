"""Khoang Lang 02:17 - stage 1: validate one desk and one bench in School No. 3.

Duplicates /Game/KhoangLang/Maps/Lvl_KL_School3 to
/Game/KhoangLang/Maps/Lvl_KL_School3_ArtTest first, then places exactly one desk
and one bench in the copy and measures them. The original map is opened read
only and never saved.

The layout facts this script works from were measured by
art_93_schoolfurn_inspect.py, not assumed:

    classroom interior   x 550 .. 1550,  y 200 .. 900
    floor top            z = 8   (KL_RoomFloor spans z 0..8)
    chalkboard           y 890, faces -Y, so desks face +Y
    existing graybox     6 cube desks (120x70x72) at y 555 / 695,
                         x 780 / 1010 / 1240, with cube benches 70 cm in front
    gameplay props       KL_AttBook (1050,830) on the teacher's desk
                         KL_Roster  (1050,880) on the chalkboard
                         KL_Corner  (1470,800) the reveal figure - keep clear
                         KL_TapeDeck(1930,0) in the hall
    doorways             hall south wall x 800..940 (Milestone 1 put it on the
                         wrong side of the building; not this script's problem
                         to fix, but nothing is placed in front of it)

The Blender desk faces -Y at yaw 0, and the FBX import preserved the axes, so
yaw 0 already points a pupil at the chalkboard. The bench sits 52 cm in front,
which is where a pupil's knees go.

Run:  run_ue_script.ps1 -Script art_94_schoolfurn_place.py
"""

import math
import os
import sys
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import kl_core as K  # noqa: E402
from editor_toolset.toolsets import scene as SCENE  # noqa: E402
from editor_toolset.toolsets import actor as ACT     # noqa: E402

SRC = K.ROOT + '/Maps/Lvl_KL_School3'
DST = K.ROOT + '/Maps/Lvl_KL_School3_ArtTest'
MESH_FOLDER = K.ROOT + '/Meshes/SchoolFurniture'
DESK = MESH_FOLDER + '/SM_KL_SchoolDesk_A'
BENCH = MESH_FOLDER + '/SM_KL_SchoolBench_A'

# measured, see art_93_schoolfurn_inspect.py
ROOM_X0, ROOM_X1 = 550.0, 1550.0
ROOM_Y0, ROOM_Y1 = 200.0, 900.0
FLOOR_Z = 8.0
WALL = 20.0

# The one set placed in this pass, staged in the empty strip between the north
# wall and the first row of desks rather than dropped on top of anything.
PROBE = dict(label='SF_Desk_Probe', mesh=DESK, x=770.0, y=330.0, yaw=0.0)
PROBE_B = dict(label='SF_Bench_Probe', mesh=BENCH, x=770.0, y=278.0, yaw=0.0)

# Actors whose footprint the furniture must stay clear of, with a margin.
PROTECTED = [
    ('KL_Corner', 1470.0, 800.0, 140.0),      # the reveal
    ('KL_AttBook', 1050.0, 830.0, 70.0),
    ('KL_Roster', 1050.0, 880.0, 70.0),
    ('KL_TapeDeck', 1930.0, 0.0, 70.0),
    ('KL_TeacherDesk', 1050.0, 830.0, 190.0),
    ('KL_ChalkBoard', 1050.0, 890.0, 280.0),
    ('KL_ChairStack', 1480.0, 800.0, 90.0),
    ('KL_ChairStack2', 1480.0, 800.0, 90.0),
    ('KL_Window0', 1560.0, 385.0, 110.0),
    ('KL_Window1', 1560.0, 685.0, 110.0),
    ('KL_DoorJambW', 785.0, -205.0, 60.0),
    ('KL_DoorJambE', 955.0, -205.0, 60.0),
]

LINES = []


def log(m):
    line = str(m)
    LINES.append(line)
    unreal.log('SF94: ' + line)


def warn(m):
    LINES.append('WARN ' + str(m))
    unreal.log_warning('SF94_WARN: ' + str(m))


def quat(pitch, yaw, roll=0.0):
    sp, cp = math.sin(math.radians(pitch) / 2), math.cos(math.radians(pitch) / 2)
    sy, cy = math.sin(math.radians(yaw) / 2), math.cos(math.radians(yaw) / 2)
    sr, cr = math.sin(math.radians(roll) / 2), math.cos(math.radians(roll) / 2)
    return unreal.Quat(x=cr * sp * cy - sr * cp * sy,
                       y=-cr * sp * sy - sr * cp * cy,
                       z=cr * cp * sy - sr * sp * cy,
                       w=cr * cp * cy + sr * sp * sy)


def xform(loc, yaw=0.0):
    t = unreal.Transform()
    t.set_editor_property('translation', unreal.Vector(*loc))
    t.set_editor_property('rotation', quat(0.0, yaw))
    t.set_editor_property('scale3d', unreal.Vector(1.0, 1.0, 1.0))
    return t


def place(spec, shadow=True):
    mesh = unreal.load_asset(spec['mesh'])
    if mesh is None:
        warn('mesh missing: %s' % spec['mesh'])
        return None
    a = SCENE.SceneTools.add_to_scene_from_class(
        unreal.StaticMeshActor.static_class(), spec['label'],
        xform((spec['x'], spec['y'], FLOOR_Z), spec['yaw']))
    if a is None:
        warn('spawn failed: %s' % spec['label'])
        return None
    c = None
    for cc in ACT.ActorTools.get_components(a):
        if 'StaticMesh' in cc.get_class().get_name():
            c = cc
            break
    if c is None:
        warn('no mesh component on %s' % spec['label'])
        return a
    c.set_editor_property('static_mesh', mesh)
    for prop, val in (('cast_shadow', shadow),
                      ('can_ever_affect_navigation', False)):
        try:
            c.set_editor_property(prop, val)
        except Exception as exc:
            warn('%s %s: %r' % (spec['label'], prop, str(exc)[:70]))
    try:
        c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    except Exception as exc:
        warn('%s collision: %r' % (spec['label'], str(exc)[:70]))
    ACT.ActorTools.set_label(a, spec['label'])
    return a


def measure(a, name):
    """World bounds of the spawned actor, and the checks that matter."""
    if a is None:
        return None
    loc = a.get_actor_location()
    comp = None
    for c in ACT.ActorTools.get_components(a):
        if 'StaticMesh' in c.get_class().get_name():
            comp = c
            break
    if comp is None:
        return None
    sm = comp.get_editor_property('static_mesh')
    b = sm.get_bounds()
    # world AABB of the rotated local box, good enough for clearance checks
    yaw = a.get_actor_rotation().yaw
    rad = math.radians(abs(yaw) % 180.0)
    ex = abs(b.box_extent.x * math.cos(rad)) + abs(b.box_extent.y * math.sin(rad))
    ey = abs(b.box_extent.x * math.sin(rad)) + abs(b.box_extent.y * math.cos(rad))
    box = (loc.x - ex, loc.x + ex, loc.y - ey, loc.y + ey,
           loc.z + b.origin.z - b.box_extent.z,
           loc.z + b.origin.z + b.box_extent.z)
    log('%-18s loc=(%.1f, %.1f, %.1f) yaw=%.1f' % (name, loc.x, loc.y, loc.z, yaw))
    log('   world AABB x %.1f..%.1f  y %.1f..%.1f  z %.1f..%.1f'
        % (box[0], box[1], box[2], box[3], box[4], box[5]))

    problems = []
    if abs(box[4] - FLOOR_Z) > 0.5:
        problems.append('floor contact off by %.2f cm (want z=%.1f)'
                        % (box[4] - FLOOR_Z, FLOOR_Z))
    if box[0] < ROOM_X0 - WALL or box[1] > ROOM_X1 + WALL:
        problems.append('outside the classroom in X')
    if box[2] < ROOM_Y0 - WALL or box[3] > ROOM_Y1 + WALL:
        problems.append('outside the classroom in Y')
    for other, ox, oy, r in PROTECTED:
        dx = max(box[0] - ox, ox - box[1], 0.0)
        dy = max(box[2] - oy, oy - box[3], 0.0)
        if dx < r and dy < r:
            problems.append('overlaps the protected zone of %s (%.0f, %.0f)'
                            % (other, ox, oy))
    try:
        log('   collision=%s nav=%s shadow=%s material=%s'
            % (comp.get_collision_enabled(),
               comp.get_editor_property('can_ever_affect_navigation'),
               comp.get_editor_property('cast_shadow'),
               sm.get_material(0).get_name() if sm.get_material(0) else None))
    except Exception as exc:
        warn('%s component readback: %r' % (name, str(exc)[:80]))
    if problems:
        for p in problems:
            warn('%s: %s' % (name, p))
    else:
        log('   checks: floor contact ok, inside the room, clear of every '
            'protected zone')
    return box


def main():
    log('=== art_94_schoolfurn_place: stage 1, one desk + one bench ===')
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)

    if unreal.load_asset(DST) is None:
        log('duplicating %s -> %s' % (SRC, DST))
        if not eas.duplicate_asset(SRC, DST):
            log('FAILED to duplicate the map')
            return
    else:
        log('%s already exists; rebuilding its SF_ actors only' % DST)

    if not unreal.EditorLevelLibrary.load_level(DST):
        log('FAILED to load %s' % DST)
        return
    world = unreal.EditorLevelLibrary.get_editor_world()
    total_before = len(unreal.GameplayStatics.get_all_actors_of_class(
        world, unreal.Actor))

    # idempotent: clear only actors this script owns
    doomed = [a for a in unreal.GameplayStatics.get_all_actors_of_class(
        world, unreal.Actor)
        if str(ACT.ActorTools.get_label(a)).startswith('SF_')]
    for a in doomed:
        SCENE.SceneTools.remove_from_scene(a)
    log('cleared %d previous SF_ actors (of %d total)'
        % (len(doomed), total_before))

    desk = place(PROBE)
    bench = place(PROBE_B, shadow=False)
    log('--- measurements ---')
    measure(desk, 'SF_Desk_Probe')
    measure(bench, 'SF_Bench_Probe')

    # gameplay must still be intact in the copy
    for want in ('KL_AttBook', 'KL_Roster', 'KL_TapeDeck', 'KL_Corner',
                 'KL_PlayerStart'):
        hit = [a for a in unreal.GameplayStatics.get_all_actors_of_class(
            world, unreal.Actor) if str(ACT.ActorTools.get_label(a)) == want]
        log('gameplay %-16s %s' % (want, 'present' if hit else 'MISSING'))
        if not hit:
            warn('%s missing from the copy' % want)
    total_after = len(unreal.GameplayStatics.get_all_actors_of_class(
        world, unreal.Actor))
    log('actors: %d before -> %d after' % (total_before, total_after))

    if eas.save_asset(DST):
        log('saved %s' % DST)
    else:
        warn('could not save %s' % DST)

    with open(os.path.join(HERE, 'art_94_schoolfurn_place.report.txt'),
              'w', encoding='utf-8') as f:
        f.write('\n'.join(LINES) + '\n')
    log('=== done ===')


try:
    main()
except Exception:
    log(traceback.format_exc())
    log('=== FAILED ===')
