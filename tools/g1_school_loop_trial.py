"""Run ONE G1 actor scenario in a fresh real PIE, using Blueprint debug calls.

Set G1_CASE in the executing script globals before exec: held, names, wrong,
tier1, decay, contact, or avoidance. Each major case requires a fresh PIE world.
Evidence distinguishes fixture setup/API calls from physical-input playtesting.
Only one nonblocking Slate callback is registered, with guaranteed cleanup.
"""
import json
from pathlib import Path
import time
import traceback
import hashlib
import datetime
import unreal

CASE = globals().get('G1_CASE', 'held')
CASES = ('held', 'names', 'wrong', 'tier1', 'decay', 'contact', 'avoidance')
if CASE not in CASES:
    raise ValueError('Unknown G1_CASE: ' + str(CASE))
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
if world is None:
    raise RuntimeError('A fresh real PIE world is required')
cls = unreal.load_class(None, '/Game/KhoangLang/Production/G1Canon/BP_KL_SchoolLoop.BP_KL_SchoolLoop_C')
loop = unreal.GameplayStatics.get_actor_of_class(world, cls)
pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
if loop is None or pawn is None:
    raise RuntimeError('G1 loop and actual pawn must be present')
if (loop.get_editor_property('LossCount') != 0 or
        loop.get_editor_property('EntityState') != 0 or
        loop.get_editor_property('Candidate') != 0 or
        loop.get_editor_property('bNotebook')):
    raise RuntimeError('Fresh PIE defaults required: do not reuse a previous case')

target = Path(unreal.Paths.project_dir()) / ('docs/agent/EVIDENCE/G1_school_' + CASE + '_trial.json')
report = {'case': CASE, 'world': world.get_path_name(), 'status': 'running',
          'method': 'Blueprint debug API calls; actual engine Tick/game time',
          'scope_limit': 'No physical-key, campaign-save or visual/audio-quality qualification',
          'fixture_setup': [], 'checks': [], 'states': []}
project_root = Path(unreal.Paths.project_dir())
report['binding'] = {
    'source_revision': globals().get('G1_SOURCE_REVISION', 'not-supplied'),
    'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'loop_asset_sha256': hashlib.sha256((project_root /
        'Content/KhoangLang/Production/G1Canon/BP_KL_SchoolLoop.uasset').read_bytes()).hexdigest(),
    'map_sha256': hashlib.sha256((project_root /
        'Content/KhoangLang/Production/G1Canon/Lvl_KL_SchoolSlice.umap').read_bytes()).hexdigest(),
    'scenario_sha256': hashlib.sha256((project_root /
        'tools/g1_school_loop_trial.py').read_bytes()).hexdigest(),
    'pawn_class': pawn.get_class().get_path_name(),
}
state = {'phase': 0, 'at': unreal.GameplayStatics.get_time_seconds(world),
         'started': unreal.GameplayStatics.get_time_seconds(world),
         'wall_started': time.monotonic(), 'handle': None}


def save():
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')


def check(condition, name):
    report['checks'].append({'name': name, 'pass': bool(condition)})
    if not condition:
        raise AssertionError(name)


def get(name):
    return loop.get_editor_property(name)


def fixture(**values):
    report['fixture_setup'].append(values)
    for key, value in values.items():
        loop.set_editor_property(key, value)


def call(name, *values):
    return loop.call_method(name, values)


def change_phase(number):
    state['phase'] = number
    state['at'] = unreal.GameplayStatics.get_time_seconds(world)
    report['states'].append({
        'phase': number, 'game_time': state['at'],
        **{key: get(key) for key in ('EntityState', 'LamState', 'Attention',
           'Candidate', 'bSealing', 'bWorkingAvailable', 'LastLoss', 'LossCount',
           'bRawRetained', 'bFalseSpace', 'RollTime', 'RollCycles')}})
    save()


def stop(status):
    report['status'] = status
    try:
        save()
    finally:
        if state['handle'] is not None:
            unreal.unregister_slate_post_tick_callback(state['handle'])
            state['handle'] = None


def ready_sources():
    # This is explicit scene-state setup, not evidence of acquiring sources.
    fixture(bNotebook=True, bLamWitness=True, bObserved=True,
            bWorkingAvailable=True, LamState=2)
    if not get('bEcho'):
        call('ToggleEcho')


def choose(index):
    call('SelectCandidate', index)
    call('Preview')


def aim_at_exit():
    exit_actor = get('ExitActor')
    check(exit_actor is not None, 'Exit actor found by tag')
    aim = exit_actor.get_actor_location()
    mesh = exit_actor.get_component_by_class(unreal.StaticMeshComponent)
    if mesh is not None:
        bounds = mesh.get_editor_property('static_mesh').get_bounds()
        aim = unreal.MathLibrary.transform_location(mesh.get_world_transform(), bounds.origin)
    # Debug positioning is explicitly not traversal/physical-key proof.
    # The exit is on the WEST end wall. Approach from the school interior,
    # never from outside the corridor behind its wall.
    position = unreal.Vector(aim.x + 180, aim.y, 98)
    pawn.set_actor_location(position, False, True)
    controller = unreal.GameplayStatics.get_player_controller(world, 0)
    camera = unreal.GameplayStatics.get_player_camera_manager(world, 0)
    controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(
        camera.get_camera_location(), aim))
    report['fixture_setup'].append({'debug_exit_position': [position.x, position.y, position.z]})


def tick(delta):
    try:
        now = unreal.GameplayStatics.get_time_seconds(world)
        if time.monotonic() - state['wall_started'] > 90:
            raise TimeoutError('G1 wall-clock timeout; PIE may be paused')
        if now - state['started'] > 35:
            raise TimeoutError('G1 scenario timeout at phase ' + str(state['phase']))
        elapsed = now - state['at']
        if state['phase'] == 0:
            if not get('bInitialised'):
                return
            check(get('bRawRetained'), 'Raw recordings retained at initialization')
            for name in ('LamActor', 'NotebookActor', 'LedgerActor', 'ListenActor',
                         'ExitActor', 'TeacherActor', 'ChildActor', 'FalseGeometryActor'):
                check(get(name) is not None, name + ' resolved')
            if CASE == 'held':
                fixture(bObserved=False, bWorkingAvailable=True)
                call('ToggleEcho')
                choose(3)
                check(get('EntityState') == 0, 'Preview alone does not anchor entity')
                call('BeginSeal')
                check(not get('bSealing'), 'Seal blocked without notebook and independent witness')
                fixture(bNotebook=True, bLamWitness=True, LamState=2)
                call('BeginSeal')
                check(not get('bSealing'), 'Early seal rejected before whole roll and child reply')
                check(not get('bObserved'), 'Interaction/state setup cannot fabricate heard completion')
                call('CancelWorking')
                check(not get('bObserved'), 'Cancel does not fabricate listening acquisition')
                call('ToggleEcho')
                call('ToggleEcho')
                check(get('RollTime') == 0. and not get('bObserved'),
                      'Interrupted/repeated playback restarts without heard acquisition')
            elif CASE == 'names':
                ready_sources()
                choose(4)
                call('BeginSeal')
                check(not get('bSealing'), 'True names require ledger')
                fixture(bLedger=True)
                call('BeginSeal')
                check(get('bSealing'), 'Fixture names seal starts after ledger')
            elif CASE == 'wrong':
                ready_sources()
                choose(1)
                call('BeginSeal')
                check(get('bSealing'), 'Wrong plausible choice can be sealed')
            elif CASE == 'tier1':
                ready_sources()
                fixture(Attention=25.)
                choose(3)
                preview = [get(k) for k in ('PreviewVoice', 'PreviewRhythm', 'PreviewRoom')]
                check(sum('không rõ' in s for s in preview) == 1,
                      'Noisy tier obscures exactly one preview criterion')
                check('nhiễu' in preview[2], 'Room criterion explicitly obscured by noise')
            elif CASE == 'decay':
                fixture(Attention=35.)
                check(not get('bEcho'), 'Present channel starts without echo')
            elif CASE == 'contact':
                ready_sources()
                fixture(EntityState=1)
                call('HandleContact')
                check(get('LossCount') == 1, 'Contact applies exactly one loss')
                check(get('LastLoss') == 1 and not get('bWorkingAvailable'),
                      'Available unsealed working reconstruction lost')
                check(get('EntityState') == 1 and get('LamState') == 2,
                      'Other two loss alternatives not applied')
                check(get('bRawRetained'), 'Contact never deletes raw recordings')
                check(get('bFalseSpace'), 'Contact opens false silence')
                call('HandleContact')
                check(get('LossCount') == 1, 'Contact cooldown prevents duplicate loss')
            elif CASE == 'avoidance':
                call('ToggleEcho')
            change_phase(1)
        elif state['phase'] == 1:
            if CASE in ('held', 'names', 'wrong'):
                if CASE == 'held':
                    if elapsed < 16.3:
                        return
                    check(get('bObserved'), 'Whole roll and child reply acquired through real Tick')
                    call('CancelWorking')
                    check(get('bObserved') and get('bRawRetained'),
                          'Cancel preserves legitimately acquired source and raw original')
                    call('ToggleEcho')
                    call('ToggleEcho')
                    check(get('bObserved') and get('RollTime') == 0.,
                          'Repeated listening retains only prior complete source acquisition')
                    choose(3)
                    call('BeginSeal')
                    check(get('bSealing'), 'Seal starts after complete listening and corroboration')
                    check(get('EntityState') == 0, 'Seal is not an immediate completion')
                    change_phase(2)
                    return
                if elapsed < float(get('SealDuration')) + .3:
                    return
                check(not get('bSealing'), 'Real world ticks finish timed seal')
                if CASE == 'held':
                    check(get('EntityState') == 1, 'Two-person response anchors cô Vân as Giữ')
                    check(get('bRawRetained'), 'Correct seal retains raw sources')
                elif CASE == 'names':
                    check(get('EntityState') == 2, 'Both ledger names complete roll call as Yên')
                    check(not get('bWorkingAvailable'), 'Completed seal is no longer exposed as unsealed work')
                else:
                    check(get('LamState') == 0, 'Wrong seal loses Lam trust')
                    check(get('EntityState') == 0, 'Wrong seal does not complete entity')
                    check(get('bFalseSpace'), 'Wrong seal produces false geometry state')
                    check(get('bRawRetained'), 'Wrong seal retains raw sources')
                stop('passed')
            elif CASE == 'decay':
                if elapsed < 1.:
                    return
                check(get('Attention') < 35., 'Device off causes real-time attention decay')
                call('ToggleEcho')
                check(get('bEcho'), 'Echo channel enabled')
                call('ToggleEcho')
                check(not get('bEcho'), 'Echo channel disabled')
                check(get('bFalseSpace'), 'Mid-roll-call interruption still distorts space')
                check(get('FalseRemaining') > 0., 'Distortion has a measured duration')
                stop('passed')
            elif CASE == 'avoidance':
                if elapsed < float(get('RollPeriod')) + .3:
                    return
                check(get('RollCycles') >= 1, 'Avoidance lets a real timed roll-call cycle finish')
                aim_at_exit()
                change_phase(2)
            else:
                if elapsed < .5:
                    return
                check(get('bRawRetained'), 'Raw retention survives subsequent real ticks')
                if CASE == 'contact':
                    call('HandleContact')
                    check(get('LossCount') == 1, 'Cooldown persists across real ticks')
                    # Explicit independent configurations exercise the other
                    # applicable alternatives without pretending cooldowns
                    # expired. This is not an end-to-end encounter traversal.
                    fixture(ContactCooldown=0., bWorkingAvailable=False,
                            LamState=2, EntityState=1)
                    call('HandleContact')
                    check(get('LossCount') == 2 and get('LastLoss') == 2,
                          'When work absent, exactly one trust loss applies')
                    check(get('LamState') == 0 and get('EntityState') == 1,
                          'Trust loss leaves anchored entity unchanged')
                    fixture(ContactCooldown=0., bWorkingAvailable=False,
                            LamState=0, EntityState=1)
                    call('HandleContact')
                    check(get('LossCount') == 3 and get('LastLoss') == 3,
                          'With work/trust absent, exactly one anchor loss applies')
                    check(get('EntityState') == 0 and get('LamState') == 0,
                          'Anchor loss changes Giữ to Tràn only')
                    fixture(ContactCooldown=0., bWorkingAvailable=False,
                            LamState=0, EntityState=0)
                    count_before = get('LossCount')
                    location_before = pawn.get_actor_location()
                    call('HandleContact')
                    check(get('LossCount') == count_before,
                          'Exhausted alternatives never fabricate a counted loss')
                    check(get('bContactDeferred'), 'Exhausted contact is explicitly deferred')
                    check(pawn.get_actor_location() == location_before,
                          'Exhausted contact does not teleport without a consequence')
                    check(get('bRawRetained'), 'All three losses retain raw recordings')
                    # Restore the same working-source availability that the
                    # diegetic Listen interaction provides, then resolve again.
                    fixture(bWorkingAvailable=True)
                    choose(3)
                    call('BeginSeal')
                    check(get('bSealing'), 'Reacquired work permits a recovery seal')
                    change_phase(2)
                    return
                stop('passed')
        elif state['phase'] == 2 and CASE == 'held':
            if elapsed < float(get('SealDuration')) + .3:
                return
            check(not get('bSealing'), 'Real world ticks finish timed seal')
            check(get('EntityState') == 1, 'Two-person response anchors cô Vân as Giữ')
            check(not get('bWorkingAvailable'), 'Successfully sealed reconstruction cannot be lost as unsealed work')
            check(get('bRawRetained'), 'Correct seal retains raw sources')
            stop('passed')
        elif state['phase'] == 2 and CASE == 'avoidance':
            if elapsed < .3:
                return
            # Refresh aim after the real player-camera update.
            exit_actor = get('ExitActor')
            controller = unreal.GameplayStatics.get_player_controller(world, 0)
            camera = unreal.GameplayStatics.get_player_camera_manager(world, 0)
            bounds = exit_actor.get_actor_bounds(False)
            controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(
                camera.get_camera_location(), bounds[0]))
            if elapsed < .6:
                return
            call('Interact')
            check(get('bLeftSchool') and get('bAvoided'), 'Exit interaction preserves avoidance outcome')
            check(get('EntityState') == 0, 'Avoidance does not falsely complete cô Vân')
            stop('passed')
        elif state['phase'] == 2 and CASE == 'contact':
            if elapsed < float(get('SealDuration')) + .3:
                return
            check(get('EntityState') == 1 and get('LamState') == 2,
                  'Correct timed reconstruction restores trust and anchors entity')
            check(not get('bContactDeferred'), 'Recovery re-arms applicable contact consequences')
            check(get('LossCount') == 3, 'Recovery preserves all three previous losses')
            check(get('bRawRetained'), 'Recovery retains raw recordings')
            stop('passed')
    except Exception:
        report['error'] = traceback.format_exc()
        stop('failed')


save()
state['handle'] = unreal.register_slate_post_tick_callback(tick)
print('G1_SCHOOL_TRIAL_STARTED ' + CASE)
