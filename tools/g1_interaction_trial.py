"""Probe actual G1 camera-ray interactions after explicit debug positioning.

This does not certify walking routes or physical keyboard controls.
"""
import json
from pathlib import Path
import time
import traceback
import unreal

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
if world is None or '/G1Canon/' not in world.get_path_name():
    raise RuntimeError('Fresh canonical school PIE required')
loop = unreal.GameplayStatics.get_actor_of_class(world, unreal.load_class(None,
    '/Game/KhoangLang/Production/G1Canon/BP_KL_SchoolLoop.BP_KL_SchoolLoop_C'))
pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
controller = unreal.GameplayStatics.get_player_controller(world, 0)
camera = unreal.GameplayStatics.get_player_camera_manager(world, 0)
if not loop or not pawn:
    raise RuntimeError('Possessed pawn and loop required')
target = Path(unreal.Paths.project_dir()) / 'docs/agent/EVIDENCE/G1_camera_interactions.json'
report = {'status': 'running', 'method': 'Debug positioning; real camera trace and Interact Blueprint',
          'scope_limit': 'No physical input or walking-route qualification', 'targets': []}
tasks = [('LamActor', 'bLamWitness', (180, 0)),
         ('NotebookActor', 'bNotebook', (150, 0)),
         ('LedgerActor', 'bLedger', (180, 0)),
         ('ListenActor', 'bWorkingAvailable', (0, -180))]
state = {'index': 0, 'phase': 0, 'at': time.monotonic(), 'phase_at': 0., 'handle': None}


def finish(status):
    report['status'] = status
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    if state['handle'] is not None:
        unreal.unregister_slate_post_tick_callback(state['handle'])
        state['handle'] = None


def tick(delta):
    try:
        if time.monotonic() - state['at'] > 30:
            raise TimeoutError('Interaction trial exceeded wall-clock bound')
        name, flag, offset = tasks[state['index']]
        actor = loop.get_editor_property(name)
        bounds = actor.get_actor_bounds(False)
        aim = bounds[0]
        if name == 'LamActor':
            # The seated silhouette's box centre falls in empty air ahead of
            # its torso. Aim at the visible head, not an empty bounding point.
            transform = actor.get_actor_transform()
            aim = unreal.MathLibrary.transform_location(transform, unreal.Vector(0, 11, 63))
        if state['phase'] == 0:
            loc = actor.get_actor_location()
            position = unreal.Vector(loc.x + offset[0], loc.y + offset[1], 98)
            pawn.set_actor_location(position, False, True)
            if name == 'ListenActor' and not loop.get_editor_property('bEcho'):
                loop.call_method('ToggleEcho', ())
            state['phase'] = 1
            state['phase_at'] = time.monotonic()
            return
        if state['phase'] == 1:
            controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(
                camera.get_camera_location(), aim))
            if time.monotonic() - state['phase_at'] < .4:
                return
            state['phase'] = 2
            state['phase_at'] = time.monotonic()
            return
        if time.monotonic() - state['phase_at'] < .25:
            return
        start = camera.get_camera_location()
        end = start + unreal.MathLibrary.get_forward_vector(camera.get_camera_rotation()) * 300
        hit = unreal.SystemLibrary.line_trace_single(world, start, end,
            unreal.TraceTypeQuery.ECC_VISIBILITY, False, [], unreal.DrawDebugTrace.NONE, True)
        hit_actor = hit.to_tuple()[9] if hit else None
        loop.call_method('Interact', ())
        row = {'target': name, 'expected_actor': actor.get_path_name(),
               'hit_actor': hit_actor.get_path_name() if hit_actor else None,
               'camera': [start.x, start.y, start.z],
               'ray_end': [end.x, end.y, end.z],
               'hit_label': hit_actor.get_actor_label() if hit_actor else None,
               'target_center': [aim.x, aim.y, aim.z],
               'acquired': bool(loop.get_editor_property(flag)),
               'message': loop.get_editor_property('Message')}
        row['pass'] = hit_actor == actor and row['acquired']
        report['targets'].append(row)
        if name == 'ListenActor':
            row['heard_not_fabricated'] = not loop.get_editor_property('bObserved')
            row['pass'] = row['pass'] and row['heard_not_fabricated']
        state['index'] += 1
        state['phase'] = 0
        if state['index'] == len(tasks):
            unreal.SystemLibrary.execute_console_command(world, 'Shot')
            finish('passed' if all(r['pass'] for r in report['targets']) else 'failed')
    except Exception:
        report['error'] = traceback.format_exc()
        finish('failed')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
print('G1_INTERACTION_TRIAL_STARTED')
