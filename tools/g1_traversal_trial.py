"""Exercise copied Move Blueprint and collision from entry to school evidence.

This drives the real CharacterMovement path with debug function calls. It does
not establish that physical keyboard or Enhanced Input events work.
"""
import json
from pathlib import Path
import traceback
import unreal

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
if world is None or '/Production/' not in world.get_path_name():
    raise RuntimeError('Production PIE required')
pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
controller = unreal.GameplayStatics.get_player_controller(world, 0)
camera = unreal.GameplayStatics.get_player_camera_manager(world, 0)
waypoints = [(-600, 0), (870, 0), (870, 430), (1340, 430), (1340, 800), (1250, 800)]
report = {'method': 'Move Blueprint debug calls and real CharacterMovement collision',
          'world': world.get_path_name(), 'status': 'running', 'waypoints': []}
target = Path(unreal.Paths.project_dir()) / 'docs/agent/EVIDENCE/G1_traversal_trial.json'
state = {'index': 0, 'started': unreal.GameplayStatics.get_time_seconds(world),
         'handle': None, 'focus_at': None}

def save():
    target.write_text(json.dumps(report, indent=2), encoding='utf-8')

def stop(status):
    report['status'] = status
    save()
    unreal.unregister_slate_post_tick_callback(state['handle'])

def tick(delta):
    try:
        now = unreal.GameplayStatics.get_time_seconds(world)
        if now - state['started'] > 30:
            loc = pawn.get_actor_location()
            raise TimeoutError('Route blocked at %s before waypoint %d' % (loc, state['index']))
        if state['index'] < len(waypoints):
            x, y = waypoints[state['index']]
            loc = pawn.get_actor_location()
            desired = unreal.Vector(x, y, loc.z)
            if (desired - loc).length() < 18:
                report['waypoints'].append({'index': state['index'],
                    'location': [loc.x, loc.y, loc.z], 'game_time': now})
                state['index'] += 1
                save()
                return
            rotation = unreal.MathLibrary.find_look_at_rotation(loc, desired)
            controller.set_control_rotation(rotation)
            pawn.call_method('Move', (0.0, 1.0))
        elif state['focus_at'] is None:
            pawn.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
            book_class = unreal.load_class(None, '/Game/KhoangLang/Production/Blueprints/Core/Props/BP_KL_Prop_AttBook.BP_KL_Prop_AttBook_C')
            book = unreal.GameplayStatics.get_actor_of_class(world, book_class)
            controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(
                camera.get_camera_location(), book.get_actor_location()))
            state['focus_at'] = now
        else:
            book_class = unreal.load_class(None, '/Game/KhoangLang/Production/Blueprints/Core/Props/BP_KL_Prop_AttBook.BP_KL_Prop_AttBook_C')
            book = unreal.GameplayStatics.get_actor_of_class(world, book_class)
            controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(
                camera.get_camera_location(), book.get_actor_location()))
            if now - state['focus_at'] < 1:
                return
            focus = pawn.get_editor_property('FocusCand')
            report['focus_owner'] = focus.get_owner().get_class().get_path_name() if focus else None
            if focus is None or focus.get_owner().get_class().get_name() != 'BP_KL_Prop_AttBook_C':
                raise AssertionError('View trace did not focus reachable attendance book')
            report['scope_limit'] = 'No physical keyboard proof; no canonical sentence or attention proof'
            unreal.SystemLibrary.execute_console_command(world, 'Shot')
            stop('passed')
    except Exception:
        report['error'] = traceback.format_exc()
        stop('failed')

save()
state['handle'] = unreal.register_slate_post_tick_callback(tick)
print('G1 traversal trial registered')
