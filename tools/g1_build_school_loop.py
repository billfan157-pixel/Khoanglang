"""Generate ONLY the isolated, canonical G1 school-loop Blueprint actor.

Editor execution is an integration operation: do not run while another writer
owns the editor. Python builds graphs only; gameplay uses Blueprint Tick.
Reversible authored composition: the school gap is the interrupted roll call
after 63, reconstructed through a rehearsed response, not a new 2002 transcript.
Lam's independent source is his CURRENT direct observation of two pauses.
True names are restricted to bG1Fixture and the temporary rice ledger.
"""
import importlib
import json
from pathlib import Path
import sys

import unreal

ROOT = Path(unreal.Paths.project_dir())
sys.path.insert(0, str(ROOT / 'Content/Python/KhoangLang'))
import kl_core as K
import build_20_blueprints as H
importlib.reload(K)
importlib.reload(H)

PATH = '/Game/KhoangLang/Production/G1Canon/BP_KL_SchoolLoop'
REPORT = ROOT / 'docs/agent/EVIDENCE/G1_school_loop_build.json'
BPT = K.BPT

BOOLS = {
    'bG1Fixture': True, 'bEcho': False, 'bNotebook': False,
    'bLamWitness': False, 'bLedger': False, 'bObserved': False,
    'bWorkingAvailable': False, 'bRawRetained': True, 'bPreviewed': False,
    'bSealing': False, 'bDossier': False, 'bFalseSpace': False,
    'bAttackProvoked': False, 'bAvoided': False, 'bLeftSchool': False,
    'bReducedSuddenAudio': False, 'bInitialised': False,
    'bContactDeferred': False,
    'bRollSourceActive': False, 'bChildReplyIssued': False,
}
INTS = {'Candidate': 0, 'EntityState': 0, 'Tier': 0, 'LamState': 1,
        'LastLoss': 0, 'LossCount': 0, 'RollCycles': 0}
FLOATS = {
    'Attention': 0., 'RollTime': 0., 'SealProgress': 0., 'PauseRemaining': 0.,
    'FalseRemaining': 0., 'ContactCooldown': 0., 'ExposureTime': 0.,
    'WavePhase': 0., 'Delta': 0., 'EchoRate': 1.8, 'QuietRate': 4.,
    'SealRate': 5., 'SealDuration': 4., 'RollPeriod': 18.,
    'RollDuration': 13., 'AmbienceTime': 0., 'AmbienceDuration': 18.,
    'HearThreshold': 20., 'RecogniseThreshold': 45., 'SeekThreshold': 75.,
    'InteractDistance': 300., 'SchoolRadius': 2200.,
    'TeacherSpeed': 85., 'ContactDistance': 85.,
}
REFS = {
    'LamActor': 'KL_Lam', 'NotebookActor': 'KL_Notebook',
    'LedgerActor': 'KL_Ledger', 'ListenActor': 'KL_Listen',
    'ExitActor': 'KL_Exit', 'TeacherActor': 'KL_Teacher',
    'ChildActor': 'KL_Child', 'FalseGeometryActor': 'KL_FalseGeometry',
}
TEXTS = {
    'Header': 'TRƯỜNG TIỂU HỌC SỐ 3 · NGHE CHO HẾT CÂU',
    'Message': 'Tìm thầy Lâm, rồi nghe hai nhịp ngắt trong lớp.',
    'Caption': '[Mưa trên mái tôn · kênh hiện tại]',
    'PreviewVoice': 'Giọng: chưa thử', 'PreviewRhythm': 'Nhịp: chưa thử',
    'PreviewRoom': 'Tiếng phòng: chưa thử',
    'Footer': '[Q] kênh  [E] dùng  [1–4] chọn  [R] thử  [Enter] niêm phong',
}
SIGNATURES = {
    'InitSchool': (), 'ToggleEcho': (), 'SelectCandidate': [('InCandidate', 'int')],
    'Preview': (), 'BeginSeal': (), 'FinishSeal': (), 'CancelWorking': (),
    'Interact': (), 'PollSchoolKeys': (), 'TickSchool': [('DeltaSeconds', 'float')],
    'UpdatePresentation': (), 'AdvanceTeacher': (), 'HandleContact': (),
    'StartRollAudio': (), 'StopRollAudio': (), 'SettleQuietly': (),
    'StartAmbience': (), 'ApplyAudioPreference': (),
}


class Graph:
    """Typed graph fragments; literals establish scalar types before promotion."""
    def __init__(self, bp, name, params=(), out=None):
        self.bp = bp
        self.g, self.b, self.e = H.newfn(bp, name, params, out)

    def var(self, name):
        return H.bv(self.b, name)

    def literal(self, value, kind=None):
        if kind is None:
            kind = 'bool' if isinstance(value, bool) else ('int' if isinstance(value, int) else 'double')
        node = self.b.c('/Script/Engine.KismetSystemLibrary:MakeLiteral' +
                        {'bool': 'Bool', 'int': 'Int', 'double': 'Double', 'string': 'String'}[kind])
        self.b.setv(node, 'Value', str(value).lower() if isinstance(value, bool) else str(value))
        return node, 'ReturnValue'

    def wire(self, value, node, pin):
        if isinstance(value, tuple):
            self.b.link(value[0], value[1], node, pin)
        else:
            self.b.setv(node, pin, str(value).lower() if isinstance(value, bool) else str(value))

    def native(graph, path, **pins):
        # `self` must remain available as the Blueprint target-pin keyword.
        node = graph.b.c('/Script/Engine.' + path)
        for pin, value in pins.items():
            graph.wire(value, node, pin)
        return node

    def call(self, name, **pins):
        node = H.callbp(self.b, PATH, name)
        for pin, value in pins.items():
            self.wire(value, node, pin)
        self.e = H.cont(self.b, self.e, node)
        return node

    def set(self, name, value):
        node = self.b.s(name)
        self.wire(value, node, name)
        self.e = H.cont(self.b, self.e, node)

    def run(self, node):
        self.e = H.cont(self.b, self.e, node)
        return node

    def condition(self, ref, yes=None, no=None):
        def branch(fn):
            def apply(entry):
                outer = self.e
                self.e = entry
                fn()
                result = self.e
                self.e = outer
                return result
            return apply if fn else None
        self.e = H.iff(self.b, self.e, lambda: ref, branch(yes), branch(no))

    def op(self, fname, left, right=None, int_op=False):
        node = self.b.c('/Script/Engine.KismetMathLibrary:' + fname)
        # First connect typed scalar B. Unreal may otherwise promote double math
        # into int/vector operators based on A's first connection.
        if right is not None:
            self.wire(right if isinstance(right, tuple) else self.literal(right, 'int' if int_op else 'double'), node, 'B')
        self.wire(left if isinstance(left, tuple) else self.literal(left, 'int' if int_op else 'double'), node, 'A')
        return node, 'ReturnValue'

    def eq(self, name, value):
        return self.op('EqualEqual_IntInt', self.var(name), value, True)

    def lt(self, left, right):
        return self.op('Less_DoubleDouble', left, right)

    def ge(self, left, right):
        return self.op('GreaterEqual_DoubleDouble', left, right)

    def both(self, *refs):
        ref = refs[0]
        for other in refs[1:]:
            ref = H.andb(self.b, ref, other)
        return ref

    def either(self, *refs):
        ref = refs[0]
        for other in refs[1:]:
            ref = H.orb(self.b, ref, other)
        return ref

    def negate(self, ref):
        return H.notb(self.b, ref)

    def sel(self, condition, no, yes):
        return H.selb(self.b, no, yes, condition)

    def valid(self, ref):
        return self.native('KismetSystemLibrary:IsValid', Object=ref), 'ReturnValue'

    def location(self, ref):
        return self.native('Actor:K2_GetActorLocation', self=ref), 'ReturnValue'

    def distance(self, a, b):
        return self.native('KismetMathLibrary:Vector_Distance', V1=a, V2=b), 'ReturnValue'

    def hidden(self, ref, value):
        self.condition(self.valid(ref), lambda: self.run(self.native(
            'Actor:SetActorHiddenInGame', self=ref, bNewHidden=value)))

    def stop_audio(self, ref):
        self.condition(self.valid(ref), lambda: self.run(self.native(
            'AudioComponent:Stop', self=ref)))

    def message(self, text):
        self.set('Message', text)

    def finish(self):
        result = self.b.ret()
        # Explicit continuation ensures the function's authored body ends here.
        if self.b.has_in(result, 'execute'):
            self.b.link(self.e[0], self.e[1], result, 'execute')


def build():
    K.FAILS.clear()
    unreal.EditorAssetLibrary.make_directory(PATH.rsplit('/', 1)[0])
    bp, _ = K.new_bp(PATH.rsplit('/', 1)[0], PATH.rsplit('/', 1)[1], 'Actor')
    for name in BOOLS:
        K.var(bp, name, 'bool', editable=True)
    for name in INTS:
        K.var(bp, name, 'int', editable=True)
    for name in FLOATS:
        K.var(bp, name, 'float', editable=True)
    for name in TEXTS:
        K.var(bp, name, 'string')
    for name in REFS:
        K.var_obj(bp, name, 'Actor', editable=True)
    for name, cls in (('PawnRef', 'Pawn'), ('ControllerRef', 'PlayerController'),
                      ('RollAudioRef', 'AudioComponent'), ('ChildAudioRef', 'AudioComponent'),
                      ('AmbienceAudioRef', 'AudioComponent')):
        K.var_obj(bp, name, cls)
    for name in ('SafeLocation', 'TeacherHome', 'PreviousLocation'):
        K.var(bp, name, 'vector', editable=True)
    for name in ('RollWave', 'ReplyWave', 'SealWave', 'AmbienceWave'):
        K.var_obj(bp, name, 'SoundWave', editable=True)
    # Declare the complete public API before adding cross-function calls.
    for name, params in SIGNATURES.items():
        H.newfn(bp, name, params)
    for name in ['GetHeader', 'GetStatus', 'GetCaption', 'GetPrompt', 'GetFooter2'] + ['GetBody%d' % i for i in range(1, 9)] + ['GetFooter']:
        H.newfn(bp, name, out=('ReturnValue', 'string'))
    H.newfn(bp, 'GetWavePhase', out=('ReturnValue', 'float'))
    H.newfn(bp, 'GetSealProgress', out=('ReturnValue', 'float'))
    H.newfn(bp, 'GetDossierOpen', out=('ReturnValue', 'bool'))
    H.newfn(bp, 'HasApplicableLoss', out=('ReturnValue', 'bool'))
    BPT.compile_blueprint(bp)
    for mapping in (BOOLS, INTS, FLOATS, TEXTS):
        for name, value in mapping.items():
            K.set_cdo(bp, name, value)
    for name, source in (('RollWave', 'S_KL_RollCall'), ('ReplyWave', 'S_KL_ChildReply'),
                         ('SealWave', 'S_KL_UI_ModeShift'), ('AmbienceWave', 'S_KL_Ambience_Hall')):
        K.set_cdo(bp, name, K.load(K.F_AUDIO + '/' + source))
    ambience = K.load(K.F_AUDIO + '/S_KL_Ambience_Hall')
    K.set_cdo(bp, 'AmbienceDuration', float(ambience.get_editor_property('duration')))

    f = Graph(bp, 'InitSchool')
    f.set('PawnRef', H.player_pawn(f.b))
    f.set('ControllerRef', H.player_ctrl(f.b))
    f.condition(f.valid(f.var('PawnRef')), lambda: (
        f.set('SafeLocation', f.location(f.var('PawnRef'))),
        f.set('PreviousLocation', f.location(f.var('PawnRef')))))
    for name, tag in REFS.items():
        def discover(name=name, tag=tag):
            query = f.native('GameplayStatics:GetAllActorsWithTag', Tag=tag)
            f.run(query)
            length = f.native('KismetArrayLibrary:Array_Length', TargetArray=(query, 'OutActors'))
            def first():
                get = f.native('KismetArrayLibrary:Array_Get', TargetArray=(query, 'OutActors'), Index='0')
                f.set(name, (get, 'Item'))
            f.condition(f.op('Greater_IntInt', (length, 'ReturnValue'), 0, True), first)
        f.condition(f.negate(f.valid(f.var(name))), discover)
    f.condition(f.valid(f.var('TeacherActor')), lambda:
                f.set('TeacherHome', f.location(f.var('TeacherActor'))))
    f.hidden(f.var('ChildActor'), True)
    f.hidden(f.var('FalseGeometryActor'), True)
    f.set('bInitialised', True)
    f.call('StartAmbience')
    f.finish()

    f = Graph(bp, 'StartAmbience')
    f.stop_audio(f.var('AmbienceAudioRef'))
    spawn = f.native('GameplayStatics:SpawnSound2D', Sound=f.var('AmbienceWave'),
                     VolumeMultiplier='0.35', bAutoDestroy=True)
    f.run(spawn)
    f.set('AmbienceAudioRef', (spawn, 'ReturnValue'))
    f.set('AmbienceTime', 0.)
    f.finish()

    f = Graph(bp, 'ApplyAudioPreference')
    for ref, normal, reduced in (('RollAudioRef', .65, .35),
                                 ('ChildAudioRef', .45, .25),
                                 ('AmbienceAudioRef', .35, .35)):
        f.condition(f.valid(f.var(ref)), lambda ref=ref, normal=normal, reduced=reduced:
                    f.run(f.native('AudioComponent:SetVolumeMultiplier', self=f.var(ref),
                        NewVolumeMultiplier=f.sel(f.var('bReducedSuddenAudio'),
                                                  f.literal(normal), f.literal(reduced)))))
    f.finish()

    f = Graph(bp, 'StopRollAudio')
    f.stop_audio(f.var('RollAudioRef'))
    f.stop_audio(f.var('ChildAudioRef'))
    f.set('bRollSourceActive', False)
    f.set('bChildReplyIssued', False)
    f.finish()

    f = Graph(bp, 'StartRollAudio')
    f.call('StopRollAudio')
    def start_roll():
        spawn = f.native('GameplayStatics:SpawnSoundAtLocation', Sound=f.var('RollWave'),
                         Location=f.location(f.var('TeacherActor')),
                         VolumeMultiplier=f.sel(f.var('bReducedSuddenAudio'), f.literal(.65), f.literal(.35)))
        f.run(spawn)
        f.set('RollAudioRef', (spawn, 'ReturnValue'))
        f.set('bRollSourceActive', True)
    f.condition(f.both(f.var('bEcho'), f.valid(f.var('TeacherActor')),
                       f.eq('EntityState', 0)), start_roll)
    f.finish()

    f = Graph(bp, 'ToggleEcho')
    def toggled_off():
        # Device-off helps attention, but interruption still deforms this room.
        f.condition(f.both(f.lt(f.var('RollTime'), 16.2), f.eq('EntityState', 0)),
                    lambda: (f.set('bFalseSpace', True), f.set('FalseRemaining', 7.),
                             f.message('Làm ngắt điểm danh: cửa vừa lùi xa hơn.')))
        f.call('StopRollAudio')
    def toggled_on():
        f.set('RollTime', 0.)
        f.call('StartRollAudio')
        f.message('Kênh hồi âm: nghe đến cả hai chỗ cô dừng.')
    f.set('bEcho', f.negate(f.var('bEcho')))
    f.condition(f.var('bEcho'), toggled_on, toggled_off)
    f.call('UpdatePresentation')
    f.finish()

    f = Graph(bp, 'SelectCandidate', SIGNATURES['SelectCandidate'])
    def choose():
        f.set('Candidate', (f.b.entry(f.g), 'InCandidate'))
        f.set('bDossier', True)
        f.set('bPreviewed', False)
        f.set('PreviewVoice', 'Giọng: chưa thử')
        f.set('PreviewRhythm', 'Nhịp: chưa thử')
        f.set('PreviewRoom', 'Tiếng phòng: chưa thử')
        f.message('Lời đáp đang thử; chưa thay đổi thực thể.')
    f.condition(f.both(f.negate(f.var('bSealing')), f.negate(f.eq('EntityState', 2))), choose)
    f.finish()

    f = Graph(bp, 'Preview')
    def preview():
        f.set('bPreviewed', True)
        f.set('bDossier', True)
        f.set('PreviewVoice', f.sel(f.eq('Candidate', 1), 'Giọng: khớp', 'Giọng: lệch'))
        f.set('PreviewRhythm', f.sel(f.eq('Candidate', 2), 'Nhịp: khớp', 'Nhịp: không rõ'))
        f.set('PreviewRoom', 'Tiếng phòng: khớp')
        f.condition(f.ge(f.var('Attention'), f.var('HearThreshold')),
                    lambda: f.set('PreviewRoom', 'Tiếng phòng: không rõ · nhiễu che'))
        f.set('Attention', f.op('Add_DoubleDouble', f.var('Attention'), 3.))
        f.message('Thử nghe chấm độ khớp; chưa xác nhận sự thật.')
    f.condition(f.both(f.var('bEcho'), f.var('bWorkingAvailable'),
                       f.negate(f.eq('Candidate', 0))), preview,
                lambda: f.message('Bật kênh hồi âm, thu đoạn ngắt, chọn lời đáp.'))
    f.finish()

    f = Graph(bp, 'BeginSeal')
    sources = f.both(f.var('bNotebook'), f.var('bLamWitness'), f.var('bObserved'),
                     f.var('bWorkingAvailable'), f.var('bPreviewed'), f.var('bEcho'),
                     f.negate(f.eq('Candidate', 0)), f.negate(f.var('bSealing')),
                     f.negate(f.eq('EntityState', 2)))
    def start():
        def allowed():
            f.set('SealProgress', 0.)
            f.set('bSealing', True)
            f.message('Đang niêm phong · tiếng máy làm tăng sự chú ý.')
            f.run(f.native('GameplayStatics:PlaySound2D', Sound=f.var('SealWave'),
                           VolumeMultiplier=f.sel(f.var('bReducedSuddenAudio'), f.literal(.3), f.literal(.15))))
        f.condition(f.either(f.negate(f.eq('Candidate', 4)),
                             f.both(f.var('bG1Fixture'), f.var('bLedger'))), allowed,
                    lambda: f.message('Tên thật cần đối chiếu với sổ phát gạo lán.'))
    f.condition(sources, start,
                lambda: f.message('Cần sổ cô Vân, lời thầy Lâm và một lần thử nghe.'))
    f.finish()

    f = Graph(bp, 'FinishSeal')
    f.set('bSealing', False)
    f.set('SealProgress', 0.)
    f.set('bPreviewed', False)
    f.set('Attention', f.op('Add_DoubleDouble', f.var('Attention'), 8.))
    def wrong():
        f.set('EntityState', 0)
        f.set('LamState', 0)
        f.set('bFalseSpace', True)
        f.set('FalseRemaining', 10.)
        f.set('bAttackProvoked', True)
        f.message('Sai lời đáp: thầy Lâm không còn tin; cô Vân bước tới.')
    def one_child():
        f.set('PauseRemaining', 8.)
        f.call('StopRollAudio')
        f.message('Cô dừng tạm. Hai chỗ trống vẫn còn.')
    def held():
        f.set('EntityState', 1)
        f.set('bWorkingAvailable', False)
        f.set('bAttackProvoked', False)
        f.set('LamState', 2)
        f.set('bContactDeferred', False)
        f.set('bFalseSpace', False)
        f.set('FalseRemaining', 0.)
        f.call('StopRollAudio')
        f.message('Cô Vân đã dừng. Hai tên vẫn còn thiếu.')
    def settled():
        f.condition(f.both(f.var('bG1Fixture'), f.var('bLedger')), lambda: (
            f.set('EntityState', 2), f.set('bAttackProvoked', False),
            f.set('bWorkingAvailable', False),
            f.set('LamState', 2), f.set('bContactDeferred', False), f.set('bFalseSpace', False),
            f.set('FalseRemaining', 0.), f.call('StopRollAudio'),
            f.message('«Có ạ.» · Cô Vân đếm đủ; vòng lặp đã kết thúc.')),
            lambda: f.message('Thiếu nguồn tên thật; vòng lặp chưa kết thúc.'))
    f.condition(f.eq('Candidate', 1), wrong, lambda:
        f.condition(f.eq('Candidate', 2), one_child, lambda:
            f.condition(f.eq('Candidate', 3), held, settled)))
    f.finish()

    f = Graph(bp, 'CancelWorking')
    f.set('bSealing', False)
    f.set('SealProgress', 0.)
    f.set('Candidate', 0)
    f.set('bPreviewed', False)
    f.message('Hủy lời đáp đang thử. Bản thô và hậu quả vẫn còn.')
    f.finish()

    # Camera trace grants interaction only with a visible reachable actor.
    f = Graph(bp, 'Interact')
    camera = f.native('GameplayStatics:GetPlayerCameraManager', PlayerIndex='0')
    loc = f.native('PlayerCameraManager:GetCameraLocation', self=(camera, 'ReturnValue'))
    rot = f.native('PlayerCameraManager:GetCameraRotation', self=(camera, 'ReturnValue'))
    forward = f.native('KismetMathLibrary:GetForwardVector', InRot=(rot, 'ReturnValue'))
    offset = f.op('Multiply_VectorFloat', (forward, 'ReturnValue'), f.var('InteractDistance'))
    end = f.native('KismetMathLibrary:Add_VectorVector', A=(loc, 'ReturnValue'), B=offset)
    trace = f.native('KismetSystemLibrary:LineTraceSingle', Start=(loc, 'ReturnValue'),
                     End=(end, 'ReturnValue'), TraceChannel='TraceTypeQuery1',
                     DrawDebugType='EDrawDebugTrace::None', bIgnoreSelf=True)
    f.run(trace)
    hit = f.b.n(K.F_BREAK_HIT)
    f.b.link(trace, 'OutHit', hit, 'Hit')
    actor = hit, 'HitActor'
    f.message('Đến gần và nhìn vào vật hoặc thầy Lâm.')
    def has_tag(tag):
        return f.native('Actor:ActorHasTag', self=actor, Tag=tag), 'ReturnValue'
    def lam():
        f.set('bLamWitness', True)
        f.condition(f.eq('LamState', 0), lambda:
                    f.message('Thầy Lâm: «Tôi nghe hai chỗ dừng. Anh nghe lại đi.»'),
                    lambda: (f.set('LamState', 2),
                             f.message('Thầy Lâm: «Tôi nghe cô dừng hai lần. Không chỉ một.»')))
    def notebook():
        f.set('bNotebook', True)
        f.message('Sổ cô Vân: «63 + 2». Nguồn có liên quan, không độc lập.')
    def ledger():
        f.condition(f.var('bG1Fixture'), lambda: (
            f.set('bLedger', True),
            f.message('Sổ phát gạo lán: Lê Thị Tuyết; Lê Thị Ngọc Ánh.')),
            lambda: f.message('Nguồn tên thật chưa có ở giai đoạn này.'))
    def listen():
        f.condition(f.var('bEcho'), lambda: (
            f.set('bWorkingAvailable', True), f.set('bContactDeferred', False),
            f.message('Đang thu đoạn ngắt. Nghe hết lượt điểm danh và tiếng đáp.')),
            lambda: f.message('Bật [Q] để nghe phần điểm danh đang lặp.'))
    def leave():
        f.set('bLeftSchool', True)
        f.condition(f.eq('EntityState', 0), lambda:
            f.condition(f.op('Greater_IntInt', f.var('RollCycles'), 0, True), lambda: (
                f.set('bAvoided', True),
                f.message('Đã lẩn tránh và rời trường. Cô vẫn tiếp tục đếm.')),
                lambda: f.message('Đã rời trường trước khi nghe hết lượt điểm danh.')),
            lambda: f.message('Đã rời trường; trạng thái cô Vân được giữ lại.'))
        f.set('bEcho', False)
        f.call('StopRollAudio')
    def dispatch():
        f.condition(has_tag('KL_Lam'), lam, lambda:
            f.condition(has_tag('KL_Notebook'), notebook, lambda:
                f.condition(has_tag('KL_Ledger'), ledger, lambda:
                    f.condition(has_tag('KL_Listen'), listen, lambda:
                        f.condition(has_tag('KL_Exit'), leave)))))
    f.condition(f.valid(actor), dispatch)
    f.finish()

    f = Graph(bp, 'HandleContact')
    def loss():
        f.set('bContactDeferred', False)
        f.set('LossCount', f.op('Add_IntInt', f.var('LossCount'), 1, True))
        def lose_work():
            f.set('LastLoss', 1)
            f.set('bWorkingAvailable', False)
            f.message('Mất bản dựng chưa niêm phong. Bản thô còn; thu lại ở loa.')
        def lose_trust():
            f.set('LastLoss', 2)
            f.set('LamState', 0)
            f.message('Thầy Lâm mất lòng tin. Bạn thoát ra ở lối vào.')
        def lose_anchor():
            f.set('LastLoss', 3)
            f.set('EntityState', 0)
            f.message('Cô Vân bắt đầu đếm lại. Bản thô vẫn còn.')
        f.condition(f.var('bWorkingAvailable'), lose_work, lambda:
            f.condition(f.op('Greater_IntInt', f.var('LamState'), 0, True), lose_trust,
                        lose_anchor))
        f.set('bSealing', False)
        f.set('bPreviewed', False)
        f.set('SealProgress', 0.)
        f.set('Candidate', 0)
        f.set('bFalseSpace', True)
        f.set('FalseRemaining', 10.)
        f.set('ContactCooldown', 12.)
        f.set('Attention', 46.)
        f.set('bAttackProvoked', False)
        f.condition(f.valid(f.var('PawnRef')), lambda: f.run(f.native(
            'Actor:K2_SetActorLocation', self=f.var('PawnRef'),
            NewLocation=f.var('SafeLocation'), bSweep=False, bTeleport=True)))
        f.condition(f.valid(f.var('TeacherActor')), lambda: f.run(f.native(
            'Actor:K2_SetActorLocation', self=f.var('TeacherActor'),
            NewLocation=f.var('TeacherHome'), bSweep=False, bTeleport=True)))
    # Never invent a fourth loss or count an already absent item as another
    # failure. When alternatives are exhausted cô waits outside touch range;
    # reacquiring the working reconstruction re-arms a meaningful consequence.
    eligible = H.callbp(f.b, PATH, 'HasApplicableLoss')
    def deferred():
        f.condition(f.negate(f.var('bContactDeferred')), lambda:
            f.message('Cô đứng chờ ở chỗ trống. Thu lại bản dựng tại loa.'))
        f.set('bContactDeferred', True)
    f.condition(f.lt(f.var('ContactCooldown'), .001), lambda:
                f.condition((eligible, 'ReturnValue'), loss, deferred))
    f.finish()

    f = Graph(bp, 'AdvanceTeacher')
    def advance():
        teacher_loc = f.location(f.var('TeacherActor'))
        pawn_loc = f.location(f.var('PawnRef'))
        direction = f.native('KismetMathLibrary:Subtract_VectorVector', A=pawn_loc, B=teacher_loc)
        split = f.native('KismetMathLibrary:BreakVector', InVec=(direction, 'ReturnValue'))
        flat = f.native('KismetMathLibrary:MakeVector', X=(split, 'X'), Y=(split, 'Y'), Z='0.0')
        normal = f.native('KismetMathLibrary:Normal', A=(flat, 'ReturnValue'))
        amount = f.op('Multiply_DoubleDouble', f.var('TeacherSpeed'), f.var('Delta'))
        zero = f.native('KismetMathLibrary:MakeVector', X='0.0', Y='0.0', Z='0.0')
        planar_distance = f.distance((flat, 'ReturnValue'), (zero, 'ReturnValue'))
        eligible = H.callbp(f.b, PATH, 'HasApplicableLoss')
        # No applicable loss means no accepted touch. Stop at a visible gap
        # instead of repeatedly teleporting the player with a fictitious loss.
        room = f.op('Subtract_DoubleDouble', planar_distance,
                    f.op('Add_DoubleDouble', f.var('ContactDistance'), 20.))
        maximum = f.native('KismetMathLibrary:FClamp', Value=room, Min='0.0', Max='10000.0')
        bounded = f.native('KismetMathLibrary:FClamp', Value=amount,
                           Min='0.0', Max=(maximum, 'ReturnValue'))
        amount = f.sel((eligible, 'ReturnValue'), (bounded, 'ReturnValue'), amount)
        offset = f.op('Multiply_VectorFloat', (normal, 'ReturnValue'), amount)
        f.run(f.native('Actor:K2_AddActorWorldOffset', self=f.var('TeacherActor'),
                       DeltaLocation=offset, bSweep=False, bTeleport=False))
        f.condition(f.lt(planar_distance, f.var('ContactDistance')),
                    lambda: f.call('HandleContact'))
    f.condition(f.both(f.valid(f.var('TeacherActor')), f.valid(f.var('PawnRef')),
                       f.negate(f.eq('EntityState', 2)),
                       f.either(f.var('bAttackProvoked'), f.eq('Tier', 3)),
                       f.lt(f.var('ContactCooldown'), .001)), advance)
    f.finish()

    f = Graph(bp, 'SettleQuietly')
    f.set('Attention', f.op('Subtract_DoubleDouble', f.var('Attention'),
                           f.op('Multiply_DoubleDouble', f.var('QuietRate'), f.var('Delta'))))
    f.finish()

    f = Graph(bp, 'TickSchool', SIGNATURES['TickSchool'])
    f.set('Delta', (f.b.entry(f.g), 'DeltaSeconds'))
    def run_tick():
        f.call('PollSchoolKeys')
        f.set('AmbienceTime', f.op('Add_DoubleDouble', f.var('AmbienceTime'), f.var('Delta')))
        f.condition(f.ge(f.var('AmbienceTime'), f.var('AmbienceDuration')),
                    lambda: f.call('StartAmbience'))
        for timer in ('PauseRemaining', 'FalseRemaining', 'ContactCooldown'):
            new = f.op('Subtract_DoubleDouble', f.var(timer), f.var('Delta'))
            clamp = f.native('KismetMathLibrary:FClamp', Value=new, Min='0.0', Max='1000.0')
            f.set(timer, (clamp, 'ReturnValue'))
        pawn_loc = f.location(f.var('PawnRef'))
        still = f.lt(f.distance(pawn_loc, f.var('PreviousLocation')), .3)
        outside = f.ge(f.distance(pawn_loc, f.var('SafeLocation')), f.var('SchoolRadius'))
        def echo_noise():
            f.set('Attention', f.op('Add_DoubleDouble', f.var('Attention'),
                                   f.op('Multiply_DoubleDouble', f.var('EchoRate'), f.var('Delta'))))
        f.condition(f.both(f.var('bEcho'), f.negate(outside), f.negate(f.var('bLeftSchool'))), echo_noise)
        f.condition(f.either(f.negate(f.var('bEcho')), still, outside, f.var('bLeftSchool')),
                    lambda: f.call('SettleQuietly'))
        f.set('PreviousLocation', pawn_loc)
        def seal_tick():
            f.set('SealProgress', f.op('Add_DoubleDouble', f.var('SealProgress'), f.var('Delta')))
            f.set('Attention', f.op('Add_DoubleDouble', f.var('Attention'),
                                   f.op('Multiply_DoubleDouble', f.var('SealRate'), f.var('Delta'))))
            f.condition(f.ge(f.var('SealProgress'), f.var('SealDuration')), lambda: f.call('FinishSeal'))
        f.condition(f.var('bSealing'), seal_tick)
        clamp = f.native('KismetMathLibrary:FClamp', Value=f.var('Attention'), Min='0.0', Max='100.0')
        f.set('Attention', (clamp, 'ReturnValue'))
        f.set('Tier', 0)
        for index, threshold in ((1, 'HearThreshold'), (2, 'RecogniseThreshold'), (3, 'SeekThreshold')):
            f.condition(f.ge(f.var('Attention'), f.var(threshold)), lambda index=index: f.set('Tier', index))
        def roll_tick():
            old_time = f.var('RollTime')
            # Store before advancing: crossing test is evaluated after writes.
            f.set('WavePhase', old_time)
            f.set('RollTime', f.op('Add_DoubleDouble', f.var('RollTime'), f.var('Delta')))
            def child_reply():
                f.condition(f.valid(f.var('ChildActor')), lambda: (
                    f.set('ChildAudioRef', (f.run(f.native(
                        'GameplayStatics:SpawnSoundAtLocation', Sound=f.var('ReplyWave'),
                        Location=f.location(f.var('ChildActor')),
                        VolumeMultiplier=f.sel(f.var('bReducedSuddenAudio'),
                                                f.literal(.45), f.literal(.25)))), 'ReturnValue')),
                    f.set('bChildReplyIssued', True)))
            f.condition(f.both(f.lt(f.var('WavePhase'), f.var('RollDuration')),
                               f.ge(f.var('RollTime'), f.var('RollDuration'))), child_reply)
            # Acquisition is earned only after the entire uninterrupted roll
            # and child reply, never by merely interacting with the recorder.
            f.condition(f.both(f.ge(f.var('RollTime'), 16.2),
                               f.var('bRollSourceActive'), f.var('bChildReplyIssued')),
                        lambda: f.set('bObserved', True))
            def cycle():
                f.set('RollCycles', f.op('Add_IntInt', f.var('RollCycles'), 1, True))
                f.set('RollTime', 0.)
                f.call('StartRollAudio')
            f.condition(f.ge(f.var('RollTime'), f.var('RollPeriod')), cycle)
        f.condition(f.both(f.var('bEcho'), f.eq('EntityState', 0),
                           f.lt(f.var('PauseRemaining'), .001)), roll_tick)
        def expose():
            f.set('ExposureTime', f.op('Add_DoubleDouble', f.var('ExposureTime'), f.var('Delta')))
            def eat_work():
                f.set('bWorkingAvailable', False)
                f.set('bPreviewed', False)
                f.set('LastLoss', 1)
                f.set('LossCount', f.op('Add_IntInt', f.var('LossCount'), 1, True))
                f.set('ExposureTime', 0.)
                f.message('Nhiễu nuốt bản dựng chưa niêm phong. Bản thô còn.')
            f.condition(f.ge(f.var('ExposureTime'), 5.), eat_work)
        f.condition(f.both(f.eq('Tier', 2), f.var('bWorkingAvailable'),
                           f.negate(f.var('bSealing'))), expose,
                    lambda: f.set('ExposureTime', 0.))
        f.call('AdvanceTeacher')
        f.call('UpdatePresentation')
    f.condition(f.valid(f.var('PawnRef')), run_tick)
    f.finish()

    f = Graph(bp, 'PollSchoolKeys')
    def poll():
        for key, action in (('Q', 'ToggleEcho'), ('E', 'Interact'), ('R', 'Preview'),
                            ('Enter', 'BeginSeal'), ('X', 'CancelWorking')):
            f.condition(H.key_pressed(f.b, key, f.var('ControllerRef')),
                        lambda action=action: f.call(action))
        for index, key in enumerate(('One', 'Two', 'Three', 'Four'), 1):
            f.condition(H.key_pressed(f.b, key, f.var('ControllerRef')),
                        lambda index=index: f.call('SelectCandidate', InCandidate=str(index)))
        f.condition(H.key_pressed(f.b, 'J', f.var('ControllerRef')),
                    lambda: f.set('bDossier', f.negate(f.var('bDossier'))))
        f.condition(H.key_pressed(f.b, 'V', f.var('ControllerRef')),
                    lambda: (f.set('bReducedSuddenAudio', f.negate(f.var('bReducedSuddenAudio'))),
                             f.call('ApplyAudioPreference')))
    f.condition(f.valid(f.var('ControllerRef')), poll)
    f.finish()

    f = Graph(bp, 'UpdatePresentation')
    f.hidden(f.var('ChildActor'), f.negate(f.both(f.var('bEcho'), f.negate(f.eq('EntityState', 2)))))
    false = f.either(f.ge(f.var('Attention'), f.var('RecogniseThreshold')),
                     f.ge(f.var('FalseRemaining'), .001))
    f.set('bFalseSpace', false)
    f.hidden(f.var('FalseGeometryActor'), f.negate(false))
    f.set('Caption', '[Mưa trên mái tôn · kênh hiện tại]')
    def caption_echo():
        f.set('Caption', 'Cô Vân: «Sáu mươi mốt, sáu mươi hai, sáu mươi ba...»')
        f.condition(f.ge(f.var('RollTime'), f.var('RollDuration')), lambda:
                    f.set('Caption', 'Bàn cuối · bé Bống: «Cô ơi, còn con nữa.»'))
        f.condition(f.ge(f.var('RollTime'), 16.2), lambda:
                    f.set('Caption', '[Tiếng phấn · hai nhịp ngắt ở cuối lớp]'))
        f.condition(f.eq('EntityState', 1), lambda:
                    f.set('Caption', '[Cô Vân đã dừng · hai chỗ vẫn chưa có tên]'))
        f.condition(f.eq('EntityState', 2), lambda:
                    f.set('Caption', 'Ngọc Ánh: «Có ạ.» · [Điểm danh đã kết thúc]'))
        f.condition(f.ge(f.var('PauseRemaining'), .001), lambda:
                    f.set('Caption', '[Cô dừng tạm · vẫn chưa đếm được cả hai]'))
    f.condition(f.var('bEcho'), caption_echo)
    f.finish()

    def getter(name, make):
        q = Graph(bp, name, out=('ReturnValue', 'string'))
        value = make(q)
        q.b.ret(value[0], value[1])

    getter('GetHeader', lambda q: q.var('Header'))
    getter('GetCaption', lambda q: q.var('Caption'))
    getter('GetPrompt', lambda q: q.var('Message'))
    getter('GetStatus', lambda q: q.sel(q.eq('Tier', 3),
        q.sel(q.eq('Tier', 2), q.sel(q.eq('Tier', 1),
            q.sel(q.var('bEcho'), 'HIỆN TẠI · Sự chú ý: Yên', 'HỒI ÂM · Sự chú ý: Yên'),
            'Sự chú ý: Nghe thấy · một tiêu chí bị nhiễu'),
            'Sự chú ý: Nhận ra · hình học sai; bản dựng có thể mất'),
        'Sự chú ý: Tìm đến · cô Vân tiến về phía bạn'))
    getter('GetBody1', lambda q: q.sel(q.var('bDossier'), q.var('Message'),
        'SỔ TAY · Lời đáp cho đoạn điểm danh bỏ dở'))
    getter('GetBody2', lambda q: q.sel(q.var('bDossier'), q.var('Caption'),
        q.sel(q.var('bNotebook'), 'Sổ cô Vân: chưa có', 'Sổ cô Vân: «63 + 2» · Có liên quan')))
    getter('GetBody3', lambda q: q.sel(q.var('bDossier'),
        q.sel(q.eq('Candidate', 4), q.sel(q.eq('Candidate', 3),
            q.sel(q.eq('Candidate', 2), q.sel(q.eq('Candidate', 1),
                'Lời đáp: [1] tên Khải [2] một bạn [3] hai người [4] tên',
                'Đang chọn: «Khải» · tên không có trong đoàn của cô'),
                'Đang chọn: «Có, còn một bạn nữa»'),
                'Đang chọn: «Thêm hai người nữa»'),
                q.sel(q.var('bLedger'), 'Đang chọn đọc tên · cần sổ phát gạo lán',
                      'Đang chọn: tên Lê Thị Tuyết và Lê Thị Ngọc Ánh')),
        q.sel(q.var('bLamWitness'), 'Thầy Lâm: chưa đối chứng',
              'Thầy Lâm: nghe hai lần dừng hiện tại · Độc lập')))
    getter('GetBody4', lambda q: q.sel(q.var('bDossier'), q.var('PreviewVoice'),
        q.sel(q.var('bLedger'), 'Tên thật: cần sổ phát gạo lán',
              'Sổ phát gạo: Lê Thị Tuyết; Lê Thị Ngọc Ánh')))
    getter('GetBody5', lambda q: q.sel(q.var('bDossier'), q.var('PreviewRhythm'),
        q.sel(q.eq('LamState', 0), 'Thầy Lâm sẵn lòng đối chứng',
              'Thầy Lâm đang mất lòng tin')))
    getter('GetBody6', lambda q: q.sel(q.var('bDossier'),
        q.sel(q.ge(q.var('Attention'), q.var('HearThreshold')),
              q.var('PreviewRoom'), 'Tiếng phòng: không rõ · nhiễu che'),
        q.sel(q.eq('EntityState', 2), q.sel(q.eq('EntityState', 1),
              'Cô Vân vẫn lặp lượt điểm danh', 'Cô Vân đã dừng; hai tên còn thiếu'),
              'Cô Vân đã hoàn thành lượt điểm danh')))
    getter('GetBody7', lambda q: q.sel(q.var('bDossier'),
        q.sel(q.var('bSealing'),
              q.sel(q.var('bWorkingAvailable'), 'Bản dựng: cần thu lại tại loa', 'Bản dựng: sẵn để thử'),
              'Niêm phong đang chạy · [X] hủy; tiếng máy gọi sự chú ý'),
        'Bản thô luôn được giữ. Mất bản dựng có thể thu lại.'))
    getter('GetBody8', lambda q: q.sel(q.var('bDossier'),
        q.sel(q.var('bReducedSuddenAudio'), '[J] sổ tay · [V] giảm âm đột ngột: TẮT',
              '[J] sổ tay · [V] giảm âm đột ngột: BẬT'),
        'Điều đã xảy ra đêm 2002 không thể thay đổi.'))
    getter('GetFooter', lambda q: q.var('Footer'))
    getter('GetFooter2', lambda q: q.sel(q.var('bReducedSuddenAudio'),
        '[J] sổ tay · [X] hủy thử · [V] giảm âm đột ngột: TẮT',
        '[J] sổ tay · [X] hủy thử · [V] giảm âm đột ngột: BẬT'))
    q = Graph(bp, 'GetWavePhase', out=('ReturnValue', 'float'))
    phase = q.native('KismetMathLibrary:Divide_DoubleDouble', A=q.var('RollTime'), B=q.var('RollDuration'))
    clamp = q.native('KismetMathLibrary:FClamp', Value=(phase, 'ReturnValue'), Min='0.0', Max='1.0')
    q.b.ret(clamp, 'ReturnValue')
    q = Graph(bp, 'GetSealProgress', out=('ReturnValue', 'float'))
    progress = q.native('KismetMathLibrary:Divide_DoubleDouble', A=q.var('SealProgress'), B=q.var('SealDuration'))
    q.b.ret(progress, 'ReturnValue')
    q = Graph(bp, 'GetDossierOpen', out=('ReturnValue', 'bool'))
    value = q.var('bDossier')
    q.b.ret(value[0], value[1])
    q = Graph(bp, 'HasApplicableLoss', out=('ReturnValue', 'bool'))
    value = q.either(q.var('bWorkingAvailable'),
                     q.op('Greater_IntInt', q.var('LamState'), 0, True),
                     q.eq('EntityState', 1))
    q.b.ret(value[0], value[1])

    graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    b = K.B(graph, 'SchoolLoop.EventGraph')
    b.clear(keep_prefixes=())
    begin = b.ev('BeginPlay')
    tick_node = b.ev('Tick')
    init = H.callbp(b, PATH, 'InitSchool')
    update = H.callbp(b, PATH, 'TickSchool')
    b.link(begin, 'then', init, 'execute')
    b.link(tick_node, 'then', update, 'execute')
    b.link(tick_node, 'DeltaSeconds', update, 'DeltaSeconds')
    if not b.compile(bp, 'canonical G1 school actor') or K.FAILS:
        raise RuntimeError('G1 school graph failed: ' + repr(K.FAILS))
    if not K.save(PATH) or K.FAILS:
        raise RuntimeError('G1 school save failed: ' + repr(K.FAILS))
    return {'asset': PATH, 'status': str(bp.get_editor_property('status')),
            'failures': list(K.FAILS), 'runtime': 'Blueprint Tick; no Python runtime',
            'refs': REFS, 'api': list(SIGNATURES),
            'scene_composition': [
                'Current Lam observation independently corroborates two pauses.',
                'Interrupted roll-call gap reconstructed by rehearsed response.',
                'bG1Fixture true-name ledger never claims early campaign access.',
                'Wave phase is a timing aid, not measured PCM waveform evidence.'],
            'exhausted_loss_rule': 'No counted contact without an applicable loss; teacher waits outside touch range until working reconstruction is reacquired.',
            'requires_runtime_validation': True}


def main():
    report = {'asset': PATH, 'status': 'building'}
    try:
        report = build()
    except Exception as exc:
        report.update(status='failed', error=repr(exc), failures=list(K.FAILS))
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        raise
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
