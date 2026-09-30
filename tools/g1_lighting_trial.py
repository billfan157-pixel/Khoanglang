"""Capture real G1 PIE exposure candidates. Runtime fixtures, no asset saves."""
import hashlib
import json
from pathlib import Path
import shutil
import time
import traceback
import unreal

ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / 'docs/agent/EVIDENCE'
SHOTS = ROOT / 'Saved/Screenshots/WindowsEditor'
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
if world is None or '/G1Canon/' not in world.get_path_name():
    raise RuntimeError('Canonical school PIE required')
pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
pc = unreal.GameplayStatics.get_player_controller(world, 0)
camera = unreal.GameplayStatics.get_player_camera_manager(world, 0)
lamp = pawn.get_component_by_class(unreal.SpotLightComponent)
grade = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world,
    unreal.PostProcessVolume) if a.get_editor_property('priority') == 100)
cases = []
for bias in (-1., -3.):
    for name, position, rotation in (
            ('entry', (-880, 0, 98), (0, 0)),
            ('hall', (300, 0, 98), (0, 0)),
            ('classroom', (870, 180, 98), (0, 90))):
        for torch in (False, True):
            cases.append((bias, name, position, rotation, torch))
report = {'status': 'running', 'scope': 'Runtime exposure fixtures, inspected images required; no assets changed',
          'map_sha256': hashlib.sha256((ROOT /
            'Content/KhoangLang/Production/G1Canon/Lvl_KL_SchoolSlice.umap').read_bytes()).hexdigest(),
          'captures': []}
state = {'index': 0, 'phase': 0, 'at': time.monotonic(), 'start': time.monotonic(),
         'seen': set(SHOTS.glob('*.png')), 'handle': None}


def save():
    (OUT / 'G1_lighting_candidates.json').write_text(json.dumps(report, indent=2), encoding='utf-8')


def stop(status):
    report['status'] = status
    save()
    unreal.unregister_slate_post_tick_callback(state['handle'])


def tick(delta):
    try:
        if time.monotonic() - state['start'] > 90:
            raise TimeoutError('Lighting capture wall-clock bound reached')
        bias, name, position, rotation, torch = cases[state['index']]
        if state['phase'] == 0:
            settings = grade.get_editor_property('settings')
            settings.set_editor_property('auto_exposure_bias', bias)
            grade.set_editor_property('settings', settings)
            pawn.set_actor_location(unreal.Vector(*position), False, True)
            pc.set_control_rotation(unreal.Rotator(pitch=rotation[0], yaw=rotation[1], roll=0))
            lamp.set_visibility(torch, True)
            lamp.set_hidden_in_game(not torch, True)
            # Bounded low-intensity flashlight candidate; runtime fixture only.
            lamp.set_editor_property('intensity', 90.)
            state['phase'] = 1
            state['at'] = time.monotonic()
            return
        if state['phase'] == 1:
            if time.monotonic() - state['at'] < .8:
                return
            state['seen'] = set(SHOTS.glob('*.png'))
            unreal.SystemLibrary.execute_console_command(world, 'Shot')
            state['phase'] = 2
            return
        files = set(SHOTS.glob('*.png')) - state['seen']
        if not files:
            return
        shot = max(files, key=lambda p: p.stat().st_mtime_ns)
        path = OUT / ('G1_ev%d_%s_%s.png' % (int(bias), name, 'on' if torch else 'off'))
        shutil.copyfile(shot, path)
        loc = camera.get_camera_location()
        report['captures'].append({'bias_ev': bias, 'scene': name, 'torch': torch,
            'torch_lumens': 90, 'camera': [loc.x, loc.y, loc.z],
            'path': path.relative_to(ROOT).as_posix(), 'screenshot_source': shot.name,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        save()
        state['index'] += 1
        state['phase'] = 0
        if state['index'] == len(cases):
            stop('captured')
    except Exception:
        report['error'] = traceback.format_exc()
        stop('failed')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
save()
print('G1_LIGHTING_TRIAL_STARTED')
