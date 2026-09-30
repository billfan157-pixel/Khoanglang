"""Khoang Lang 02:17 - capture the art pass for visual review (art step 5).

Runs inside the FULL editor (not a commandlet) because screenshots need a real
render thread. A commandlet has no tick loop, so the capture is driven by a
slate post-tick callback: each tick advances one step of a small state machine
that settles the view, fires one screenshot, then moves on.

Views are chosen to judge the things that actually matter for this art pass:
the corridor read, the classroom read, the furniture close up, the moonlight
through the windows, and the staged reveal in the corner.

The figure is temporarily unhidden for the reveal shot and hidden again after,
so the level that gets saved still starts with the corner empty.

Launched by:  art_90_shot.ps1
"""

import math
import os
import sys
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import kl_core as K   # noqa: E402
from editor_toolset.toolsets import actor as ACT  # noqa: E402

OUT = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Saved\ArtShots'
MAP = K.ROOT + '/Maps/Lvl_KL_School3_Art'
RES = (1280, 720)
REP = os.path.join(OUT, 'shots_report.txt')

# name, location, yaw, pitch, fov
POSES = [
    ('01_corridor_entry',   (-950.0, 0.0, 165.0),     0.0,   0.0, 75.0),
    ('02_hall_west',        (-330.0, 0.0, 165.0),     0.0,  -2.0, 75.0),
    ('03_hall_east_pa',     (1500.0, -20.0, 165.0),   6.0,  -3.0, 70.0),
    ('04_classroom_door',   (872.0, 250.0, 165.0),   16.0,  -4.0, 78.0),
    ('05_classroom_desks',  (1050.0, 300.0, 150.0),  86.0,  -6.0, 70.0),
    ('06_classroom_board',  (1050.0, 480.0, 150.0),   0.0,   2.0, 72.0),
    ('07_moonlight_desks',  (1230.0, 500.0, 110.0),  62.0, -10.0, 74.0),
    ('08_corner_reveal',    (1180.0, 620.0, 150.0),  -26.0,  -6.0, 62.0),
    ('09_corner_after',     (1250.0, 700.0, 150.0),  -18.0,  -4.0, 66.0),
]

ST = {'phase': 'boot', 'i': 0, 'wait': 0, 'cam': None, 'shots': 0,
      'settle': 0, 'fired': set(), 'reg': 0}
_REGISTERED = False


def log(m):
    line = str(m)
    unreal.log('SHOT: ' + line)
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
                       z=cr * sp * cy - sr * sp * cy,
                       w=cr * cp * cy + sr * sp * sy)


def xform(loc, pitch=0.0, yaw=0.0):
    t = unreal.Transform()
    t.set_editor_property('translation', unreal.Vector(*loc))
    t.set_editor_property('rotation', quat(pitch, yaw))
    t.set_editor_property('scale3d', unreal.Vector(1, 1, 1))
    return t


def set_figure_visible(v):
    world = unreal.EditorLevelLibrary.get_editor_world()
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if str(ACT.ActorTools.get_label(a)) == 'ART_Corner':
            for c in ACT.ActorTools.get_components(a):
                if 'StaticMesh' in c.get_class().get_name():
                    for prop in ('hidden_in_game', 'visible'):
                        try:
                            c.set_editor_property(prop, not v)
                        except Exception:
                            pass
            # also light the corner the way the reveal does
            for c in ACT.ActorTools.get_components(a):
                if 'PointLight' in c.get_class().get_name():
                    try:
                        c.set_editor_property('intensity', 18.0 if v else 0.0)
                    except Exception:
                        pass
            log('  figure %s' % ('shown' if v else 'hidden'))
            return True
    return False


def make_cam(loc, pitch, yaw, fov):
    from editor_toolset.toolsets import scene as SCENE
    old = ST.get('cam')
    if old is not None:
        try:
            SCENE.SceneTools.remove_from_scene(old)
        except Exception:
            pass
    cam = SCENE.SceneTools.add_to_scene_from_class(
        unreal.CameraActor.static_class(), 'SHOT_Cam', xform(loc, pitch, yaw))
    if cam is None:
        log('camera spawn failed')
        return None
    for c in ACT.ActorTools.get_components(cam):
        if 'Camera' in c.get_class().get_name():
            for prop, val in (('field_of_view', fov), ('max_ortho_width', 1000.0)):
                try:
                    c.set_editor_property(prop, val)
                except Exception:
                    pass
    ST['cam'] = cam
    # put the editor viewport in the same place, so the on-screen view matches
    try:
        unreal.EditorLevelLibrary.set_level_viewport_camera_info(
            unreal.Vector(*loc), unreal.Rotator(pitch, yaw, 0.0))
    except Exception as exc:
        log('  viewport camera: %r' % str(exc)[:80])
    return cam


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
    set_figure_visible(False)
    world = unreal.EditorLevelLibrary.get_editor_world()
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if str(ACT.ActorTools.get_label(a)).startswith('SHOT_'):
            try:
                SCENE.SceneTools.remove_from_scene(a)
            except Exception:
                pass
    # re-save so the shipped level still starts with the corner empty
    try:
        unreal.EditorAssetLibrary.save_asset(MAP)
        log('level re-saved with the corner hidden')
    except Exception as exc:
        log('save: %r' % str(exc)[:100])
    log('done: %d screenshots' % ST['shots'])


def tick(delta):
    try:
        p = ST['phase']
        if p == 'boot':
            ST['phase'] = 'load'
            return
        if p == 'load':
            unreal.EditorLevelLibrary.load_level(MAP)
            log('level loaded, waiting for shaders')
            ST['phase'] = 'settle'
            ST['settle'] = 0
            return
        if p == 'settle':
            # let streaming, lightmaps and shader compiles finish before judging
            ST['settle'] += 1
            if ST['settle'] > 180:
                ST['phase'] = 'pose'
                ST['wait'] = 12
            return
        if p == 'pose':
            if ST['wait'] > 0:
                ST['wait'] -= 1
                return
            if ST['i'] >= len(POSES):
                ST['phase'] = 'done'
                log('all poses dispatched')
                cleanup()
                unreal.SystemLibrary.quit_editor()
                return
            idx = ST['i']
            name, loc, yaw, pitch, fov = POSES[idx]
            if name == '08_corner_reveal':
                set_figure_visible(True)
            cam = make_cam(loc, pitch, yaw, fov)
            ST['i'] = idx + 1
            if cam is None:
                log('pose %d (%s): no camera' % (idx, name))
                ST['wait'] = 12
                return
            path = os.path.join(OUT, name + '.png')
            try:
                unreal.AutomationLibrary.take_high_res_screenshot(
                    RES[0], RES[1], path, cam)
                ST['shots'] += 1
                log('pose %d/%d %s -> %s' % (idx + 1, len(POSES), name, path))
            except Exception as exc:
                log('pose %d %s FAILED: %r' % (idx, name, str(exc)[:150]))
            ST['wait'] = 30
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
        # -ExecCmds can run the script more than once; a second tick callback
        # would double-dispatch every pose.
        log('already registered, ignoring duplicate run')
        return
    _REGISTERED = True
    if os.path.exists(REP):
        os.remove(REP)
    log('shot run start: %d poses at %dx%d' % (len(POSES), RES[0], RES[1]))
    unreal.register_slate_post_tick_callback(tick)
    log('post-tick callback registered')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        log(traceback.format_exc())
        log('BOOT FAILED')
