"""Qualify tier2/3/0 effects in fresh G1 PIE with actual Blueprint world ticks.

Only this engineering test uses Python. No physical input, sound quality,
campaign progression, collision navigation, or packaged performance is proved.
QuietRate/EchoRate and initial attention/source availability are recorded debug
fixtures. The teacher is positioned once per pursuit; movement/contact are then
performed by the game's Blueprint Tick, never by this Python callback.

The existing one-criterion preview noise is preserved. Tier2 adds actual false
geometry and working-record risk; it does not acquire a new two-criterion rule.
"""
import datetime
import hashlib
import json
import math
from pathlib import Path
import time
import traceback
import unreal

ROOT = Path(unreal.Paths.project_dir())
BASE = '/Game/KhoangLang/Production/G1Canon'
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
if world is None or '/G1Canon/' not in world.get_path_name() or 'Lvl_KL_SchoolSlice' not in world.get_path_name():
    raise RuntimeError('Fresh canonical school PIE is required')
loop = unreal.GameplayStatics.get_actor_of_class(world, unreal.load_class(
    None, BASE + '/BP_KL_SchoolLoop.BP_KL_SchoolLoop_C'))
pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
if loop is None or pawn is None:
    raise RuntimeError('School loop and native possessed player are required')
if pawn.get_class().get_path_name() != BASE + '/BP_KL_SchoolPlayer.BP_KL_SchoolPlayer_C':
    raise RuntimeError('Attention trial requires the new native SchoolPlayer')
for key, expected in (('EntityState', 0), ('LossCount', 0), ('Candidate', 0), ('bNotebook', False)):
    if loop.get_editor_property(key) != expected:
        raise RuntimeError('Fresh PIE defaults required: ' + key)

TARGET = ROOT / 'docs/agent/EVIDENCE/G1_attention_trial.json'
BOUND_FILES = {
    'canon': 'docs/story/Khoang_Lang_02_17_Cot_truyen_v3.md',
    'core_source': 'tools/g1_build_school_loop.py',
    'player_source': 'tools/g1_build_native_player.py',
    'scenario_source': 'tools/g1_attention_trial.py',
    'core_asset': 'Content/KhoangLang/Production/G1Canon/BP_KL_SchoolLoop.uasset',
    'player_asset': 'Content/KhoangLang/Production/G1Canon/BP_KL_SchoolPlayer.uasset',
    'map': 'Content/KhoangLang/Production/G1Canon/Lvl_KL_SchoolSlice.umap',
}


def hashes():
    return {name: {'path': path, 'sha256': hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}
            for name, path in BOUND_FILES.items()}


report = {
    'status': 'running',
    'method': 'Recorded debug fixtures; actual game-time Blueprint Tick pursuit/contact/decay',
    'scope_limit': 'No physical input, collision-route, voice/scare, campaign, or packaged-performance acceptance',
    'binding': {
        'source_revision': globals().get('G1_SOURCE_REVISION', 'not-supplied'),
        'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'world': world.get_path_name(), 'loop_class': loop.get_class().get_path_name(),
        'pawn_class': pawn.get_class().get_path_name(), 'files_at_start': hashes(),
        'qualification': 'Saved disk assets/source plus observed runtime class; no in-memory bytecode hash claimed',
    },
    'expected_tier2_obscured_criteria': 1,
    'expectation_origin': 'Existing one-criterion noise preserved; canon tier2 adds geometry/draft risk without an additional mask count',
    'fixture_setup': [], 'checks': [], 'states': [], 'teacher_samples': [],
}
state = {
    'phase': 0, 'phase_at': unreal.GameplayStatics.get_time_seconds(world),
    'game_started': unreal.GameplayStatics.get_time_seconds(world),
    'wall_started': time.monotonic(), 'handle': None,
    'sample_at': -1., 'bong_caption_seen': False,
}


def get(name):
    return loop.get_editor_property(name)


def call(name, *args):
    return loop.call_method(name, args)


def xyz(vector):
    return [float(vector.x), float(vector.y), float(vector.z)]


def distance_xy(a, b):
    return math.hypot(float(a.x - b.x), float(a.y - b.y))


def save():
    TARGET.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')


def check(condition, name, critical=True, details=None):
    item = {'name': name, 'pass': bool(condition)}
    if details is not None:
        item['details'] = details
    report['checks'].append(item)
    if not condition and critical:
        raise AssertionError(name)


def fixture(**values):
    report['fixture_setup'].append({
        'game_time': unreal.GameplayStatics.get_time_seconds(world), 'fields': values})
    for name, value in values.items():
        loop.set_editor_property(name, value)


def phase(number):
    state['phase'] = number
    state['phase_at'] = unreal.GameplayStatics.get_time_seconds(world)
    report['states'].append({
        'phase': number, 'game_time': state['phase_at'],
        **{name: get(name) for name in ('Attention', 'Tier', 'EntityState',
            'LamState', 'LossCount', 'LastLoss', 'ContactCooldown',
            'bWorkingAvailable', 'bRawRetained', 'bSealing', 'bFalseSpace')}})
    save()


def position_teacher(offset_cm=1050.):
    teacher = get('TeacherActor')
    current = teacher.get_actor_location()
    player = pawn.get_actor_location()
    position = unreal.Vector(player.x + offset_cm, player.y, current.z)
    teacher.set_actor_location(position, False, True)
    report['fixture_setup'].append({
        'game_time': unreal.GameplayStatics.get_time_seconds(world),
        'debug_teacher_position': xyz(position), 'purpose': 'Known initial planar separation; not navigation proof'})
    return position


def stop(status):
    try:
        report['binding']['files_at_end'] = hashes()
        same = report['binding']['files_at_end'] == report['binding']['files_at_start']
        check(same, 'Bound source/core/player/map files unchanged during trial', critical=False)
        failed = sum(not item['pass'] for item in report['checks'])
        report['failed_checks'] = failed
        report['status'] = 'failed' if status != 'passed' or failed else 'passed'
        report['finished_game_time'] = unreal.GameplayStatics.get_time_seconds(world)
        report['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        save()
    finally:
        if state['handle'] is not None:
            unreal.unregister_slate_post_tick_callback(state['handle'])
            state['handle'] = None


def observe(now):
    caption = str(call('GetCaption'))
    if 'Bống' in caption:
        state['bong_caption_seen'] = True
        report['back_row_caption'] = caption
    if now - state['sample_at'] >= .5:
        teacher = get('TeacherActor').get_actor_location()
        player = pawn.get_actor_location()
        report['teacher_samples'].append({
            'phase': state['phase'], 'game_time': now,
            'teacher': xyz(teacher), 'pawn': xyz(player),
            'distance_xy_cm': distance_xy(teacher, player),
            'attention': float(get('Attention')), 'tier': int(get('Tier')),
            'loss_count': int(get('LossCount')), 'provoked': bool(get('bAttackProvoked'))})
        state['sample_at'] = now
        save()


def tick(delta):
    try:
        if time.monotonic() - state['wall_started'] > 60:
            raise TimeoutError('Attention trial exceeded 60s wall-clock bound')
        current_world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if current_world is None or current_world != world:
            raise RuntimeError('PIE ended/replaced during attention trial')
        now = unreal.GameplayStatics.get_time_seconds(world)
        if now - state['game_started'] > 60:
            raise TimeoutError('Attention trial exceeded 60s game-clock bound')
        elapsed = now - state['phase_at']
        if state['phase'] == 0:
            if not get('bInitialised'):
                return
            for name in ('TeacherActor', 'ChildActor', 'FalseGeometryActor', 'ListenActor'):
                check(get(name) is not None, name + ' resolved')
            check(get('ChildActor') != get('TeacherActor'), 'Back-row child is separate from cô Vân')
            check(get('ChildActor').actor_has_tag(unreal.Name('KL_Child')), 'Back-row child retains its own KL_Child identity')
            report['back_row_child_actor'] = get('ChildActor').get_path_name()
            report['nhi_scope'] = 'No Nhi identity assigned to the back-row actor; observe bé Bống caption'
            check(get('bRawRetained'), 'Raw recording retention starts true')
            state['original_quiet_rate'] = float(get('QuietRate'))
            state['original_echo_rate'] = float(get('EchoRate'))
            fixture(QuietRate=0., EchoRate=0., Attention=55.,
                    bWorkingAvailable=True, bObserved=False, bNotebook=False,
                    bLamWitness=False, LamState=2, bAttackProvoked=False)
            if not get('bEcho'):
                call('ToggleEcho')
            call('SelectCandidate', 3)
            call('Preview')
            preview = {name: str(get(name)) for name in ('PreviewVoice', 'PreviewRhythm', 'PreviewRoom')}
            obscured = sum('không rõ' in text for text in preview.values())
            report['tier2_preview'] = {'criteria': preview, 'obscured_count': obscured}
            check(obscured == 1, 'Tier2 preserves existing one-criterion preview noise',
                  details={'expected': 1, 'observed': obscured})
            call('BeginSeal')
            check(not get('bSealing') and get('EntityState') == 0,
                  'Preview/high attention cannot bypass missing independent-source and whole-listening gates')
            state['tier2_loss_before'] = int(get('LossCount'))
            phase(1)
            return
        observe(now)
        if state['phase'] == 1:
            if elapsed < .25:
                return
            if 'tier2_geometry_observed' not in state:
                check(get('Tier') == 2, 'Tier2 persists under fixed-attention fixture')
                check(get('bFalseSpace'), 'Tier2 exposes false-space state')
                check(not get('FalseGeometryActor').get_editor_property('hidden'),
                      'Tier2 actually unhides false geometry actor')
                state['tier2_geometry_observed'] = True
            if get('LossCount') == state['tier2_loss_before']:
                if elapsed > 7:
                    raise AssertionError('Sustained tier2 failed to produce a material recording risk')
                return
            check(get('LossCount') == state['tier2_loss_before'] + 1,
                  'Sustained tier2 consumes exactly one available working reconstruction')
            check(not get('bWorkingAvailable') and get('LastLoss') == 1,
                  'Tier2 loss removes active unsealed work, not raw evidence')
            check(get('bRawRetained'), 'Tier2 erosion preserves raw recordings')
            check(get('LamState') == 2 and get('EntityState') == 0,
                  'Tier2 working-material loss does not silently change trust/entity state')
            fixture(Attention=0., bAttackProvoked=True, bWorkingAvailable=True,
                    FalseRemaining=0., ExposureTime=0., ContactCooldown=0.)
            state['provoked_start'] = position_teacher()
            state['provoked_distance'] = distance_xy(state['provoked_start'], pawn.get_actor_location())
            phase(2)
        elif state['phase'] == 2:
            if elapsed < 2:
                return
            teacher = get('TeacherActor').get_actor_location()
            change = state['provoked_distance'] - distance_xy(teacher, pawn.get_actor_location())
            check(get('Tier') == 0, 'Wrong-response provocation works independently of high attention')
            check(change > 70., 'Entity-specific provocation causes actual planar movement at tier0')
            check(abs(teacher.z - state['provoked_start'].z) < .5,
                  'Provoked approach preserves teacher height')
            fixture(Attention=80., bAttackProvoked=False, bWorkingAvailable=True,
                    ContactCooldown=0., ExposureTime=0.)
            state['pursuit_start'] = position_teacher()
            state['pursuit_distance'] = distance_xy(state['pursuit_start'], pawn.get_actor_location())
            state['pursuit_loss_before'] = int(get('LossCount'))
            state['pursuit_trust_before'] = int(get('LamState'))
            phase(3)
        elif state['phase'] == 3:
            teacher = get('TeacherActor').get_actor_location()
            if get('LossCount') == state['pursuit_loss_before']:
                deviation = abs(teacher.z - state['pursuit_start'].z)
                state['max_pursuit_z_deviation'] = max(state.get('max_pursuit_z_deviation', 0.), deviation)
                if deviation >= .5:
                    raise AssertionError('Teacher changed height during actual sustained pursuit')
                if elapsed >= 8 and 'eight_second_proof' not in state:
                    check(get('Tier') == 3 and not get('bAttackProvoked'),
                          'Sustained tier3 drives pursuit without wrong-response provocation')
                    check(get('Attention') >= get('SeekThreshold'), 'Tier3 remains sustained for at least eight game seconds')
                    decrease = state['pursuit_distance'] - distance_xy(teacher, pawn.get_actor_location())
                    check(decrease > 400., 'Actual teacher approach closes substantial distance across eight seconds')
                    report['eight_second_pursuit'] = {
                        'duration_s': elapsed, 'start': xyz(state['pursuit_start']),
                        'end': xyz(teacher), 'distance_closed_cm': decrease,
                        'teacher_z_delta_cm': float(teacher.z - state['pursuit_start'].z),
                        'maximum_z_deviation_cm': state['max_pursuit_z_deviation']}
                    state['eight_second_proof'] = True
                if elapsed > 18:
                    raise AssertionError('Sustained tier3 approach never reached a meaningful contact')
                return
            check('eight_second_proof' in state, 'Meaningful contact follows eight seconds of real pursuit')
            check(get('LossCount') == state['pursuit_loss_before'] + 1,
                  'Automatic contact applies exactly one new loss')
            check(get('LastLoss') == 1 and not get('bWorkingAvailable'),
                  'Automatic contact loses actual available unsealed material')
            check(get('LamState') == state['pursuit_trust_before'] and get('EntityState') == 0,
                  'Automatic contact leaves the other loss alternatives unchanged')
            check(get('bRawRetained'), 'Automatic contact retains raw recordings')
            check(get('ContactCooldown') > 0., 'Automatic contact arms cooldown')
            check(get('bFalseSpace'), 'Automatic contact opens false space')
            check(abs(teacher.z - state['pursuit_start'].z) < .5,
                  'Contact/reset preserves teacher height')
            report['contact'] = {'game_time': now, 'teacher_end': xyz(teacher),
                'pawn_end': xyz(pawn.get_actor_location()), 'cooldown': float(get('ContactCooldown')),
                'loss_delta': int(get('LossCount')) - state['pursuit_loss_before']}
            state['contact_loss_count'] = int(get('LossCount'))
            if get('bEcho'):
                call('ToggleEcho')
            call('CancelWorking')
            fixture(QuietRate=state['original_quiet_rate'], EchoRate=state['original_echo_rate'],
                    bAttackProvoked=False)
            state['decay_start'] = float(get('Attention'))
            phase(4)
        elif state['phase'] == 4:
            if get('LossCount') != state['contact_loss_count']:
                raise AssertionError('Cooldown/recovery duplicated the contact loss')
            if get('Tier') != 0 or get('Attention') > .05 or get('bFalseSpace'):
                if elapsed > 18:
                    raise AssertionError('Quiet/off recovery did not return to tier0 and clear false geometry')
                return
            check(not get('bEcho') and get('Attention') < state['decay_start'],
                  'Real off-channel quiet decay returns attention to zero')
            check(get('Tier') == 0, 'Real Tick returns to tier0')
            check(get('FalseGeometryActor').get_editor_property('hidden'),
                  'Recovered tier0 actually hides false geometry')
            check(get('bRawRetained'), 'Raw recordings retained through attention recovery')
            check(get('LossCount') == state['contact_loss_count'],
                  'Cooldown/recovery preserves exactly one contact loss')
            check(state['bong_caption_seen'], 'Back-row reply is captioned as bé Bống, independently of Nhi')
            stop('passed')
    except Exception:
        report['error'] = traceback.format_exc()
        stop('failed')


save()
state['handle'] = unreal.register_slate_post_tick_callback(tick)
print('G1_ATTENTION_TRIAL_STARTED')
