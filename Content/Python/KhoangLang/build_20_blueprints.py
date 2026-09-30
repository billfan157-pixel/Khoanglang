"""Khoang Lang 02:17 - Milestone 1, pass 2: gameplay Blueprints.

Creates / extends
  BP_KL_InvestigationComponent  - evidence + quest state (no audio, no drawing)
  BP_KL_ListeningComponent      - the two listening states (audio presentation)
  BP_KL_InteractComponent       - one reusable interaction payload
  BP_FirstPersonCharacter       - template character, extended in place
  BP_KL_HUD                     - canvas overlay / journal
  BP_KL_GameMode                - template game mode, points at the HUD

Run headless:  run_ue_script.ps1 build_20_blueprints.py
"""

import os
import sys

import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import kl_core as K  # noqa: E402
from kl_core import BP, BPT, ContainerType  # noqa: E402
from kl_core import step, ok, warn, fail  # noqa: E402

DEF = K.F_DATA + '/BP_KL_EvidenceDef'
INV = K.F_CORE + '/BP_KL_InvestigationComponent'
LIS = K.F_CORE + '/BP_KL_ListeningComponent'
INT = K.F_CORE + '/BP_KL_InteractComponent'
HUD = K.F_UI + '/BP_KL_HUD'
GM = K.F_PLAYER + '/BP_KL_GameMode'
CHAR = K.BP_TPL_CHAR
SND = K.F_AUDIO

# --------------------------------------------------------------------------- #
# player-facing copy
# --------------------------------------------------------------------------- #

MSG_ALREADY = 'Đã ghi vào sổ tay rồi.'
MSG_DOC = 'Đã ghi: sổ điểm danh tập kết.   Bấm [Tab] để đọc lại.'
MSG_TAPE = 'Đã ghi: băng thu 02:16:34.   Bấm [Q] để bật NGHE LỌC rồi nghe lại.'
MSG_TAPE_HEARD = 'Nghe lọc tách được các câu. Hai giọng nhỏ nhất nằm sát đáy băng.'
MSG_NEED_MORE = 'Chưa đủ. Phải nghe hết câu trên băng trước đã.'
MSG_REVEAL = 'Có thứ gì đó ở góc cuối. Giữ NGHE LỌC và nhìn thẳng vào.'
MSG_BEAT = 'Có tiếng trả lời trong lớp. Cả lớp đang chờ.'
MSG_CORROB = 'Sổ tay: hai nguồn không khớp.  63 tên có thực, 65 giọng đã trả lời.'
MSG_OPENING = 'Trường tiểu học số 3. Đã mấy năm không ai dẫn đoàn.'
MSG_CONSUMED = 'Đã lấy.'
MSG_NONE = ''
MSG_ROSTER = 'Bảng lớp 3, năm 2002. 63 dòng tên. Hai dòng cuối trống, cạnh chữ "ghi sau".'

OBJ = [
    'Mục tiêu: vào hành lang Trường tiểu học số 3, tìm sổ điểm danh trong lớp 3.',
    'Mục tiêu: đã có sổ. Đi tới cuối hành lang, tìm đầu băng nối loa.',
    'Mục tiêu: đã có băng. Quay vào lớp 3 lấy sổ trên bàn giáo viên.',
    'Mục tiêu: đủ hai nguồn. Bật [Q] NGHE LỌC, phát băng [E] và nghe đến hết.',
    'Mục tiêu: đã đối chứng. Quay lại lớp 3, bật [Q] NGHE LỌC, nhìn góc cuối.',
    'Mục tiêu: có thứ gì đó ở đó. Bấm [E] để lên tiếng.',
    'Hết phần thử nghiệm Milestone 1.',
    'Mục tiêu: đã nghe hết băng. Mở sổ tay [Tab] để đối chứng.',
]

CORROB = [
    'ĐỐI CHỨNG - nguồn A: sổ cô Vân, 63 tên + hai dòng trống ghi "ghi sau".',
    'ĐỐI CHỨNG - nguồn B: băng 02:16:34, 65 giọng đã trả lời (đếm được sau khi lọc).',
    'Hai con số lệch nhau đúng bằng hai dòng trống đó.',
    'Bản tin chính thức ghi 63 nạn nhân: đó là số người được đếm tên,',
    'không phải số người đã cất tiếng.',
    'Nghe hết câu là bước một. Đối chứng nguồn độc lập mới là bước hai.',
]

ENDING = [
    'Hết thử nghiệm Milestone 1 - Trường tiểu học số 3',
    'Bạn đã nghe được thứ vốn bị chôn, và đọc được thứ vốn bị bỏ trống.',
    'Hai nguồn độc lập không khớp: 63 tên có thực, 65 giọng đã trả lời.',
    'Chưa được trả lời ở đây: ai được đếm,',
    'ai được nghe, và ai có quyền kể lại.',
]
HINT_END = 'Hết phần thử nghiệm.     [Enter] chơi lại       [Esc] thoát'

LISTEN_ON = 'NGHE LỌC: lớp nhiễu bị bóp nghẹt, các giọng dưới đáy băng tách ra.'
LISTEN_OFF = 'NGHE THƯỜNG: âm thanh đi qua lớp vữa và tiếng mưa, không ngõi được gì.'
CONTROLS = ('WASD di chuyển · Chuột để nhìn · [E] tương tác · [Q] NGHE LỌC · '
            '[Tab] sổ tay · [F] đèn pin')

MIX = {
    'VolAmbNormal': 1.0, 'VolAmbFiltered': 0.30,
    'VolMaskNormal': 0.45, 'VolMaskFiltered': 0.0,
    'VolClarNormal': 0.0, 'VolClarFiltered': 0.32,
    'VolHumNormal': 0.0, 'VolHumFiltered': 0.24,
    'LowPassCutoff': 700.0,
    'RevealIntensity': 1.6, 'BeatIntensity': 3.6,
}

# --------------------------------------------------------------------------- #
# wiring helpers
# --------------------------------------------------------------------------- #


def iff(b, entry, cond_fn, then_fn=None, else_fn=None):
    sequence = b.n('Utilities|FlowControl|Sequence')
    b.link(entry[0], entry[1], sequence, 'execute')
    br = b.branch()
    b.link(sequence, 'then_0', br, 'execute')
    c = cond_fn()
    b.link(c[0], c[1], br, 'Condition')
    if then_fn:
        then_fn((br, 'then'))
    if else_fn:
        else_fn((br, 'else'))
    return (sequence, 'then_1')


def bv(b, var):
    g = b.g(var)
    return (g, b.out_any(g).name)


def sv(b, var, value):
    s = b.s(var)
    b.setv(s, var, value)
    return s


def sb(b, var, value):
    return sv(b, var, 'true' if value else 'false')


def cont(b, entry, node):
    b.link(entry[0], entry[1], node, 'execute')
    return (node, 'then')


def setp(b, entry, var, src_node, src_pin):
    """entry -> set <var> = src.<pin>"""
    s = b.s(var)
    b.link(entry[0], entry[1], s, 'execute')
    b.link(src_node, src_pin, s, var)
    return (s, 'then')


def setp_param(b, g, entry, var, pname):
    s = b.s(var)
    b.link(entry[0], entry[1], s, 'execute')
    b.link_param(g, pname, s, var)
    return (s, 'then')


def callbp(b, bp_path, fname):
    return b.c('%s:%s' % (K.cls_path(bp_path), fname))


def _ref(b, val):
    """Normalise a reference to a 1-tuple holding a PinInfo."""
    if val is None:
        return None
    if isinstance(val, str):
        return ('lit', val)
    if isinstance(val, tuple):
        if len(val) == 1:
            return val
        return (b.out(val[0], val[1]),)
    return (val,)


def _wire(b, selnode, val, pin_name):
    ref = _ref(b, val)
    if ref is None:
        return
    if ref[0] == 'lit':
        b.setv(selnode, pin_name, ref[1])
    else:
        BPT.connect_pins(ref[0].pin_id, b.inp(selnode, pin_name).pin_id)


def selb(b, zero, one, idx, zero_pin='Option 0', one_pin='Option 1',
         idx_pin='Index'):
    """wildcard Select with up to three connected options (None = skip)."""
    if isinstance(zero, str) and isinstance(one, str):
        # A literal does not establish a wildcard pin's type. Use an explicitly
        # typed select when neither option supplies a connected value.
        if zero == 'true' and one == 'false':
            return notb(b, idx)
        s = b.c('/Script/Engine.KismetMathLibrary:SelectString')
        _wire(b, s, zero, 'B')
        _wire(b, s, one, 'A')
        _wire(b, s, idx, 'bPickA')
        return (s, 'ReturnValue')
    s = b.sel()
    # Establish a value type before setting a literal on the other option.
    for value, pin in ((zero, zero_pin), (one, one_pin)):
        if not isinstance(value, str):
            _wire(b, s, value, pin)
    _wire(b, s, idx, idx_pin)
    for value, pin in ((zero, zero_pin), (one, one_pin)):
        if isinstance(value, str):
            _wire(b, s, value, pin)
    return (s, 'ReturnValue')


def andb(b, a, c):
    n = b.c('/Script/Engine.KismetMathLibrary:BooleanAND')
    _wire(b, n, a, 'A')
    _wire(b, n, c, 'B')
    return (n, 'ReturnValue')


def orb(b, a, c):
    n = b.c('/Script/Engine.KismetMathLibrary:BooleanOR')
    _wire(b, n, a, 'A')
    _wire(b, n, c, 'B')
    return (n, 'ReturnValue')


def notb(b, a):
    n = b.c('/Script/Engine.KismetMathLibrary:Not_PreBool')
    _wire(b, n, a, 'A')
    return (n, 'ReturnValue')


def text_getter(bp, name, var):
    g, b, e = newfn(bp, name, out=('ReturnValue', 'string'))
    gv = b.g(var)
    b.ret(b.text2str(gv, b.out_any(gv).name))
    b.compile(bp, name)


def bool_getter(bp, name, var):
    g, b, e = newfn(bp, name, out=('ReturnValue', 'bool'))
    gv = b.g(var)
    b.ret(gv, b.out_any(gv).name)
    b.compile(bp, name)


def def_getter(bp, name, defvar, fname):
    """One Text field of an evidence DataAsset, returned as a string."""
    g, b, e = newfn(bp, name, out=('ReturnValue', 'string'))
    dv = b.g(defvar)
    call = callbp(b, DEF, fname)
    b.link(dv, b.out_any(dv).name, call, 'self')
    b.ret(call, 'ReturnValue')
    b.compile(bp, name)


def newfn(bp, name, params=(), out=None):
    g = BPT.add_function_graph(bp, name)
    b = K.B(g, name)
    if out:
        b.ed.set_is_pure_function(True)
    b.clear()
    # Old generated graphs retain Entry -> Return even after body nodes clear.
    entry = b.entry(g)
    for pin in b.info(entry).output_pins:
        if pin.type_id == 'Exec':
            for linked in list(pin.connected_pins):
                BPT.break_pins(pin.pin_id, linked)
    if out:
        # a previous run may have declared the return value as an input pin
        for pn in ('ReturnValue',):
            try:
                b.ed.remove_graph_input_parameter(g, pn)
            except Exception:
                pass
    decls = [(p[0], p[1], p[2] if len(p) > 2 else True) for p in params]
    if out:
        decls.append((out[0], out[1], False))
    for pname, ptype, pin in decls:
        try:
            BPT.add_function_param(g, pname, ptype, pin, None)
        except Exception as exc:
            if 'already exists' not in str(exc):
                warn('param %s/%s: %r' % (name, pname, exc))
    return g, b, (b.entry(g), 'then')


def comp_class_ref(spec):
    """A /Script/... class path usable on a ComponentClass pin."""
    if spec.startswith('/Game/'):
        return K.cls_path(spec)
    if spec.startswith('/'):
        return spec
    return '/Script/Engine.' + spec


def self_comp(b, bp_or_native):
    """GetComponentByClass on this blueprint's own actor (self is implicit)."""
    n = b.n(K.F_GET_COMP)
    b.setv(n, 'ComponentClass', comp_class_ref(bp_or_native))
    return (n, 'ReturnValue')


def own_comp(b, native_class):
    """Typed component on the actor that owns this component."""
    own = b.c(K.F_GET_OWNER)
    n = b.n(K.F_GET_COMP)
    b.link(own, 'ReturnValue', n, 'self')
    b.setv(n, 'ComponentClass', comp_class_ref(native_class))
    return (n, 'ReturnValue'), own


def comp_of_ref(b, actor_ref, bp_or_native):
    n = b.n(K.F_GET_COMP)
    b.link(actor_ref[0], actor_ref[1], n, 'self')
    b.setv(n, 'ComponentClass', comp_class_ref(bp_or_native))
    return (n, 'ReturnValue')


def color(b, r, g, bl, a=1.0):
    n = b.n('Math|Color|MakeColor')
    b.setv(n, 'R', str(r))
    b.setv(n, 'G', str(g))
    b.setv(n, 'B', str(bl))
    b.setv(n, 'A', str(a))
    return (n, 'ReturnValue')


# --------------------------------------------------------------------------- #
# 1. investigation component
# --------------------------------------------------------------------------- #

INV_STATE = ('bHasDoc', 'bHasTape', 'bTapeHeard', 'bCorroborated', 'bRevealed',
             'bBeatDone', 'bEnded', 'JournalOpen')

INV_TEXT = {
    'ObjectiveText': OBJ[0], 'PromptText': MSG_NONE, 'SubtitleText': MSG_NONE,
    'MsgAlready': MSG_ALREADY, 'MsgDocGot': MSG_DOC, 'MsgTapeGot': MSG_TAPE,
    'MsgTapeHeard': MSG_TAPE_HEARD, 'MsgReveal': MSG_REVEAL, 'MsgBeat': MSG_BEAT,
    'MsgCorroborated': MSG_CORROB, 'MsgOpening': MSG_OPENING,
    'Obj0': OBJ[0], 'Obj1': OBJ[1], 'Obj2': OBJ[2], 'Obj3': OBJ[3],
    'Obj4': OBJ[4], 'Obj5': OBJ[5], 'Obj6': OBJ[6],
    'Obj7': OBJ[7],
    'Corrob1': CORROB[0], 'Corrob2': CORROB[1], 'Corrob3': CORROB[2],
    'Corrob4': CORROB[3], 'Corrob5': CORROB[4], 'Corrob6': CORROB[5],
    'EndTitle': ENDING[0], 'EndLine1': ENDING[1], 'EndLine2': ENDING[2],
    'EndLine3': ENDING[3], 'EndLine4': ENDING[4], 'HintEnd': HINT_END,
}

DEF_FIELDS = [('TitleStr', 'GetTitleStr'), ('SourceStr', 'GetSourceStr'),
              ('Body1Str', 'GetBody1Str'), ('Body2Str', 'GetBody2Str'),
              ('Body3Str', 'GetBody3Str'), ('Body4Str', 'GetBody4Str'),
              ('Clue1Str', 'GetClue1Str'), ('Clue2Str', 'GetClue2Str'),
              ('Clue3Str', 'GetClue3Str')]

INV_STATE_GETTERS = [('GetHasDoc', 'bHasDoc'), ('GetHasTape', 'bHasTape'),
                     ('GetTapeHeard', 'bTapeHeard'),
                     ('GetCorroborated', 'bCorroborated'),
                     ('GetBeatDone', 'bBeatDone'), ('GetEnded', 'bEnded'),
                     ('GetJournalOpen', 'JournalOpen')]


def build_investigation(repair_definition=True):
    step('BP_KL_InvestigationComponent')
    # The evidence asset's getters are read by other pure getters and the HUD.
    # Older builds created them as impure functions, causing Unreal to prune
    # every unwired Exec call and return empty default values at runtime.
    definition = K.load(DEF)
    if repair_definition:
        for graph in BPT.list_graphs(definition):
            if graph.get_name() in {name for _, name in DEF_FIELDS}:
                K.B(graph, graph.get_name()).ed.set_is_pure_function(True)
        BPT.compile_blueprint(definition)
        K.save(DEF)
    bp, path = K.new_bp(K.F_CORE, 'BP_KL_InvestigationComponent', 'ActorComponent')
    for v in INV_TEXT:
        K.var(bp, v, 'text')
    for v in INV_STATE:
        K.var(bp, v, 'bool')
    K.var_obj(bp, 'DocDef', DEF)
    K.var_obj(bp, 'TapeDef', DEF)
    K.var_obj(bp, 'Collected', DEF, ContainerType.ARRAY)
    BPT.compile_blueprint(bp)
    for v, txt in INV_TEXT.items():
        K.set_cdo(bp, v, unreal.Text(txt))
    for v in INV_STATE:
        K.set_cdo(bp, v, False)
    c = K.cdo(bp)
    c.set_editor_property('DocDef', K.load(K.F_DATA + '/EVD_SoDiemDanh'))
    c.set_editor_property('TapeDef', K.load(K.F_DATA + '/EVD_Bang021634'))
    ok('DocDef=%s  TapeDef=%s' % (c.get_editor_property('DocDef').get_name(),
                                  c.get_editor_property('TapeDef').get_name()))

    for f, v in (('GetObjectiveStr', 'ObjectiveText'),
                 ('GetPromptStr', 'PromptText'),
                 ('GetSubtitleStr', 'SubtitleText')):
        text_getter(bp, f, v)
    for f, v in INV_STATE_GETTERS:
        bool_getter(bp, f, v)
    for slot, defvar in (('Doc', 'DocDef'), ('Tape', 'TapeDef')):
        for suffix, fname in DEF_FIELDS:
            def_getter(bp, 'Get%s%s' % (slot, suffix), defvar, fname)
    for i in range(1, 7):
        text_getter(bp, 'GetCorrob%dStr' % i, 'Corrob%d' % i)
    text_getter(bp, 'GetEndTitleStr', 'EndTitle')
    for i in range(1, 5):
        text_getter(bp, 'GetEndLine%dStr' % i, 'EndLine%d' % i)
    text_getter(bp, 'GetHintEndStr', 'HintEnd')

    inv_logic(bp)
    K.save(path)
    return path


def inv_logic(bp):
    g, b, e = newfn(bp, 'InitRun')
    for v in INV_STATE:
        e = cont(b, e, sb(b, v, False))
    e = cont(b, e, sv(b, 'ObjectiveText', OBJ[0]))
    e = cont(b, e, sv(b, 'SubtitleText', MSG_OPENING))
    b.ret()
    b.compile(bp, 'InitRun')

    # ---- RefreshObjective: beat > revealed > corroborated > flags --------- #
    g, b, e = newfn(bp, 'RefreshObjective')

    def setobj(en, text):
        return cont(b, en, sv(b, 'ObjectiveText', text))

    def lvl4(en):
        iff(b, en, lambda: bv(b, 'bHasDoc'),
            then_fn=lambda x: iff(b, x, lambda: bv(b, 'bHasTape'),
                                  then_fn=lambda y: iff(
                                      b, y, lambda: bv(b, 'bTapeHeard'),
                                      then_fn=lambda z: setobj(z, OBJ[7]),
                                      else_fn=lambda z: setobj(z, OBJ[3])),
                                  else_fn=lambda y: setobj(y, OBJ[1])),
            else_fn=lambda x: iff(b, x, lambda: bv(b, 'bHasTape'),
                                  then_fn=lambda y: setobj(y, OBJ[2]),
                                  else_fn=lambda y: setobj(y, OBJ[0])))
        return en

    def lvl3(en):
        iff(b, en, lambda: bv(b, 'bCorroborated'),
            then_fn=lambda x: setobj(x, OBJ[4]), else_fn=lvl4)
        return en

    def lvl2(en):
        iff(b, en, lambda: bv(b, 'bRevealed'),
            then_fn=lambda x: setobj(x, OBJ[5]), else_fn=lvl3)
        return en

    iff(b, e, lambda: bv(b, 'bBeatDone'),
        then_fn=lambda x: setobj(x, OBJ[6]), else_fn=lvl2)
    b.ret()
    b.compile(bp, 'RefreshObjective')

    for kind, flagvar, defvar, msg, label in (
            ('Doc', 'bHasDoc', 'DocDef', 'MsgDocGot', 'EVD_DOC_ROLLCALL'),
            ('Tape', 'bHasTape', 'TapeDef', 'MsgTapeGot', 'EVD_TAPE_0216')):
        g, b, e = newfn(bp, 'Collect%s' % kind)

        def collect(en, flagvar=flagvar, defvar=defvar, msg=msg, label=label):
            arr = b.g('Collected')
            add = b.n(K.F_ARR_ADD)
            b.link(en[0], en[1], add, 'execute')
            b.link(arr, b.out_any(arr).name, add, 'TargetArray')
            b.link(b.g(defvar), b.out_any(b.g(defvar)).name, add, 'NewItem')
            en = (add, 'then')
            en = cont(b, en, sb(b, flagvar, True))
            en = cont(b, en, sv(b, 'SubtitleText', msg))
            en = cont(b, en, b.print('KL: collected %s' % label))
            return cont(b, en, callbp(b, INV, 'RefreshObjective'))

        iff(b, e, lambda: bv(b, flagvar),
            then_fn=lambda x: setp(b, x, 'SubtitleText', b.g('MsgAlready'),
                                   b.out_any(b.g('MsgAlready')).name),
            else_fn=collect)
        b.ret()
        b.compile(bp, 'Collect%s' % kind)

    for fname, flagvar, msg, label in (
            ('SetTapeHeard', 'bTapeHeard', 'MsgTapeHeard', 'tape heard in NGHE LOC'),
            ('NoteRevealed', 'bRevealed', 'MsgReveal', 'figure revealed')):
        g, b, e = newfn(bp, fname)

        def go(en, flagvar=flagvar, msg=msg, label=label):
            en = cont(b, en, sb(b, flagvar, True))
            en = cont(b, en, sv(b, 'SubtitleText', msg))
            en = cont(b, en, b.print('KL: %s' % label))
            return cont(b, en, callbp(b, INV, 'RefreshObjective'))

        iff(b, e, lambda: bv(b, flagvar), else_fn=go)
        b.ret()
        b.compile(bp, fname)

    g, b, e = newfn(bp, 'BeginBeat')

    def beat(en):
        en = cont(b, en, sb(b, 'bBeatDone', True))
        en = cont(b, en, sv(b, 'ObjectiveText', OBJ[6]))
        en = cont(b, en, sv(b, 'SubtitleText', MSG_BEAT))
        return cont(b, en, b.print('KL: roll call beat fired'))

    iff(b, e, lambda: bv(b, 'bBeatDone'), else_fn=beat)
    b.ret()
    b.compile(bp, 'BeginBeat')

    g, b, e = newfn(bp, 'FinishRun')
    e = cont(b, e, sb(b, 'bEnded', True))
    e = cont(b, e, b.print('KL: MILESTONE1 COMPLETE'))
    b.ret()
    b.compile(bp, 'FinishRun')

    # ---- ToggleJournal ----------------------------------------------------- #
    g, b, e = newfn(bp, 'ToggleJournal')

    def fresh(en):
        en = cont(b, en, sb(b, 'bCorroborated', True))
        en = cont(b, en, sv(b, 'SubtitleText', MSG_CORROB))
        en = cont(b, en, b.print('KL: journal corroborated'))
        return cont(b, en, callbp(b, INV, 'RefreshObjective'))

    def both(en):
        iff(b, en, lambda: bv(b, 'bCorroborated'), else_fn=fresh)
        return en

    iff(b, e, lambda: bv(b, 'JournalOpen'),
        then_fn=lambda x: cont(b, x, sb(b, 'JournalOpen', False)),
        else_fn=lambda x: iff(
            b, cont(b, x, sb(b, 'JournalOpen', True)),
            lambda: bv(b, 'bHasDoc'),
            then_fn=lambda y: iff(
                b, y, lambda: bv(b, 'bHasTape'),
                then_fn=lambda z: iff(
                    b, z, lambda: bv(b, 'bTapeHeard'), then_fn=both))))
    b.ret()
    b.compile(bp, 'ToggleJournal')

    for fname, pname, target, is_text in (
            ('SetPromptFromString', 'InS', 'PromptText', False),
            ('SetSubtitleFromString', 'InS', 'SubtitleText', False),
            ('SetSubtitleText', 'InT', 'SubtitleText', True),
            ('SetObjectiveText', 'InT', 'ObjectiveText', True)):
        g, b, e = newfn(bp, fname, [(pname, 'text' if is_text else 'string', True)])
        s = b.s(target)
        b.link(e[0], e[1], s, 'execute')
        if is_text:
            b.link_param(g, pname, s, target)
        else:
            conv = b.c(K.F_STR2TEXT)
            b.link_param(g, pname, conv, 'InString')
            b.link(conv, 'ReturnValue', s, target)
        b.ret()
        b.compile(bp, fname)

    g, b, e = newfn(bp, 'ClearPrompt')
    e = cont(b, e, sv(b, 'PromptText', MSG_NONE))
    b.ret()
    b.compile(bp, 'ClearPrompt')


# --------------------------------------------------------------------------- #
# 2. listening component
# --------------------------------------------------------------------------- #

LIS_BOOL = ('bFilterOn', 'bStarted')
LIS_FLOAT = ('VolAmbNormal', 'VolAmbFiltered', 'VolMaskNormal', 'VolMaskFiltered',
             'VolClarNormal', 'VolClarFiltered', 'VolHumNormal', 'VolHumFiltered',
             'LowPassCutoff', 'Zero')

BEDS = (('Amb', 'AmbWave', 'S_KL_Ambience_Hall', 'VolAmbNormal'),
        ('Mask', 'MaskWave', 'S_KL_NoiseMask', 'VolMaskNormal'),
        ('Clar', 'ClarWave', 'S_KL_ClarityTone', 'VolClarNormal'),
        ('Hum', 'HumWave', 'S_KL_SpeakerHum', 'VolHumNormal'))

ADJUST = (('Mask', 'VolMaskNormal', 'VolMaskFiltered', '0.45'),
          ('Clar', 'VolClarNormal', 'VolClarFiltered', '0.60'),
          ('Hum', 'VolHumNormal', 'VolHumFiltered', '0.80'))


def build_listening():
    step('BP_KL_ListeningComponent')
    bp, path = K.new_bp(K.F_CORE, 'BP_KL_ListeningComponent', 'ActorComponent')
    for v in LIS_BOOL:
        K.var(bp, v, 'bool')
    for v in LIS_FLOAT:
        K.var(bp, v, 'float')
    for v, w, _, _ in BEDS:
        K.var_obj(bp, v, 'AudioComponent')
        K.var_obj(bp, w, 'SoundWave')
    K.var_obj(bp, 'ModeSfx', 'SoundWave')
    BPT.compile_blueprint(bp)
    for v in LIS_BOOL:
        K.set_cdo(bp, v, False)
    for v in LIS_FLOAT:
        K.set_cdo(bp, v, MIX.get(v, 0.0))
    c = K.cdo(bp)
    for v, w, snd, _ in BEDS:
        c.set_editor_property(w, K.load('%s/%s' % (SND, snd)))
    c.set_editor_property('ModeSfx', K.load(SND + '/S_KL_UI_ModeShift'))
    ok('beds: %s' % ', '.join(snd for _, _, snd, _ in BEDS))

    # ---- StartBeds: spawn the four ambient beds on this component ---------- #
    g, b, e = newfn(bp, 'StartBeds')

    def spawn_bed(en, compvar, wavevar, volvar):
        spawn = b.c(K.F_SPAWNATLOC)
        b.link(en[0], en[1], spawn, 'execute')
        b.link(b.g(wavevar), b.out_any(b.g(wavevar)).name, spawn, 'Sound')
        zero = b.n('Math|Vector|MakeVector')
        b.setv(zero, 'X', '0.0')
        b.setv(zero, 'Y', '0.0')
        b.setv(zero, 'Z', '0.0')
        b.link(zero, 'ReturnValue', spawn, 'Location')
        b.link(b.g(volvar), b.out_any(b.g(volvar)).name, spawn, 'VolumeMultiplier')
        b.setv(spawn, 'bAutoDestroy', 'false')
        st = b.s(compvar)
        b.link(spawn, 'then', st, 'execute')
        b.link(spawn, 'ReturnValue', st, compvar)
        return (st, 'then')

    def beds(en):
        for compvar, wavevar, _, volvar in BEDS:
            en = spawn_bed(en, compvar, wavevar, volvar)
        return cont(b, en, sb(b, 'bStarted', True))

    iff(b, e, lambda: bv(b, 'bStarted'), else_fn=beds)
    b.ret()
    b.compile(bp, 'StartBeds')

    # ---- SetFilter: the two listening states ------------------------------- #
    g, b, e = newfn(bp, 'SetFilter', [('bOn', 'bool', True)])
    pon = b.param(g, 'bOn')
    P = (pon,)

    def vref(name):
        gv = b.g(name)
        return (gv, b.out_any(gv).name)

    volsel = selb(b, vref('VolAmbNormal'), vref('VolAmbFiltered'), P)
    n = b.c('/Script/Engine.AudioComponent:SetVolumeMultiplier')
    b.link(volsel[0], volsel[1], n, 'NewVolumeMultiplier')
    b.link(vref('Amb')[0], vref('Amb')[1], n, 'self')
    e = cont(b, e, n)
    n = b.c('/Script/Engine.AudioComponent:SetLowPassFilterEnabled')
    BPT.connect_pins(pon.pin_id, b.inp(n, 'InLowPassFilterEnabled').pin_id)
    b.link(vref('Amb')[0], vref('Amb')[1], n, 'self')
    e = cont(b, e, n)
    n = b.c('/Script/Engine.AudioComponent:SetLowPassFilterFrequency')
    b.link(vref('Amb')[0], vref('Amb')[1], n, 'self')
    b.link(vref('LowPassCutoff')[0], vref('LowPassCutoff')[1],
           n, 'InLowPassFilterFrequency')
    e = cont(b, e, n)

    for compvar, zv, ov, dur in ADJUST:
        s = selb(b, vref(zv), vref(ov), P)
        n = b.c('/Script/Engine.AudioComponent:AdjustVolume')
        b.setv(n, 'AdjustVolumeDuration', dur)
        b.link(s[0], s[1], n, 'AdjustVolumeLevel')
        b.link(vref(compvar)[0], vref(compvar)[1], n, 'self')
        e = cont(b, e, n)

    n = b.n(K.F_PLAY2D)
    ms = b.g('ModeSfx')
    b.link(ms, b.out_any(ms).name, n, 'Sound')
    b.setv(n, 'bIsUISound', 'true')
    e = cont(b, e, n)
    e = setp_param(b, g, e, 'bFilterOn', 'bOn')
    b.ret()
    b.compile(bp, 'SetFilter')

    bool_getter(bp, 'IsFilterOn', 'bFilterOn')

    g, b, e = newfn(bp, 'GetModeStr', out=('ReturnValue', 'string'))
    s = selb(b, 'NGHE THƯỜNG', 'NGHE LỌC', bv(b, 'bFilterOn'))
    b.ret(s[0], s[1])
    b.compile(bp, 'GetModeStr')
    K.save(path)
    return path


# --------------------------------------------------------------------------- #
# 3. interact component
# --------------------------------------------------------------------------- #

INT_BOOL = ('bTapeMode', 'bCornerMode', 'bNoteMode', 'bConsumed',
            'bTapeStarted', 'bPlayingClear', 'bReady', 'bFocus', 'bFilter', 'bBeatFired',
            'bHiddenAtStart')
INT_TEXT = {'PromptText': 'Xem', 'MsgConsumed': MSG_CONSUMED,
            'MsgNeedMore': MSG_NEED_MORE, 'MsgRoster': MSG_ROSTER}
INT_SOUNDS = ('MaskedWave', 'ClearWave', 'SfxTake', 'SfxBeat', 'SfxReply', 'SfxNote')
INT_FLOAT = ('Zero', 'RevealIntensity', 'BeatIntensity')


def build_interact():
    step('BP_KL_InteractComponent')
    bp, path = K.new_bp(K.F_CORE, 'BP_KL_InteractComponent', 'ActorComponent')
    for v in INT_BOOL:
        K.var(bp, v, 'bool')
    for v in INT_TEXT:
        K.var(bp, v, 'text')
    for v in INT_SOUNDS:
        K.var_obj(bp, v, 'SoundWave')
    for v in INT_FLOAT:
        K.var(bp, v, 'float')
    BPT.compile_blueprint(bp)
    for v in INT_BOOL:
        K.set_cdo(bp, v, False)
    for v, t in INT_TEXT.items():
        K.set_cdo(bp, v, unreal.Text(t))
    K.set_cdo(bp, 'Zero', 0.0)
    K.set_cdo(bp, 'RevealIntensity', MIX['RevealIntensity'])
    K.set_cdo(bp, 'BeatIntensity', MIX['BeatIntensity'])
    c = K.cdo(bp)
    c.set_editor_property('MaskedWave', K.load(SND + '/S_KL_T2_Masked'))
    c.set_editor_property('ClearWave', K.load(SND + '/S_KL_T2_Clear'))
    c.set_editor_property('SfxTake', K.load(SND + '/S_KL_TapeDeck'))
    c.set_editor_property('SfxBeat', K.load(SND + '/S_KL_RollCall'))
    c.set_editor_property('SfxReply', K.load(SND + '/S_KL_ChildReply'))
    c.set_editor_property('SfxNote', K.load(SND + '/S_KL_UI_Evidence'))
    ok('interact component ready')

    # ---- event graph: hide props that start invisible, corner light off ---- #
    g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    b = K.B(g, 'Int.EventGraph')
    b.clear()
    beg = b.ev('BeginPlay')
    mesh, _own = own_comp(b, 'StaticMeshComponent')
    light, _own2 = own_comp(b, 'PointLightComponent')
    hide = bv(b, 'bHiddenAtStart')

    def start_hidden(en):
        h = b.n(K.F_SET_HIDDEN)
        b.link(mesh[0], mesh[1], h, 'self')
        b.link(hide[0], hide[1], h, 'NewHidden')
        b.setv(h, 'bPropagateToChildren', 'true')
        en = cont(b, en, h)
        li = b.n(K.F_LIGHT_INT)
        b.link(light[0], light[1], li, 'self')
        b.setv(li, 'NewIntensity', '0.0')
        return cont(b, en, li)

    iff(b, (beg, 'then'), lambda: bv(b, 'bHiddenAtStart'), then_fn=start_hidden)
    b.compile(bp, '(event graph)')

    # ---- GetPromptStr / IsAvailable / IsFocused ---------------------------- #
    g, b, e = newfn(bp, 'GetPromptStr', out=('ReturnValue', 'string'))
    a = b.text2str(b.g('MsgConsumed'), b.out_any(b.g('MsgConsumed')).name)
    pn = b.text2str(b.g('PromptText'), b.out_any(b.g('PromptText')).name)
    s = selb(b, (a, 'ReturnValue'), (pn, 'ReturnValue'), bv(b, 'bConsumed'))
    b.ret(s[0], s[1])
    b.compile(bp, 'GetPromptStr')

    g, b, e = newfn(bp, 'IsAvailable', out=('ReturnValue', 'bool'))
    s = selb(b, 'true', 'false', bv(b, 'bConsumed'))
    b.ret(s[0], s[1])
    b.compile(bp, 'IsAvailable')

    bool_getter(bp, 'IsFocused', 'bFocus')

    # ---- SetFocused: reveal the corner only in NGHE LOC + ready state ----- #
    PARAMS = [('bFocused', 'bool', True), ('bFilter', 'bool', True),
              ('bHasDoc', 'bool', True), ('bHasTape', 'bool', True),
              ('bTapeHeard', 'bool', True)]
    g, b, e = newfn(bp, 'SetFocused', PARAMS)
    P = lambda n: (b.param(g, n),)
    ready = andb(b, andb(b, P('bHasDoc'), P('bHasTape')), P('bTapeHeard'))
    gate = andb(b, andb(b, andb(b, P('bFocused'), P('bFilter')),
                        bv(b, 'bCornerMode')), ready)
    show = orb(b, gate, bv(b, 'bBeatFired'))
    e = setp_param(b, g, e, 'bFocus', 'bFocused')
    e = setp_param(b, g, e, 'bFilter', 'bFilter')
    e = setp(b, e, 'bReady', ready[0], ready[1])
    corner_only = b.branch()
    b.link(e[0], e[1], corner_only, 'execute')
    corner_flag = b.g('bCornerMode')
    b.link(corner_flag, b.out_any(corner_flag).name, corner_only, 'Condition')
    e = (corner_only, 'then')
    mesh, own = own_comp(b, 'StaticMeshComponent')
    hide = notb(b, show)
    n = b.n(K.F_SET_HIDDEN)
    b.link(mesh[0], mesh[1], n, 'self')
    b.link(hide[0], hide[1], n, 'NewHidden')
    b.setv(n, 'bPropagateToChildren', 'true')
    e = cont(b, e, n)
    light, own2 = own_comp(b, 'PointLightComponent')
    inten = selb(b, (b.g('Zero'), b.out_any(b.g('Zero')).name),
                 (b.g('RevealIntensity'),
                  b.out_any(b.g('RevealIntensity')).name), show)
    n = b.n(K.F_LIGHT_INT)
    b.link(light[0], light[1], n, 'self')
    b.link(inten[0], inten[1], n, 'NewIntensity')
    e = cont(b, e, n)
    b.ret()
    b.compile(bp, 'SetFocused')

    # ---- player handles (no object params exist in this toolset) ---------- #
    def player_comp(b, bp_path):
        pawn = b.c('/Script/Engine.GameplayStatics:GetPlayerPawn')
        b.setv(pawn, 'PlayerIndex', '0')
        return comp_of_ref(b, (pawn, 'ReturnValue'), bp_path)

    def player_filter(b):
        lis = player_comp(b, LIS)
        call = callbp(b, LIS, 'IsFilterOn')
        b.link(lis[0], lis[1], call, 'self')
        return (call, 'ReturnValue')

    # Completion is earned only after the full 16-second clear tape has played.
    # The timer is reset on replay and cancelled whenever the masked layer is
    # selected, so a quick mode toggle cannot satisfy the investigation gate.
    def tape_timer(b, en, node_id, arm=False):
        n = b.n(node_id)
        ref = b.n('Variables|Getareferencetoself')
        b.link(ref, 'self', n, 'Object')
        b.setv(n, 'FunctionName', 'CompleteClearTape')
        if arm:
            b.setv(n, 'Time', '16.0')
            b.setv(n, 'bLooping', 'false')
        return cont(b, en, n)

    g, b, e = newfn(bp, 'DisarmClearTape')
    e = cont(b, e, sb(b, 'bPlayingClear', False))
    tape_timer(b, e, 'Utilities|Time|ClearTimerbyFunctionName')
    b.ret()
    b.compile(bp, 'DisarmClearTape')

    g, b, e = newfn(bp, 'ArmClearTape')
    e = tape_timer(b, e, 'Utilities|Time|ClearTimerbyFunctionName')
    e = cont(b, e, sb(b, 'bPlayingClear', True))
    tape_timer(b, e, 'Utilities|Time|SetTimerbyFunctionName', arm=True)
    b.ret()
    b.compile(bp, 'ArmClearTape')

    g, b, e = newfn(bp, 'CompleteClearTape')
    inv = player_comp(b, INV)

    def mark_heard(en):
        call = callbp(b, INV, 'SetTapeHeard')
        b.link(inv[0], inv[1], call, 'self')
        en = cont(b, en, call)
        return cont(b, en, sb(b, 'bPlayingClear', False))

    iff(b, e, lambda: bv(b, 'bPlayingClear'), then_fn=mark_heard)
    b.ret()
    b.compile(bp, 'CompleteClearTape')

    # ---- DoDocument ------------------------------------------------------- #
    g, b, e = newfn(bp, 'DoDocument')
    inv = player_comp(b, INV)
    collect = callbp(b, INV, 'CollectDoc')
    b.link(inv[0], inv[1], collect, 'self')
    e = cont(b, e, collect)

    def consume(en):
        mesh, own = own_comp(b, 'StaticMeshComponent')
        n = b.n(K.F_SET_HIDDEN)
        b.link(mesh[0], mesh[1], n, 'self')
        b.setv(n, 'NewHidden', 'true')
        b.setv(n, 'bPropagateToChildren', 'true')
        en = cont(b, en, n)
        n = b.n(K.F_PLAY2D)
        sv_ = b.g('SfxTake')
        b.link(sv_, b.out_any(sv_).name, n, 'Sound')
        en = cont(b, en, n)
        return cont(b, en, sb(b, 'bConsumed', True))

    iff(b, e, lambda: bv(b, 'bConsumed'), else_fn=consume)
    b.ret()
    b.compile(bp, 'DoDocument')

    # ---- DoTape ----------------------------------------------------------- #
    g, b, e = newfn(bp, 'DoTape')
    inv = player_comp(b, INV)
    collect = callbp(b, INV, 'CollectTape')
    b.link(inv[0], inv[1], collect, 'self')
    e = cont(b, e, collect)
    n = b.n(K.F_PLAY2D)
    sv_ = b.g('SfxTake')
    b.link(sv_, b.out_any(sv_).name, n, 'Sound')
    e = cont(b, e, n)
    tape, own = own_comp(b, 'AudioComponent')
    filt = player_filter(b)

    def play(wavevar):
        def fn(en):
            n = b.n(K.F_AC_SET_SOUND)
            w = b.g(wavevar)
            b.link(w, b.out_any(w).name, n, 'NewSound')
            b.link(tape[0], tape[1], n, 'self')
            en = cont(b, en, n)
            n = b.n(K.F_AC_PLAY)
            b.link(tape[0], tape[1], n, 'self')
            en = cont(b, en, n)
            timer_fn = 'ArmClearTape' if wavevar == 'ClearWave' else 'DisarmClearTape'
            return cont(b, en, callbp(b, INT, timer_fn))
        return fn

    e = iff(b, e, lambda: filt, then_fn=play('ClearWave'), else_fn=play('MaskedWave'))
    e = cont(b, e, sb(b, 'bTapeStarted', True))
    b.ret()
    b.compile(bp, 'DoTape')

    # ---- DoNote ----------------------------------------------------------- #
    g, b, e = newfn(bp, 'DoNote')
    n = b.n(K.F_PLAY2D)
    sv_ = b.g('SfxNote')
    b.link(sv_, b.out_any(sv_).name, n, 'Sound')
    e = cont(b, e, n)
    inv = player_comp(b, INV)
    call = callbp(b, INV, 'SetSubtitleText')
    b.link(inv[0], inv[1], call, 'self')
    b.link(b.g('MsgRoster'), b.out_any(b.g('MsgRoster')).name, call, 'InT')
    e = cont(b, e, call)
    b.ret()
    b.compile(bp, 'DoNote')

    # Function graphs cannot own latent Delay nodes. Timers retain the actor
    # component as their owner and let the game world advance between beats.
    def schedule(b, en, function, seconds):
        node = b.n('Utilities|Time|SetTimerbyFunctionName')
        ref = b.n('Variables|Getareferencetoself')
        b.link(ref, 'self', node, 'Object')
        b.setv(node, 'FunctionName', function)
        b.setv(node, 'Time', str(seconds))
        b.setv(node, 'bLooping', 'false')
        return cont(b, en, node)

    g, b, e = newfn(bp, 'FinishBeat')
    inv = player_comp(b, INV)
    call = callbp(b, INV, 'FinishRun')
    b.link(inv[0], inv[1], call, 'self')
    cont(b, e, call)
    b.ret()
    b.compile(bp, 'FinishBeat')

    g, b, e = newfn(bp, 'ReplyBeat')
    owner = b.c(K.F_GET_OWNER)
    loc = b.n(K.F_GET_ACTOR_LOC)
    b.link(owner, 'ReturnValue', loc, 'self')
    sound = b.c(K.F_PLAYATLOC)
    wave = b.g('SfxReply')
    b.link(wave, b.out_any(wave).name, sound, 'Sound')
    b.link(loc, 'ReturnValue', sound, 'Location')
    e = cont(b, e, sound)
    schedule(b, e, 'FinishBeat', 3.2)
    b.ret()
    b.compile(bp, 'ReplyBeat')

    # ---- DoCorner: the scripted supernatural beat ------------------------- #
    g, b, e = newfn(bp, 'DoCorner')
    inv = player_comp(b, INV)
    mesh, own = own_comp(b, 'StaticMeshComponent')
    loc = b.n(K.F_GET_ACTOR_LOC)
    b.link(own, 'ReturnValue', loc, 'self')
    light, own2 = own_comp(b, 'PointLightComponent')

    def play_at(wavevar):
        def fn(en):
            n = b.c(K.F_PLAYATLOC)
            w = b.g(wavevar)
            b.link(w, b.out_any(w).name, n, 'Sound')
            b.link(loc, b.out_any(loc).name, n, 'Location')
            return cont(b, en, n)
        return fn

    def beat(en):
        n = b.n(K.F_SET_HIDDEN)
        b.link(mesh[0], mesh[1], n, 'self')
        b.setv(n, 'NewHidden', 'false')
        b.setv(n, 'bPropagateToChildren', 'true')
        en = cont(b, en, n)
        n = b.n(K.F_LIGHT_INT)
        b.link(light[0], light[1], n, 'self')
        bi = b.g('BeatIntensity')
        b.link(bi, b.out_any(bi).name, n, 'NewIntensity')
        en = cont(b, en, n)
        n = b.n(K.F_LIGHT_COLOR)
        b.link(light[0], light[1], n, 'self')
        red = color(b, 0.55, 0.06, 0.06)
        b.link(red[0], red[1], n, 'NewLightColor')
        b.setv(n, 'bSRGB', 'true')
        en = cont(b, en, n)
        en = play_at('SfxBeat')(en)
        en = cont(b, en, sb(b, 'bBeatFired', True))
        call = callbp(b, INV, 'BeginBeat')
        b.link(inv[0], inv[1], call, 'self')
        en = cont(b, en, call)
        return schedule(b, en, 'ReplyBeat', 13.0)

    def need_more(en):
        call = callbp(b, INV, 'SetSubtitleText')
        b.link(inv[0], inv[1], call, 'self')
        b.link(b.g('MsgNeedMore'), b.out_any(b.g('MsgNeedMore')).name, call, 'InT')
        return cont(b, en, call)

    iff(b, e, lambda: bv(b, 'bBeatFired'),
        else_fn=lambda x: iff(b, x, lambda: bv(b, 'bReady'),
                              then_fn=beat, else_fn=need_more))
    b.ret()
    b.compile(bp, 'DoCorner')

    # ---- SetFilterMode: restart the selected layer and its completion gate - #
    g, b, e = newfn(bp, 'SetFilterMode', [('bOn', 'bool', True)])
    tape, own = own_comp(b, 'AudioComponent')

    def set_sound(wavevar):
        def fn(en):
            n = b.n(K.F_AC_SET_SOUND)
            w = b.g(wavevar)
            b.link(w, b.out_any(w).name, n, 'NewSound')
            b.link(tape[0], tape[1], n, 'self')
            en = cont(b, en, n)
            n = b.n(K.F_AC_PLAY)
            b.link(tape[0], tape[1], n, 'self')
            en = cont(b, en, n)
            timer_fn = 'ArmClearTape' if wavevar == 'ClearWave' else 'DisarmClearTape'
            return cont(b, en, callbp(b, INT, timer_fn))
        return fn

    iff(b, e, lambda: bv(b, 'bTapeMode'),
        then_fn=lambda x: iff(
            b, x, lambda: bv(b, 'bTapeStarted'),
            then_fn=lambda y: iff(
                b, y, lambda: (b.entry(g), 'bOn'),
                then_fn=set_sound('ClearWave'),
                else_fn=set_sound('MaskedWave'))))
    b.ret()
    b.compile(bp, 'SetFilterMode')

    # ---- DoInteract dispatch ---------------------------------------------- #
    g, b, e = newfn(bp, 'DoInteract')
    iff(b, e, lambda: bv(b, 'bCornerMode'),
        then_fn=lambda x: cont(b, x, callbp(b, INT, 'DoCorner')),
        else_fn=lambda x: iff(
            b, x, lambda: bv(b, 'bTapeMode'),
            then_fn=lambda y: cont(b, y, callbp(b, INT, 'DoTape')),
            else_fn=lambda y: iff(
                b, y, lambda: bv(b, 'bNoteMode'),
                then_fn=lambda z: cont(b, z, callbp(b, INT, 'DoNote')),
                else_fn=lambda z: cont(b, z, callbp(b, INT, 'DoDocument')))))
    b.ret()
    b.compile(bp, 'DoInteract')

    bad = b.audit(bp)
    if bad:
        for x in bad:
            fail('unconnected self pin: %s' % x)
    else:
        ok('component-method self pins all connected')

    K.save(path)
    return path


# --------------------------------------------------------------------------- #
# 4. template character, extended in place
# --------------------------------------------------------------------------- #

CHAR_STR = ('MsgListenOnStr', 'MsgListenOffStr')


def player_pawn(b):
    pawn = b.c('/Script/Engine.GameplayStatics:GetPlayerPawn')
    b.setv(pawn, 'PlayerIndex', '0')
    return (pawn, 'ReturnValue')


def player_ctrl(b):
    pc = b.c('/Script/Engine.GameplayStatics:GetPlayerController')
    b.setv(pc, 'PlayerIndex', '0')
    return (pc, 'ReturnValue')


def key_pressed(b, letter, pc):
    """WasInputKeyJustPressed with an FKey struct literal.

    MakeKey exposes no editable pin in this build (add_node_pin takes a single
    argument), so the struct default is written straight onto the Key pin.
    """
    n = b.c(K.F_KEY_DOWN)
    b.setv(n, 'Key', '(KeyName="%s")' % letter)
    b.link(pc[0], pc[1], n, 'self')
    return (n, 'ReturnValue')


def build_character():
    step('BP_FirstPersonCharacter (extended in place)')
    bp = K.load(CHAR, unreal.Blueprint)
    path = CHAR
    selfcls = bp.get_path_name() + '_C'
    for v in CHAR_STR:
        K.var(bp, v, 'string')
    K.var(bp, 'TorchOn', 'bool')
    K.var(bp, 'NextFilterOn', 'bool')
    K.var_obj(bp, 'FocusCand', INT)
    K.var_obj(bp, 'FocusPrev', INT)
    BPT.compile_blueprint(bp)
    cdo = K.cdo(bp)
    cdo.set_editor_property('MsgListenOnStr', LISTEN_ON)
    cdo.set_editor_property('MsgListenOffStr', LISTEN_OFF)
    cdo.set_editor_property('TorchOn', True)
    BPT.compile_blueprint(bp)

    inv_c = K.add_comp(bp, INV, 'KL_Investigation')
    lis_c = K.add_comp(bp, LIS, 'KL_Listening')
    cam = K.find_comp_of(bp, 'CameraComponent')
    torch = K.find_comp_of(bp, 'SpotLightComponent')
    if torch is None:
        torch = K.add_comp(bp, 'SpotLightComponent', 'KL_Torch', parent=cam)
    for prop, val in (('inner_cone_angle', 22.0), ('outer_cone_angle', 48.0),
                      ('attenuation_radius', 2200.0), ('cast_shadows', False),
                      ('light_color', unreal.Color(1.0, 0.93, 0.80)),
                      ('visible', True)):
        K.comp_set(torch, prop, val, 'torch')
    ok('components added: investigate=%s listening=%s torch=%s camera=%s' % (
        inv_c is not None, lis_c is not None, torch is not None, cam is not None))

    g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    b = K.B(g, 'Char.EventGraph')
    b.clear(keep_prefixes=())

    def me(kb, fname):
        return kb.c('%s:%s' % (selfcls, fname))

    def vref(kb, name):
        gv = kb.g(name)
        return (gv, kb.out_any(gv).name)

    def call_on_self(kb, target, fname):
        """Call `fname` on a component of this blueprint's own actor."""
        n = callbp(kb, target, fname)
        c = self_comp(kb, target)
        kb.link(c[0], c[1], n, 'self')
        return (n, 'ReturnValue')

    def ison(kb, target, fname):
        """Boolean state query on one of this actor's components."""
        return call_on_self(kb, target, fname)

    # ---- InitKL ------------------------------------------------------------ #
    gk, kb, e = newfn(bp, 'InitKL')
    n = callbp(kb, INV, 'InitRun')
    c = self_comp(kb, INV)
    kb.link(c[0], c[1], n, 'self')
    e = cont(kb, e, n)
    n = callbp(kb, LIS, 'StartBeds')
    c = self_comp(kb, LIS)
    kb.link(c[0], c[1], n, 'self')
    e = cont(kb, e, n)
    e = cont(kb, e, sb(kb, 'TorchOn', True))
    e = cont(kb, e, kb.print('KL: InitKL ready'))
    kb.ret()
    kb.compile(bp, 'InitKL')

    # ---- UpdateFocus -------------------------------------------------------- #
    gk, kb, e = newfn(bp, 'UpdateFocus')
    trace = kb.n(K.F_SPHERE_TRACE)
    loc = kb.n(K.F_GET_ACTOR_LOC)
    kb.link(loc, 'ReturnValue', trace, 'Start')
    kb.link(loc, 'ReturnValue', trace, 'End')
    kb.setv(trace, 'Radius', '260.0')
    kb.setv(trace, 'TraceChannel', 'ETraceTypeQuery::Visibility')
    kb.setv(trace, 'DrawDebugType', 'EDrawDebugTrace::None')
    kb.setv(trace, 'bIgnoreSelf', 'true')
    brk = kb.n(K.F_BREAK_HIT)
    kb.link(trace, 'OutHit', brk, 'Hit')
    comp = comp_of_ref(kb, (brk, 'HitActor'), INT)
    comp_node, comp_pin_name = comp
    comp_pin = kb.out(comp_node, comp_pin_name)
    valid = kb.c(K.F_ISVALID)
    kb.link(comp[0], comp[1], valid, 'Object')

    filt = ison(kb, LIS, 'IsFilterOn')
    hasdoc = ison(kb, INV, 'GetHasDoc')
    hasTape = ison(kb, INV, 'GetHasTape')
    heard = ison(kb, INV, 'GetTapeHeard')

    def unfocus(en, ref):
        n = callbp(kb, INT, 'SetFocused')
        kb.link(ref[0], ref[1], n, 'self')
        for pn in ('bFocused', 'bFilter', 'bHasDoc', 'bHasTape', 'bTapeHeard'):
            kb.setv(n, pn, 'false')
        return cont(kb, en, n)

    def focus(en):
        cand = kb.s('FocusCand')
        kb.link(en[0], en[1], cand, 'execute')
        kb.link(comp_node, comp_pin_name, cand, 'FocusCand')
        en = (cand, 'then')
        prev = vref(kb, 'FocusPrev')
        en = unfocus(en, prev)
        n = callbp(kb, INT, 'SetFocused')
        BPT.connect_pins(comp_pin.pin_id, kb.inp(n, 'self').pin_id)
        kb.setv(n, 'bFocused', 'true')
        for pn, ref in (('bFilter', filt), ('bHasDoc', hasdoc),
                        ('bHasTape', hasTape), ('bTapeHeard', heard)):
            BPT.connect_pins(kb.out(ref[0], ref[1]).pin_id, kb.inp(n, pn).pin_id)
        en = cont(kb, en, n)
        prompt = callbp(kb, INT, 'GetPromptStr')
        BPT.connect_pins(comp_pin.pin_id, kb.inp(prompt, 'self').pin_id)
        call = callbp(kb, INV, 'SetPromptFromString')
        c = self_comp(kb, INV)
        kb.link(c[0], c[1], call, 'self')
        kb.link(prompt, 'ReturnValue', call, 'InS')
        return cont(kb, en, call)

    prev = vref(kb, 'FocusCand')
    pvalid = kb.c(K.F_ISVALID)
    kb.link(prev[0], prev[1], pvalid, 'Object')
    e = iff(kb, e, lambda: (pvalid, 'ReturnValue'),
        then_fn=lambda x: unfocus(x, prev),
        else_fn=lambda x: cont(kb, x, trace))

    def clear_prompt(en):
        call = callbp(kb, INV, 'ClearPrompt')
        c = self_comp(kb, INV)
        kb.link(c[0], c[1], call, 'self')
        return cont(kb, en, call)

    iff(kb, e, lambda: (valid, 'ReturnValue'), then_fn=focus,
        else_fn=lambda x: clear_prompt(
            unfocus(x, vref(kb, 'FocusCand'))))
    kb.ret()
    kb.compile(bp, 'UpdateFocus')

    # ---- PollKeys ----------------------------------------------------------- #
    gk, kb, e = newfn(bp, 'PollKeys')
    pc = player_ctrl(kb)
    pawn = player_pawn(kb)
    filt = ison(kb, LIS, 'IsFilterOn')
    kq = key_pressed(kb, 'Q', pc)
    ke = key_pressed(kb, 'E', pc)
    ktab = key_pressed(kb, 'Tab', pc)
    kf = key_pressed(kb, 'F', pc)
    kent = key_pressed(kb, 'Enter', pc)
    kesc = key_pressed(kb, 'Escape', pc)
    jopen = ison(kb, INV, 'GetJournalOpen')
    ended = ison(kb, INV, 'GetEnded')
    focusref = vref(kb, 'FocusCand')
    fvalid = kb.c(K.F_ISVALID)
    kb.link(focusref[0], focusref[1], fvalid, 'Object')
    fcond = (fvalid, 'ReturnValue')

    def toggle_filter(en):
        nf = notb(kb, filt)
        store = kb.s('NextFilterOn')
        kb.link(nf[0], nf[1], store, 'NextFilterOn')
        en = cont(kb, en, store)
        nf = vref(kb, 'NextFilterOn')
        n = callbp(kb, LIS, 'SetFilter')
        c = self_comp(kb, LIS)
        kb.link(c[0], c[1], n, 'self')
        BPT.connect_pins(kb.out(nf[0], nf[1]).pin_id, kb.inp(n, 'bOn').pin_id)
        en = cont(kb, en, n)
        msg = selb(kb, vref(kb, 'MsgListenOffStr'), vref(kb, 'MsgListenOnStr'), nf)
        call = callbp(kb, INV, 'SetSubtitleFromString')
        c = self_comp(kb, INV)
        kb.link(c[0], c[1], call, 'self')
        kb.link(msg[0], msg[1], call, 'InS')
        en = cont(kb, en, call)
        # The tape may still be audible after the player steps away from it.
        # The graybox and art levels use separate Actor classes with the same
        # interaction component, so check both rather than using FocusCand.
        for tape_path in (K.F_CORE + '/Props/BP_KL_Prop_TapeDeck',
                          K.F_CORE + '/PropsArt/BP_KL_Prop_ART_TapeDeck'):
            if not unreal.EditorAssetLibrary.does_asset_exist(tape_path):
                continue
            actor = kb.n('Actor|GetActorOfClass')
            kb.setv(actor, 'ActorClass', K.cls_path(tape_path))
            en = cont(kb, en, actor)
            tape_valid = kb.c(K.F_ISVALID)
            kb.link(actor, 'ReturnValue', tape_valid, 'Object')

            def sync_tape(en2, actor=actor):
                tape_comp = comp_of_ref(kb, (actor, 'ReturnValue'), INT)
                tm = callbp(kb, INT, 'SetFilterMode')
                kb.link(tape_comp[0], tape_comp[1], tm, 'self')
                BPT.connect_pins(kb.out(nf[0], nf[1]).pin_id,
                                 kb.inp(tm, 'bOn').pin_id)
                return cont(kb, en2, tm)

            en = iff(kb, en, lambda v=tape_valid: (v, 'ReturnValue'),
                then_fn=sync_tape)
        return cont(kb, en, kb.print('KL: NGHE LOC toggled'))

    def do_interact(en):
        def do_it(en2):
            n = callbp(kb, INT, 'DoInteract')
            f2 = vref(kb, 'FocusCand')
            kb.link(f2[0], f2[1], n, 'self')
            return cont(kb, en2, n)
        iff(kb, en, lambda: jopen, else_fn=lambda x: iff(
            kb, x, lambda: fcond, then_fn=do_it))
        return en

    def journal(en):
        n = callbp(kb, INV, 'ToggleJournal')
        c = self_comp(kb, INV)
        kb.link(c[0], c[1], n, 'self')
        return cont(kb, en, n)

    def torch(en):
        on = notb(kb, bv(kb, 'TorchOn'))
        ts = kb.s('TorchOn')
        kb.link(en[0], en[1], ts, 'execute')
        kb.link(on[0], on[1], ts, 'TorchOn')
        light = self_comp(kb, 'SpotLightComponent')
        hide = notb(kb, on)
        h = kb.n(K.F_SET_HIDDEN)
        kb.link(light[0], light[1], h, 'self')
        kb.link(hide[0], hide[1], h, 'NewHidden')
        kb.setv(h, 'bPropagateToChildren', 'true')
        return cont(kb, (ts, 'then'), h)

    def restart(en):
        def do_restart(en2):
            n = kb.n('Game|OpenLevel(byName)')
            kb.setv(n, 'LevelName', K.MAP_NAME)
            return cont(kb, en2, n)
        iff(kb, en, lambda: ended, then_fn=do_restart)
        return en

    def quit_game(en):
        def do_quit(en2):
            return cont(kb, en2, kb.n('Game|QuitGame'))
        iff(kb, en, lambda: ended, then_fn=do_quit)
        return en

    e = iff(kb, e, lambda: kq, then_fn=toggle_filter,
        else_fn=lambda x: iff(
            kb, x, lambda: ke, then_fn=do_interact,
            else_fn=lambda y: iff(
                kb, y, lambda: ktab, then_fn=journal,
                else_fn=lambda z: iff(
                    kb, z, lambda: kf, then_fn=torch, else_fn=restart))))
    iff(kb, e, lambda: kesc, then_fn=quit_game)
    kb.ret()
    kb.compile(bp, 'PollKeys')

    # ---- CheckHeard: kept as a harmless compatibility function.  The tape
    #      component now owns completion via CompleteClearTape. -------------- #
    gk, kb, e = newfn(bp, 'CheckHeard')
    kb.ret()
    kb.compile(bp, 'CheckHeard')

    # ---- TickKL --------------------------------------------------------------- #
    gk, kb, e = newfn(bp, 'TickKL')
    e = cont(kb, e, me(kb, 'UpdateFocus'))
    e = cont(kb, e, me(kb, 'PollKeys'))
    kb.ret()
    kb.compile(bp, 'TickKL')

    # ---- event graph ------------------------------------------------------------ #
    beg = b.ev('BeginPlay')
    tick = b.ev('Tick')
    b.link(beg, 'then', me(b, 'InitKL'), 'execute')
    b.link(tick, 'then', me(b, 'TickKL'), 'execute')
    # clear() preserved EnhancedInput events but removed their handlers.
    # Reconnect them to the template's still-present movement/aim functions.
    for node in list(b.ed.list_all_nodes()):
        title = node.get_node_title()
        if not title.startswith('EnhancedInputAction '):
            continue
        if title.endswith('IA_Move'):
            target = me(b, 'Move')
            b.link(node, 'Triggered', target, 'execute')
            b.link(node, 'ActionValue_X', target, 'Left / Right')
            b.link(node, 'ActionValue_Y', target, 'Forward / Backward')
        elif title.endswith(('IA_Look', 'IA_MouseLook')):
            target = me(b, 'Aim')
            b.link(node, 'Triggered', target, 'execute')
            b.link(node, 'ActionValue_X', target, 'Yaw')
            b.link(node, 'ActionValue_Y', target, 'Pitch')
        elif title.endswith('IA_Jump'):
            jump = b.c('/Script/Engine.Character:Jump')
            stop = b.c('/Script/Engine.Character:StopJumping')
            b.link(node, 'Started', jump, 'execute')
            b.link(node, 'Completed', stop, 'execute')
    b.compile(bp, '(event graph)')

    K.save(CHAR)
    return path


def bp_self_name(bp):
    return '%s.%s_C' % (bp.get_path_name(), bp.get_name())


# --------------------------------------------------------------------------- #
# 5. HUD
# --------------------------------------------------------------------------- #

CREAM = (0.92, 0.90, 0.82)
ACCENT = (0.72, 0.92, 0.78)
WARM = (0.98, 0.74, 0.50)
DIM = (0.58, 0.60, 0.58)
WHITE = (1.0, 1.0, 1.0)
PANEL = (0.015, 0.018, 0.022, 0.90)
BAR = (0.30, 0.52, 0.36, 1.0)

JOURNAL_TITLE = 'SỔ TAY KHẢI  -  Trường tiểu học số 3'
JOURNAL_CLOSE = '[Tab] đóng sổ tay'
CORROB_HEADER = 'ĐỐI CHỨNG HAI NGUỒN ĐỘC LẬP'


def build_hud(asset_name='BP_KL_HUD'):
    step(asset_name)
    bp, path = K.new_bp(K.F_UI, asset_name, 'HUD')
    g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    b = K.B(g, 'HUD.EventGraph')
    b.clear(keep_prefixes=())
    ev = b.n('AddEvent|EventReceiveDrawHUD')
    if ev is None:
        fail('HUD: AddEvent|EventReceiveDrawHUD unavailable - no overlay will draw')
        return None
    ok('HUD draw event: pins IN %s OUT %s' % (
        [x.name for x in b.info(ev).input_pins],
        [x.name for x in b.info(ev).output_pins]))

    def pixel(value, size_pin):
        multiply = b.c('/Script/Engine.KismetMathLibrary:Multiply_DoubleDouble')
        b.link(ev, size_pin, multiply, 'A')
        b.setv(multiply, 'B', value)
        return multiply

    def text(en, value, x, y, scale, rgb):
        n = b.n('HUD|DrawText')
        b.link(en[0], en[1], n, 'execute')
        if isinstance(value, str):
            b.setv(n, 'Text', value)
        else:
            b.link(value[0], kb_out(b, value), n, 'Text')
        b.link(pixel(x, 'SizeX'), 'ReturnValue', n, 'ScreenX')
        b.link(pixel(y, 'SizeY'), 'ReturnValue', n, 'ScreenY')
        b.setv(n, 'Scale', scale)
        b.setv(n, 'bScalePosition', 'false')
        b.setv(n, 'Font', K.FONT + '.Roboto')
        col = color(b, *rgb)
        b.link(col[0], col[1], n, 'TextColor')
        return (n, 'then')

    def rect(en, rgb, x, y, w, h):
        n = b.n('HUD|DrawRect')
        b.link(en[0], en[1], n, 'execute')
        for pin, value, size in (('ScreenX', x, 'SizeX'), ('ScreenY', y, 'SizeY'),
                                 ('ScreenW', w, 'SizeX'), ('ScreenH', h, 'SizeY')):
            b.link(pixel(value, size), 'ReturnValue', n, pin)
        col = color(b, *rgb)
        b.link(col[0], col[1], n, 'RectColor')
        return (n, 'then')

    pawn = player_pawn(b)
    inv_c = comp_of_ref(b, pawn, INV)
    lis_c = comp_of_ref(b, pawn, LIS)

    def inv_str(fname):
        n = callbp(b, INV, fname)
        b.link(inv_c[0], inv_c[1], n, 'self')
        return (n, 'ReturnValue')

    def inv_bool(fname):
        n = callbp(b, INV, fname)
        b.link(inv_c[0], inv_c[1], n, 'self')
        return (n, 'ReturnValue')

    def lis_str(fname):
        n = callbp(b, LIS, fname)
        b.link(lis_c[0], lis_c[1], n, 'self')
        return (n, 'ReturnValue')

    e = (ev, 'then')
    e = text(e, inv_str('GetObjectiveStr'), '0.025', '0.030', '0.85', CREAM)
    e = text(e, lis_str('GetModeStr'), '0.820', '0.030', '0.85', ACCENT)
    e = text(e, '+', '0.4965', '0.4620', '0.9', WHITE)
    e = text(e, inv_str('GetPromptStr'), '0.300', '0.610', '1.0', ACCENT)
    e = text(e, inv_str('GetSubtitleStr'), '0.060', '0.800', '0.85', CREAM)
    e = text(e, CONTROLS, '0.025', '0.930', '0.72', DIM)

    # ---- journal ---------------------------------------------------------- #
    jopen = inv_bool('GetJournalOpen')

    def journal(en):
        en = rect(en, PANEL, '0.05', '0.09', '0.90', '0.82')
        en = rect(en, BAR, '0.05', '0.09', '0.90', '0.004')
        en = text(en, JOURNAL_TITLE, '0.07', '0.120', '1.0', ACCENT)

        def doc(en2):
            en2 = text(en2, inv_str('GetDocTitleStr'), '0.07', '0.170', '0.9', ACCENT)
            en2 = text(en2, inv_str('GetDocSourceStr'), '0.07', '0.205', '0.75', DIM)
            y = 0.245
            for i in range(1, 5):
                en2 = text(en2, inv_str('GetDocBody%dStr' % i), '0.07',
                           '%.3f' % y, '0.8', CREAM)
                y += 0.025
            for i in range(1, 3):
                en2 = text(en2, inv_str('GetDocClue%dStr' % i), '0.07',
                           '%.3f' % y, '0.8', WARM)
                y += 0.025
            return en2

        def tape(en2):
            en2 = text(en2, inv_str('GetTapeTitleStr'), '0.07', '0.440', '0.9', ACCENT)
            en2 = text(en2, inv_str('GetTapeSourceStr'), '0.07', '0.475', '0.75', DIM)
            y = 0.515
            for i in range(1, 5):
                en2 = text(en2, inv_str('GetTapeBody%dStr' % i), '0.07',
                           '%.3f' % y, '0.8', CREAM)
                y += 0.025
            for i in range(1, 4):
                en2 = text(en2, inv_str('GetTapeClue%dStr' % i), '0.07',
                           '%.3f' % y, '0.8', WARM)
                y += 0.025
            return en2

        en2 = iff(b, en, lambda: inv_bool('GetHasDoc'), then_fn=doc)
        en2 = iff(b, en2, lambda: inv_bool('GetHasTape'), then_fn=tape)

        def corrob(en3):
            en3 = text(en3, CORROB_HEADER, '0.07', '0.700', '0.9', ACCENT)
            y = 0.730
            for i in range(1, 7):
                en3 = text(en3, inv_str('GetCorrob%dStr' % i), '0.07',
                           '%.3f' % y, '0.8', WARM)
                y += 0.025
            return en3

        en2 = iff(b, en2, lambda: inv_bool('GetCorroborated'), then_fn=corrob)
        return text(en2, JOURNAL_CLOSE, '0.07', '0.875', '0.8', DIM)

    e = iff(b, e, lambda: jopen, then_fn=journal)

    # ---- ending ----------------------------------------------------------- #
    def ending(en):
        en = rect(en, (0.01, 0.01, 0.012, 0.94), '0.0', '0.0', '1.0', '1.0')
        en = text(en, inv_str('GetEndTitleStr'), '0.12', '0.330', '1.0', ACCENT)
        y = 0.390
        for i in range(1, 5):
            en = text(en, inv_str('GetEndLine%dStr' % i), '0.12',
                      '%.3f' % y, '0.9', CREAM)
            y += 0.040
        return text(en, inv_str('GetHintEndStr'), '0.12', '0.560', '0.9', WARM)

    iff(b, e, lambda: inv_bool('GetEnded'), then_fn=ending)

    b.compile(bp, '(event graph)')
    missing_targets = []
    for node in unreal.BlueprintGraphEditor.get_graph_editor(g).list_all_nodes():
        for pin in BPT.get_node_infos([node])[0].input_pins:
            if (pin.name == 'self' and
                    ('BP KL Investigation Component' in str(pin.type_id) or
                     'BP KL Listening Component' in str(pin.type_id)) and
                    not pin.connected_pins):
                missing_targets.append(node.get_node_title())
    if missing_targets:
        fail('%s has %d unconnected component targets: %s' % (
            asset_name, len(missing_targets), missing_targets[:5]))
        return None
    K.save(path)
    return path


def kb_out(b, ref):
    return b.out_any(ref[0]) if len(ref) == 1 else ref[1]


# --------------------------------------------------------------------------- #
# 6. game mode
# --------------------------------------------------------------------------- #

def build_gamemode():
    step('BP_KL_GameMode')
    bp, path = K.new_bp(K.F_PLAYER, 'BP_KL_GameMode', K.BP_TPL_GM)
    cdo = K.cdo(bp)
    applied = False
    for prop in ('hud_class', 'HUDClass'):
        try:
            cdo.set_editor_property(prop, K.bp_class(HUD))
            applied = True
            ok('GameMode %s = BP_KL_HUD' % prop)
            break
        except Exception:
            continue
    if not applied:
        fail('could not set HUD class on BP_KL_GameMode')
    for prop, val in (('default_pawn_class', K.bp_class(CHAR)),
                      ('player_controller_class',
                       K.bp_class(K.BP_TPL_PC))):
        try:
            cdo.set_editor_property(prop, val)
            ok('GameMode %s = %s' % (prop, val.get_name()))
        except Exception as exc:
            warn('GameMode %s: %r' % (prop, exc))
    BPT.compile_blueprint(bp)
    K.save(path)
    return path


# --------------------------------------------------------------------------- #

def main():
    K.make_folders()
    build_investigation()
    build_listening()
    build_interact()
    build_character()
    build_hud()
    build_gamemode()


if __name__ == '__main__':
    K.run(main)
