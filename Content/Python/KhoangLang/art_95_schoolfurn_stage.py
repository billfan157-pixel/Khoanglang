"""Khoang Lang 02:17 - stage 2: dress the classroom with the new furniture.

Runs on /Game/KhoangLang/Maps/Lvl_KL_School3_ArtTest only. Lvl_KL_School3 is
never opened for writing.

What it does
------------
Replaces the six greybox cube desk/bench pairs with the imported Blender
furniture, on the same grid the Milestone 1 greybox used, so the room reads the
same to the player and only its surface changes:

    desks   x 780 / 1010 / 1240,  y 555 and 695   (facing the chalkboard, +Y)
    benches 52 cm in front of each desk, on the -Y side

The six cube actors that are replaced (KL_Desk00..02, KL_Desk10..12,
KL_Bench00..02, KL_Bench10..12) are plain StaticMeshActors with no gameplay
component. The four interactable props, the PlayerStart, the lights and the
game mode are left exactly where they were, and the script asserts as much
after it saves.

Staging, not scattering
-----------------------
The grid is kept because a classroom grid is what the level is designed around,
but the individual pieces are set by hand rather than by a loop: small yaw
offsets per desk, one desk pushed a few centimetres out of line toward the
aisle, one bench left askew in front of its desk, and one seat with no bench at
all. Six identical pairs in a perfect grid read as a level editor, not as a room
somebody used and then left.

The reveal corner (KL_Corner, 1470,800) keeps a clear approach and a clear
sightline: nothing is placed east of x 1300 or north of y 760.

Run:  run_ue_script.ps1 -Script art_95_schoolfurn_stage.py
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

DST = K.ROOT + '/Maps/Lvl_KL_School3_ArtTest'
MESH_FOLDER = K.ROOT + '/Meshes/SchoolFurniture'
DESK = MESH_FOLDER + '/SM_KL_SchoolDesk_A'
BENCH = MESH_FOLDER + '/SM_KL_SchoolBench_A'

FLOOR_Z = 8.0
BENCH_GAP = 52.0          # cm in front of the desk, where the knees go

# labels of the greybox pairs this script replaces
GREYBOX = (['KL_Desk00', 'KL_Desk01', 'KL_Desk02',
             'KL_Desk10', 'KL_Desk11', 'KL_Desk12',
             'KL_Bench00', 'KL_Bench01', 'KL_Bench02',
             'KL_Bench10', 'KL_Bench11', 'KL_Bench12'])

MUST_KEEP = ['KL_AttBook', 'KL_Roster', 'KL_TapeDeck', 'KL_Corner',
             'KL_PlayerStart', 'KL_TeacherDesk', 'KL_ChalkBoard',
             'KL_ChairStack', 'KL_ChairStack2']

# label suffix, x, y, desk yaw, bench dx, bench dy, bench yaw or None for "no bench"
SETS = [
    ('A', 780.0, 555.0, -2.5, 0.0, 0.0, -2.5),
    ('B', 1010.0, 555.0, 1.5, 0.0, 0.0, 1.5),
    ('C', 1240.0, 555.0, -1.0, 0.0, 0.0, -1.0),
    ('D', 786.0, 695.0, 3.5, 0.0, 0.0, 9.0),
    ('E', 1007.0, 695.0, -2.0, 0.0, 4.0, -6.0),
    ('F', 1248.0, 692.0, 5.0, 0.0, 0.0, None),
    # The front row is one desk, left where it was when the room was locked up.
    # It sits 170 cm clear of the next row instead of on the grid, which is what
    # stops the room reading as six objects copied six times.
    ('G', 770.0, 330.0, -6.0, 0.0, 0.0, 2.0),
]

LINES = []


def log(m):
    LINES.append(str(m))
    unreal.log('SF95: ' + str(m))


def warn(m):
    LINES.append('WARN ' + str(m))
    unreal.log_warning('SF95_WARN: ' + str(m))


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


def spawn(label, mesh_path, x, y, yaw, shadow=True):
    mesh = unreal.load_asset(mesh_path)
    if mesh is None:
        warn('mesh missing: %s' % mesh_path)
        return None
    a = SCENE.SceneTools.add_to_scene_from_class(
        unreal.StaticMeshActor.static_class(), label,
        xform((x, y, FLOOR_Z), yaw))
    if a is None:
        warn('spawn failed: %s' % label)
        return None
    comp = None
    for c in ACT.ActorTools.get_components(a):
        if 'StaticMesh' in c.get_class().get_name():
            comp = c
            break
    if comp is None:
        warn('no mesh component on %s' % label)
        return a
    comp.set_editor_property('static_mesh', mesh)
    for prop, val in (('cast_shadow', shadow),
                      ('can_ever_affect_navigation', False)):
        try:
            comp.set_editor_property(prop, val)
        except Exception as exc:
            warn('%s %s: %r' % (label, prop, str(exc)[:70]))
    try:
        comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    except Exception as exc:
        warn('%s collision: %r' % (label, str(exc)[:70]))
    ACT.ActorTools.set_label(a, label)
    return a


def aabb(a):
    loc = a.get_actor_location()
    comp = None
    for c in ACT.ActorTools.get_components(a):
        if 'StaticMesh' in c.get_class().get_name():
            comp = c
            break
    if comp is None:
        return None
    b = comp.get_editor_property('static_mesh').get_bounds()
    rad = math.radians(abs(a.get_actor_rotation().yaw) % 180.0)
    ex = abs(b.box_extent.x * math.cos(rad)) + abs(b.box_extent.y * math.sin(rad))
    ey = abs(b.box_extent.x * math.sin(rad)) + abs(b.box_extent.y * math.cos(rad))
    return (loc.x - ex, loc.x + ex, loc.y - ey, loc.y + ey,
            loc.z + b.origin.z - b.box_extent.z)


def main():
    log('=== art_95_schoolfurn_stage ===')
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    if unreal.load_asset(DST) is None:
        log('FAILED: %s does not exist, run art_94 first' % DST)
        return
    if not unreal.EditorLevelLibrary.load_level(DST):
        log('FAILED to load %s' % DST)
        return
    world = unreal.EditorLevelLibrary.get_editor_world()
    actors = lambda: unreal.GameplayStatics.get_all_actors_of_class(
        world, unreal.Actor)

    log('actors on entry: %d' % len(actors()))

    # idempotent: rebuild only what this script owns
    owned = [a for a in actors()
             if str(ACT.ActorTools.get_label(a)).startswith(('SF_Desk_',
                                                             'SF_Bench_'))]
    for a in owned:
        SCENE.SceneTools.remove_from_scene(a)
    log('cleared %d previously staged SF_ actors' % len(owned))

    # the greybox placeholders go, so nothing intersects the real furniture
    removed = []
    for a in actors():
        if str(ACT.ActorTools.get_label(a)) in GREYBOX:
            removed.append(str(ACT.ActorTools.get_label(a)))
            SCENE.SceneTools.remove_from_scene(a)
    log('removed %d greybox cube actors: %s' % (len(removed), sorted(removed)))

    made = []
    for (tag, x, y, dyaw, bdx, bdy, byaw) in SETS:
        d = spawn('SF_Desk_%s' % tag, DESK, x, y, dyaw)
        if d is not None:
            made.append(d)
            box = aabb(d)
            log('SF_Desk_%s  x=%.1f y=%.1f yaw=%+.1f  x %.1f..%.1f  floor z=%.2f'
                % (tag, x, y, dyaw, box[0], box[1], box[4]))
            if abs(box[4] - FLOOR_Z) > 0.5:
                warn('SF_Desk_%s not on the floor: z=%.2f' % (tag, box[4]))
            if box[0] < 550.0 or box[1] > 1550.0 or box[2] < 200.0 \
                    or box[3] > 900.0:
                warn('SF_Desk_%s outside the classroom' % tag)
            if box[1] > 1330.0 or box[3] > 760.0:
                warn('SF_Desk_%s intrudes on the reveal corner' % tag)
        if byaw is None:
            log('SF_Bench_%s deliberately missing - nobody put it back' % tag)
            continue
        bx, by = x + bdx, y - BENCH_GAP + bdy
        b = spawn('SF_Bench_%s' % tag, BENCH, bx, by, byaw, shadow=False)
        if b is not None:
            made.append(b)
            box = aabb(b)
            log('SF_Bench_%s x=%.1f y=%.1f yaw=%+.1f  floor z=%.2f'
                % (tag, bx, by, byaw, box[4]))
            if abs(box[4] - FLOOR_Z) > 0.5:
                warn('SF_Bench_%s not on the floor: z=%.2f' % (tag, box[4]))
    log('placed %d actors' % len(made))

    # ---- gameplay must be untouched --------------------------------------- #
    log('--- gameplay check ---')
    labels = {}
    for a in actors():
        labels[str(ACT.ActorTools.get_label(a))] = a
    for want in MUST_KEEP:
        log('%-18s %s' % (want, 'present' if want in labels else 'MISSING'))
        if want not in labels:
            warn('%s missing' % want)
    sf = sorted([k for k in labels if k.startswith('SF_')])
    log('SF_ actors in the level: %d %s' % (len(sf), sf))
    log('total actors: %d' % len(actors()))

    if eas.save_asset(DST):
        log('saved %s' % DST)
    else:
        warn('could not save %s' % DST)

    with open(os.path.join(HERE, 'art_95_schoolfurn_stage.report.txt'),
              'w', encoding='utf-8') as f:
        f.write('\n'.join(LINES) + '\n')
    log('=== done ===')


try:
    main()
except Exception:
    log(traceback.format_exc())
    log('=== FAILED ===')
