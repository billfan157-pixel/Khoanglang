"""Khoang Lang 02:17 - capture the school furniture before and after.

Runs inside the FULL editor, because a commandlet has no render thread and
cannot take a screenshot. Same slate post-tick state machine as
art_90_shot.py, extended to visit two maps with the same camera poses so the
before and after are directly comparable:

    Lvl_KL_School3        the Milestone 1 greybox, untouched
    Lvl_KL_School3_ArtTest the copy carrying the imported furniture

The poses are chosen against the measured classroom, not guessed:
interior x 550..1550, y 200..900, floor top z = 8, chalkboard on the south wall
at y 890, reveal figure at (1470, 800).

Nothing is saved. The temporary camera is deleted and the editor is quit; if the
run dies mid-way the maps on disk are still exactly as they were, which is the
failure mode that matters here.

Launched by: art_96_schoolfurn_shot.ps1
"""

import math
import os
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
OUT = (r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217'
       r'\Saved\FurnitureShots')
RES = (1280, 720)
REP = os.path.join(OUT, 'shots_report.txt')

MAPS = [
    ('after', '/Game/KhoangLang/Maps/Lvl_KL_School3_ArtTest'),
    ('before', '/Game/KhoangLang/Maps/Lvl_KL_School3'),
]

# name, location, yaw, pitch, fov
POSES = [
    ('01_room_wide',   (640.0, 250.0, 170.0),  68.0, -3.0, 78.0),
    ('02_aisle',       (900.0, 420.0, 165.0),  82.0, -4.0, 70.0),
    ('03_front_left',  (700.0, 560.0, 150.0), 100.0, -8.0, 55.0),
    ('04_corner',      (1180.0, 640.0, 160.0), 28.0, -2.0, 72.0),
]

ST = {'phase': 'boot', 'map': 0, 'i': 0, 'settle': 0, 'wait': 0, 'cam': None,
      'shots': 0, 'reg': 0}
_REGISTERED = False


def log(m):
    line = str(m)
    unreal.log('SFSHOT: ' + line)
    try:
        with open(REP, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass


def quat(pitch, yaw, roll=0.0):
    sp, cp = math.sin(math.radians(pitch) / 2), math.cos(math.radians(pitch) / 2)
    sy, cy = math.sin(math.radians(yaw) / 2), math.cos(math.radians(yaw) / 2)
    sr, cr = math.sin(math.radians(roll) / 2), math.cos(math.radians(roll) / 2)
    return unreal.Quat(x=cr * sp * cy - sr * cp * sy,
                       y=-cr * sp * sy - sr * cp * cy,
                       z=cr * cp * sy - sr * sp * cy,
                       w=cr * cp * cy + sr * sp * sy)


def xform(loc, pitch=0.0, yaw=0.0):
    t = unreal.Transform()
    t.set_editor_property('translation', unreal.Vector(*loc))
    t.set_editor_property('rotation', quat(pitch, yaw))
    t.set_editor_property('scale3d', unreal.Vector(1, 1, 1))
    return t


def make_cam(loc, pitch, yaw, fov):
    from editor_toolset.toolsets import scene as SCENE
    old = ST.get('cam')
    if old is not None:
        try:
            SCENE.SceneTools.remove_from_scene(old)
        except Exception:
            pass
        ST['cam'] = None
    cam = SCENE.SceneTools.add_to_scene_from_class(
        unreal.CameraActor.static_class(), 'SFSHOT_Cam', xform(loc, pitch, yaw))
    if cam is None:
        return None
    try:
        for c in cam.get_components_by_class(unreal.CameraComponent):
            c.set_editor_property('field_of_view', fov)
    except Exception as exc:
        log('  camera settings: %r' % str(exc)[:90])
    ST['cam'] = cam
    try:
        unreal.EditorLevelLibrary.set_level_viewport_camera_info(
            unreal.Vector(*loc), unreal.Rotator(pitch, yaw, 0.0))
    except Exception:
        pass
    return cam


def shoot(path):
    """Render one frame.

    take_high_res_screenshot(width, height, path, camera) stack-overflows on
    this machine's Intel driver - it recursed until EXCEPTION_STACK_OVERFLOW,
    and the project's own art pass run only ever produced a single frame from
    it. The viewport route is used first instead: point the editor viewport at
    the pose, then ask AutomationLibrary to render whatever it is showing.
    """
    lib = unreal.AutomationLibrary
    attempts = [
        ('take_automation_high_res_screenshot', (RES[0], RES[1], path)),
        ('take_high_res_screenshot', (RES[0], RES[1], path)),
    ]
    for fn, args in attempts:
        if not hasattr(lib, fn):
            continue
        try:
            getattr(lib, fn)(*args)
            ST['shots'] += 1
            log('  shot via %s -> %s' % (fn, path))
            return True
        except Exception as exc:
            log('  %s: %s' % (fn, str(exc)[:130]))
    return False


def cleanup():
    from editor_toolset.toolsets import scene as SCENE
    try:
        unreal.unregister_slate_post_tick_callback(tick)
    except Exception:
        pass
    if ST.get('cam') is not None:
        try:
            SCENE.SceneTools.remove_from_scene(ST['cam'])
        except Exception:
            pass
        ST['cam'] = None
    world = unreal.EditorLevelLibrary.get_editor_world()
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if a.get_name().startswith('SFSHOT'):
            try:
                SCENE.SceneTools.remove_from_scene(a)
            except Exception:
                pass
    log('done: %d screenshots, no level was saved' % ST['shots'])


def tick(delta):
    try:
        p = ST['phase']
        if p == 'boot':
            ST['phase'] = 'load'
            return
        if p == 'load':
            tag, path = MAPS[ST['map']]
            unreal.EditorLevelLibrary.load_level(path)
            log('loaded %s (%s)' % (path, tag))
            ST['phase'] = 'settle'
            ST['settle'] = 0
            return
        if p == 'settle':
            # let streaming, lightmaps and first-time shader compiles finish
            ST['settle'] += 1
            if ST['settle'] > 200:
                ST['phase'] = 'pose'
                ST['wait'] = 20
            return
        if p == 'pose':
            if ST['wait'] > 0:
                ST['wait'] -= 1
                return
            tag, _ = MAPS[ST['map']]
            if ST['i'] >= len(POSES):
                ST['phase'] = 'switch'
                ST['wait'] = 10
                return
            name, loc, yaw, pitch, fov = POSES[ST['i']]
            cam = make_cam(loc, pitch, yaw, fov)
            ST['i'] += 1
            if cam is None:
                log('%s %s: camera spawn failed' % (tag, name))
                ST['wait'] = 20
                return
            path = os.path.join(OUT, '%s_%s.png' % (tag, name))
            shoot(path)
            ST['wait'] = 45
            return
        if p == 'switch':
            ST['map'] += 1
            ST['i'] = 0
            if ST['map'] >= len(MAPS):
                cleanup()
                unreal.SystemLibrary.quit_editor()
                return
            ST['phase'] = 'load'
            return
    except Exception:
        log(traceback.format_exc())
        try:
            cleanup()
        except Exception:
            pass
        try:
            unreal.SystemLibrary.quit_editor()
        except Exception:
            pass


def main():
    global _REGISTERED
    os.makedirs(OUT, exist_ok=True)
    if _REGISTERED:
        log('already registered, ignoring duplicate run')
        return
    _REGISTERED = True
    if os.path.exists(REP):
        os.remove(REP)
    log('shot run: %d maps x %d poses at %dx%d'
        % (len(MAPS), len(POSES), RES[0], RES[1]))
    unreal.register_slate_post_tick_callback(tick)
    log('post-tick callback registered')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        log(traceback.format_exc())
        log('BOOT FAILED')
