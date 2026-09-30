"""Debug steer a fresh native Character through the actual school collision.

Run with exec(compile(source, __file__, 'exec'), an_isolated_namespace). Pass
G1_PIE_START_RESULT as the caller's StartPIE result, if available. All
callback state is additionally private to start_trial's closure. No actor or
pawn is repositioned: Move is the native player's gameplay Blueprint API and
CharacterMovement integrates every step. Control rotation is an explicit debug
fixture, not physical keyboard/mouse or remapping acceptance.

Any unresolved leg, unexpected pawn replacement/destruction, fall, wrong camera
target or unavailable evidence aborts the route. No waypoint skipping/recovery
teleports, editor changes or inferred cause for the prior deck disappearance.
"""


def start_trial(pie_start_result=None):
    import datetime
    import hashlib
    import json
    import math
    from pathlib import Path
    import time
    import traceback
    import unreal

    root = Path(unreal.Paths.project_dir())
    base = '/Game/KhoangLang/Production/G1Canon'
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = editor.get_game_world()
    if world is None or '/G1Canon/' not in world.get_path_name() or 'Lvl_KL_SchoolSlice' not in world.get_path_name():
        raise RuntimeError('Fresh canonical school PIE required')
    loop = unreal.GameplayStatics.get_actor_of_class(world, unreal.load_class(
        None, base + '/BP_KL_SchoolLoop.BP_KL_SchoolLoop_C'))
    pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
    controller = unreal.GameplayStatics.get_player_controller(world, 0)
    camera = unreal.GameplayStatics.get_player_camera_manager(world, 0)
    if not all((loop, pawn, controller, camera)):
        raise RuntimeError('Loop, possessed native player, controller and camera required')
    if pawn.get_class().get_path_name() != base + '/BP_KL_SchoolPlayer.BP_KL_SchoolPlayer_C':
        raise RuntimeError('Independent native SchoolPlayer required')
    for name, value in (('EntityState', 0), ('LossCount', 0), ('bNotebook', False),
                        ('bLedger', False), ('bLamWitness', False), ('bLeftSchool', False)):
        if loop.get_editor_property(name) != value:
            raise RuntimeError('Fresh PIE defaults required: ' + name)
    movement = pawn.get_component_by_class(unreal.CharacterMovementComponent)
    capsule = pawn.get_component_by_class(unreal.CapsuleComponent)
    if not movement or not capsule:
        raise RuntimeError('Native Character movement/capsule missing')

    # Hall centerline avoids its wall benches. Front cross-aisle y257 and
    # east classroom aisle x1400 avoid the 700/880/1060/1240 desk columns.
    # Actual attempt3 hit hall wall's classroom face atY220: capsule radius30
    # needs center>=250, so y257 lies between wall clearance and front desks.
    # The fallen chair at940/250 is a known potential front-aisle blocker:
    # this candidate route must fail visibly if real collision closes that gap.
    # Notebook +170x clears both the raised rear lid and platform edge.
    # Attempt4 stopped at X1205.29: X1200 is inside capsule/platform clearance.
    # Ledger is viewed diagonally
    # from the clear front aisle, +180x/+110y; no traversal through pupil desks.
    route = [
        ('entry corridor', (-600., 0.), None),
        ('hall entrance', (0., 0.), None),
        ('Lam hall approach', (560., 0.), None),
        ('Lam present witness', (740., -90.), 'LamActor'),
        ('return hall center', (740., 0.), None),
        ('east hall center', (1600., 0.), None),
        ('listening deck west approach', (1770., 0.), 'ListenActor'),
        ('return classroom hall', (870., 0.), None),
        ('classroom door', (870., 200.), None),
        ('classroom front cross aisle', (870., 257.), None),
        ('classroom east aisle entry', (1400., 257.), None),
        ('classroom east aisle', (1400., 790.), None),
        ('notebook east side', (1220., 790.), 'NotebookActor'),
        ('notebook retreat east', (1400., 790.), None),
        ('teacher front aisle east', (1400., 664.), None),
        ('ledger front aisle', (750., 664.), None),
        ('rice ledger diagonal side', (750., 680.), 'LedgerActor'),
        ('ledger retreat front aisle', (750., 664.), None),
        ('return east front aisle', (1400., 664.), None),
        ('return east cross aisle', (1400., 257.), None),
        ('return doorway aisle', (870., 257.), None),
        ('leave classroom doorway', (870., 200.), None),
        ('return hall', (870., 0.), None),
        ('return hall entrance', (0., 0.), None),
        ('return corridor', (-600., 0.), None),
        ('exit interior approach', (-800., -70.), 'ExitActor'),
    ]
    flags = {'LamActor': 'bLamWitness', 'ListenActor': 'bWorkingAvailable',
             'NotebookActor': 'bNotebook', 'LedgerActor': 'bLedger', 'ExitActor': 'bLeftSchool'}
    bound_files = {
        'canon': 'docs/story/Khoang_Lang_02_17_Cot_truyen_v3.md',
        'core_source': 'tools/g1_build_school_loop.py',
        'player_source': 'tools/g1_build_native_player.py',
        'trial_source': 'tools/g1_navigation_trial.py',
        'core_asset': 'Content/KhoangLang/Production/G1Canon/BP_KL_SchoolLoop.uasset',
        'player_asset': 'Content/KhoangLang/Production/G1Canon/BP_KL_SchoolPlayer.uasset',
        'map': 'Content/KhoangLang/Production/G1Canon/Lvl_KL_SchoolSlice.umap',
    }
    def hashes():
        return {key: {'path': path, 'sha256': hashlib.sha256((root / path).read_bytes()).hexdigest()}
                for key, path in bound_files.items()}

    def xyz(value):
        return [float(value.x), float(value.y), float(value.z)]

    def distance(a, point):
        return math.hypot(float(a.x) - point[0], float(a.y) - point[1])

    target = root / 'docs/agent/EVIDENCE/G1_navigation_trial.json'
    initial_game_time = float(unreal.GameplayStatics.get_time_seconds(world))
    report = {
        'status': 'running', 'method': 'Native Move Blueprint, actual game Tick and collision; debug control-rotation steering',
        'scope_limit': 'No physical keyboard/mouse, remapping, packaged performance, or complete narrative acceptance',
        'prior_deck_disappearance': 'Cause unresolved; no source destroy/damage operation found in core/native player. This run diagnoses survival rather than inferring a cause.',
        'binding': {'world': world.get_path_name(), 'pawn': pawn.get_path_name(),
                    'pawn_class': pawn.get_class().get_path_name(),
                    'start_game_time': initial_game_time,
                    'pie_start_result': str(pie_start_result) if pie_start_result is not None else 'not supplied',
                    'pie_session_note': 'Fresh source defaults are asserted; this script does not start PIE or establish a newly created session. An already-running PIE may have earlier presentation cues.',
                    'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    'files_at_start': hashes(),
                    'qualification': 'Saved disk assets/source and runtime class; no in-memory bytecode hash'},
        'revision_note': 'Hashes are acquired from current saved core/player/map files on every run; earlier attempt hashes remain in preserved reports, including concurrent input fixes.',
        'waypoint_plan': [{'name': n, 'xy': list(p), 'interaction': a} for n, p, a in route],
        'waypoints': [], 'samples': [], 'interactions': [], 'checks': [], 'steering_inputs': [],
        'fixture': 'Only control rotation and Move inputs are debug driven; no location/collision/time/source state writes',
        'capsule': {'radius': capsule.get_scaled_capsule_radius(), 'half_height': capsule.get_scaled_capsule_half_height()},
        'speed_cm_s': float(movement.get_editor_property('max_walk_speed')),
        'minimum_analog_speed_cm_s': float(movement.get_editor_property('min_analog_walk_speed')),
        'steering_rule': 'Throttle = min(1, 0.4 * distance/(maxWalkSpeed * conservative actual game/callback delta)); five-centimetre arrival, native braking only at arrival',
    }
    settings = world.get_world_settings()
    try:
        report['world_kill_z'] = float(settings.get_editor_property('kill_z'))
        report['world_bounds_checks'] = bool(settings.get_editor_property('enable_world_bounds_checks'))
    except Exception as exc:
        report['world_settings_diagnostic_unavailable'] = str(exc)
    state = {'index': 0, 'mode': 'init', 'handle': None,
             'game_started': initial_game_time,
             'wall_started': time.monotonic(), 'sample_at': -1., 'done': False,
             'last_position': None, 'turn_fixtures': 0,
             'last_callback_game_time': initial_game_time, 'recent_game_deltas': []}

    def get(name):
        return loop.get_editor_property(name)

    def check(condition, name):
        report['checks'].append({'name': name, 'pass': bool(condition)})
        if not condition:
            raise AssertionError(name)

    def save():
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

    def hit_description(hit):
        if not hit:
            return None
        data = hit.to_tuple()
        actor, component = data[9], data[10]
        return {'actor': actor.get_path_name() if actor else None,
                'label': actor.get_actor_label() if actor else None,
                'component': component.get_name() if component else None,
                'blocking_hit': bool(data[0]), 'impact_point': xyz(data[5])}

    def floor_probe(position):
        start = unreal.Vector(position.x, position.y, position.z + 10.)
        end = unreal.Vector(position.x, position.y, position.z - 500.)
        return hit_description(unreal.SystemLibrary.line_trace_single(
            world, start, end, unreal.TraceTypeQuery.ECC_VISIBILITY, False,
            [pawn], unreal.DrawDebugTrace.NONE, True))

    def diagnostics(position, point):
        forward = unreal.Vector(point[0] - position.x, point[1] - position.y, 0.)
        length = math.hypot(forward.x, forward.y)
        if length > .001:
            forward = forward * (min(length, 180.) / length)
        end = position + forward
        try:
            blocker = hit_description(unreal.SystemLibrary.capsule_trace_single(
                world, position, end, capsule.get_scaled_capsule_radius(),
                capsule.get_scaled_capsule_half_height(), unreal.TraceTypeQuery.ECC_VISIBILITY,
                False, [pawn], unreal.DrawDebugTrace.NONE, True))
        except Exception as exc:
            blocker = {'diagnostic_error': str(exc)}
        return {'position': xyz(position), 'waypoint': list(point),
                'distance_xy_cm': distance(position, point), 'floor': floor_probe(position),
                'forward_capsule_visibility_blocker': blocker,
                'qualification': 'Visibility diagnostics identify geometry; actual Pawn collision is the native movement result',
                'velocity': xyz(pawn.get_velocity()), 'movement_mode': str(movement.get_editor_property('movement_mode'))}

    def finish(status):
        state['done'] = True
        try:
            report['binding']['files_at_end'] = hashes()
            unchanged = report['binding']['files_at_start'] == report['binding']['files_at_end']
            report['checks'].append({'name': 'Source/core/player/map hashes unchanged', 'pass': unchanged})
            failed = sum(not row['pass'] for row in report['checks'])
            report['failed_checks'] = failed
            report['status'] = 'passed' if status == 'passed' and not failed else 'failed'
            report['finished_game_time'] = unreal.GameplayStatics.get_time_seconds(world)
            report['control_rotation_fixture_updates'] = state['turn_fixtures']
            save()
        finally:
            if state['handle'] is not None:
                unreal.unregister_slate_post_tick_callback(state['handle'])
                state['handle'] = None
            if unreal.SystemLibrary.is_valid(pawn):
                movement.stop_movement_immediately()

    def turn(rotation):
        controller.set_control_rotation(rotation)
        state['turn_fixtures'] += 1

    def aim_point(actor, name):
        if name == 'LamActor':
            return unreal.MathLibrary.transform_location(actor.get_actor_transform(), unreal.Vector(0., 11., 63.))
        return actor.get_actor_bounds(False)[0]

    def sample(now, position):
        if now - state['sample_at'] < .25:
            return
        report['samples'].append({'game_time': now, 'index': state['index'],
                                 'mode': state['mode'], 'pawn': xyz(position),
                                 'velocity': xyz(pawn.get_velocity()),
                                 'movement_mode': str(movement.get_editor_property('movement_mode')),
                                 'floor': floor_probe(position), 'raw_retained': bool(get('bRawRetained'))})
        state['sample_at'] = now
        save()

    def begin_leg(now, position):
        state['mode'] = 'walk'
        state['leg_started'] = now
        state['progress_at'] = now
        state['progress_distance'] = distance(position, route[state['index']][1])
        state['leg_timeout'] = max(8., state['progress_distance'] / max(report['speed_cm_s'], 1.) * 3. + 4.)

    def tick(delta):
        if state['done']:
            return
        try:
            if time.monotonic() - state['wall_started'] > 120:
                raise TimeoutError('Navigation exceeded 120s wall bound')
            if editor.get_game_world() != world:
                raise RuntimeError('PIE ended/replaced during navigation')
            now = unreal.GameplayStatics.get_time_seconds(world)
            actual_delta = max(0., now - state['last_callback_game_time'])
            state['last_callback_game_time'] = now
            state['recent_game_deltas'].append(actual_delta)
            state['recent_game_deltas'] = state['recent_game_deltas'][-4:]
            # Slate callback deltas alone can understate the real time elapsed
            # between game updates while the editor is hidden/backgrounded.
            steering_delta = max(.016, float(delta), *state['recent_game_deltas'])
            if now - state['game_started'] > 100:
                raise TimeoutError('Navigation exceeded 100s game bound')
            current = unreal.GameplayStatics.get_player_pawn(world, 0)
            if not unreal.SystemLibrary.is_valid(pawn) or current != pawn:
                report['pawn_survival_failure'] = {'game_time': now,
                    'last_valid_position': state['last_position'],
                    'possessed_pawn': current.get_path_name() if current else None,
                    'waypoint_index': state['index'],
                    'cause': 'Unassigned; inspect last native movement/floor samples'}
                raise RuntimeError('Native pawn destroyed, unpossessed or replaced')
            position = pawn.get_actor_location()
            state['last_position'] = xyz(position)
            if position.z < -100. or position.z > 350.:
                report['fall_or_height_failure'] = diagnostics(position, route[state['index']][1])
                raise AssertionError('Native traversal left the expected floor-height envelope')
            if not get('bRawRetained'):
                raise AssertionError('Navigation lost retained raw evidence')
            sample(now, position)
            name, point, interaction = route[state['index']]
            if state['mode'] == 'init':
                if not get('bInitialised'):
                    return
                check(distance(position, (-880., 0.)) < 120., 'Actual player starts at entry without positioning fixture')
                report['spawn'] = diagnostics(position, route[0][1])
                for ref in flags:
                    check(get(ref) is not None, ref + ' resolved')
                    report.setdefault('target_positions', {})[ref] = xyz(get(ref).get_actor_location())
                begin_leg(now, position)
            if state['mode'] == 'walk':
                remaining = distance(position, point)
                if remaining <= 5.:
                    movement.stop_movement_immediately()
                    report['waypoints'].append({'index': state['index'], 'name': name,
                        'game_time': now, 'pawn': xyz(position), 'remaining_cm': remaining,
                        'leg_duration_s': now - state['leg_started']})
                    if interaction:
                        state['mode'] = 'aim'
                        state['aim_at'] = now
                        if interaction == 'ListenActor' and not get('bEcho'):
                            loop.call_method('ToggleEcho', ())
                            report.setdefault('actions', []).append({'game_time': now, 'action': 'ToggleEcho native gameplay API'})
                    else:
                        state['index'] += 1
                        begin_leg(now, position)
                    save()
                    return
                if remaining < state['progress_distance'] - .5:
                    state['progress_distance'] = remaining
                    state['progress_at'] = now
                if now - state['progress_at'] > 2.5 or now - state['leg_started'] > state['leg_timeout']:
                    failure = {'index': state['index'], 'name': name,
                        'game_time': now, 'seconds_without_progress': now - state['progress_at'],
                        **diagnostics(position, point)}
                    speed = math.hypot(failure['velocity'][0], failure['velocity'][1])
                    blocker = failure['forward_capsule_visibility_blocker']
                    has_blocker = isinstance(blocker, dict) and blocker.get('blocking_hit', False)
                    if speed > 1. and not has_blocker:
                        failure['classification'] = 'Debug steering/overshoot failure; moving pawn and no observed forward blocker. Geometry obstruction is unproved.'
                        report['steering_failure'] = failure
                        raise AssertionError('Debug steering failed to converge; no geometry-block claim')
                    failure['classification'] = ('Forward collision candidate; native route progress stalled'
                        if has_blocker else 'Unassigned route progress stall; no forward geometry blocker established')
                    report['blocked_leg'] = failure
                    raise AssertionError('Native route progress failed; see qualified blocker diagnostics')
                desired = unreal.Vector(point[0], point[1], position.z)
                turn(unreal.MathLibrary.find_look_at_rotation(position, desired))
                throttle = min(1., .4 * remaining / (max(report['speed_cm_s'], 1.) * steering_delta))
                report['steering_inputs'].append({'game_time': now, 'index': state['index'],
                    'remaining_cm': remaining, 'actual_game_delta_s': actual_delta,
                    'slate_delta_s': float(delta), 'conservative_delta_s': steering_delta,
                    'throttle': throttle,
                    'predicted_input_step_cm': report['speed_cm_s'] * throttle * steering_delta})
                pawn.call_method('Move', (0., throttle))
                return
            actor = get(interaction)
            turn(unreal.MathLibrary.find_look_at_rotation(camera.get_camera_location(), aim_point(actor, interaction)))
            if now - state['aim_at'] < .5:
                return
            start = camera.get_camera_location()
            end = start + unreal.MathLibrary.get_forward_vector(camera.get_camera_rotation()) * 300.
            hit = unreal.SystemLibrary.line_trace_single(world, start, end,
                unreal.TraceTypeQuery.ECC_VISIBILITY, False, [pawn], unreal.DrawDebugTrace.NONE, True)
            actual_actor = hit.to_tuple()[9] if hit else None
            row = {'target': interaction, 'game_time': now, 'pawn': xyz(position),
                   'camera': xyz(start), 'ray_end': xyz(end), 'expected_actor': actor.get_path_name(),
                   'camera_hit': hit_description(hit), 'before_acquired': bool(get(flags[interaction]))}
            report['interactions'].append(row)
            check(actual_actor == actor, 'Native camera ray actually hits ' + interaction)
            loop.call_method('Interact', ())
            row.update(acquired=bool(get(flags[interaction])), message=str(get('Message')),
                       raw_retained=bool(get('bRawRetained')))
            check(row['acquired'], 'Actual Interact acquires ' + flags[interaction])
            if interaction == 'ListenActor':
                check(not get('bObserved'), 'Deck interaction does not fabricate whole-roll listening')
                # This route qualifies movement/collection, not uninterrupted
                # listening. Return through the present channel using the real
                # gameplay toggle rather than fixture-writing attention/source.
                loop.call_method('ToggleEcho', ())
                report.setdefault('actions', []).append({'game_time': now,
                    'action': 'ToggleEcho native gameplay API; traversal continues in present channel'})
            if interaction == 'ExitActor':
                check(get('bLeftSchool') and get('EntityState') == 0, 'Walking exit leaves the loop unresolved')
                check(bool(get('bAvoided')) == (int(get('RollCycles')) > 0),
                      'Exit distinguishes early departure from completed-roll avoidance')
                report['exit_outcome'] = {'avoided': bool(get('bAvoided')),
                    'roll_cycles': int(get('RollCycles')), 'entity_state': int(get('EntityState'))}
                check(get('LossCount') == 0, 'Traversal did not invent an attention/contact loss')
                check(get('bRawRetained'), 'Native traversal retains raw evidence')
                check(len(report['waypoints']) == len(route), 'Every waypoint reached without teleport or phase skip')
                finish('passed')
                return
            state['index'] += 1
            begin_leg(now, position)
            save()
        except Exception:
            report['error'] = traceback.format_exc()
            report['checks'].append({'name': 'Native route completes without blocked leg/fall/wrong target', 'pass': False})
            finish('failed')

    save()
    state['handle'] = unreal.register_slate_post_tick_callback(tick)
    print('G1_NAVIGATION_TRIAL_STARTED')


start_trial(globals().get('G1_PIE_START_RESULT'))
