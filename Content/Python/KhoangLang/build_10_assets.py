"""Khoan Lang 02:17 - Milestone 1, pass 1: audio flags, materials, evidence data.

Evidence copy is stored as fixed numbered lines (Body1..4, Clue1..2) rather than
one multi-line blob: the Milestone 1 HUD draws text one canvas row at a time and
does not implement text wrapping yet.  See docs/tech/MILESTONE1_NOTES.md.

Run headless:  run_ue_script.ps1 build_10_assets.py
"""

import os
import sys

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import kl_core as K  # noqa: E402
from kl_core import BP, BPT, ContainerType  # noqa: E402
from kl_core import step, ok, warn, fail  # noqa: E402

SRC_AUDIO = os.path.join(unreal.Paths.project_dir(), 'Content', 'KhoangLang',
                         'SourceAudio')

LOOPING = ('S_KL_Ambience_Hall', 'S_KL_NoiseMask', 'S_KL_ClarityTone',
           'S_KL_SpeakerHum')

# --------------------------------------------------------------------------- #
# player-facing copy - canon wording, V3 story bible sections 3 / 4 / 6
# --------------------------------------------------------------------------- #

EVIDENCE_DEFS = [
    dict(
        name='EVD_SoDiemDanh',
        eid='EVD_DOC_ROLLCALL',
        title='Sổ điểm danh tập kết - đêm 21/9/2002',
        source='Nguồn: sổ tay cô Vân, GV Trường tiểu học số 3. Còn nằm trên bàn giáo viên, phòng học 3.',
        body=['Sổ bìa cứng, mép còn dính nước. Cô Vân ghi tên lần lượt từ 00:30',
              'đến 01:30 sáng, lúc dân kéo nhau tới trường tập kết.',
              'Cuối trang, bút chì nhạt hơn phần còn lại: "63 + 2".',
              'Hai dòng cuối không có tên, chỉ có dấu chấm, cạnh chữ "ghi sau".'],
        clue=['63 là số tên cô Vân kịp ghi trong đoàn mình. Hai người đi cuối',
              'hàng không có tên trong sổ nào. Tổng 65. Sổ đếm NGƯỜI ĐẾM ĐƯỢC,',
              'không đếm người đã trả lời.'],
        is_doc=True, is_aud=False, related=('EVD_TAPE_0216',),
    ),
    dict(
        name='EVD_Bang021634',
        eid='EVD_TAPE_0216',
        title='Băng thu 02:16:34 (bản phát)',
        source='Nguồn: đầu băng nối vào loa hành lang Trường tiểu học số 3, tuyến loa Trường học.',
        body=['Giọng tổng đài đọc: "Kiểm tra lần cuối. Những người còn ở lại,',
              'xin hãy lên tiếng."',
              'Sau đó là một khối tiếng. Ở NGHE THƯỜNG chỉ còn lớp nhiễu, không ngõi gì.',
              'Ở NGHE LỌC, các câu tách ra: "Còn! Còn ở đây!".'],
        clue=['Bản phát không bị xóa. 65 câu trả lời vẫn còn, bị chôn dưới lớp nhiễu.',
              'Hai giọng nhỏ nhất nằm sát đáy băng. Một giọng trẻ con bị cắt cụt:',
              '"Còn! Còn em ở..."  Nghe hết câu chưa đủ, phải đối chứng nguồn độc lập.'],
        is_doc=False, is_aud=True, related=('EVD_DOC_ROLLCALL',),
    ),
]

EVIDENCE_FIELDS = ('Title', 'SourceText',
                  'Body1', 'Body2', 'Body3', 'Body4',
                  'Clue1', 'Clue2', 'Clue3')

# --------------------------------------------------------------------------- #
# 1. audio
# --------------------------------------------------------------------------- #

def check_audio():
    step('audio assets')
    if not os.path.isdir(SRC_AUDIO):
        fail('missing source audio dir: %s' % SRC_AUDIO)
        return
    at = unreal.AssetToolsHelpers.get_asset_tools()
    K.eas().make_directory(K.F_AUDIO)
    wavs = sorted(f for f in os.listdir(SRC_AUDIO) if f.lower().endswith('.wav'))
    for fn in wavs:
        name = os.path.splitext(fn)[0]
        if unreal.load_asset('%s/%s' % (K.F_AUDIO, name)) is not None:
            continue
        task = unreal.AssetImportTask()
        task.set_editor_property('filename', os.path.join(SRC_AUDIO, fn))
        task.set_editor_property('destination_path', K.F_AUDIO)
        task.set_editor_property('destination_name', name)
        task.set_editor_property('automated', True)
        task.set_editor_property('save', True)
        task.set_editor_property('replace_existing', True)
        at.import_asset_tasks([task])
    for fn in wavs:
        name = os.path.splitext(fn)[0]
        a = K.load('%s/%s' % (K.F_AUDIO, name))
        want_loop = name in LOOPING
        for prop in ('looping', 'bLooping'):
            try:
                if bool(a.get_editor_property(prop)) != want_loop:
                    a.set_editor_property(prop, want_loop)
            except Exception:
                pass
        ok('%-22s loop=%-5s dur=%.1fs' % (name, want_loop, a.get_editor_property('duration')))


# --------------------------------------------------------------------------- #
# 2. materials
# --------------------------------------------------------------------------- #

MATERIALS = [
    ('M_KL_WallUpper', (0.60, 0.58, 0.48), 'tuong hoc tro'),
    ('M_KL_Wainscot', (0.20, 0.27, 0.22), 'chan tuong truong hoc xanh'),
    ('M_KL_Floor', (0.21, 0.20, 0.19), 'san betong'),
    ('M_KL_Ceiling', (0.52, 0.52, 0.49), 'tran nhua'),
    ('M_KL_Desk', (0.29, 0.18, 0.10), 'ban hoc go'),
    ('M_KL_Board', (0.03, 0.10, 0.06), 'bang den'),
    ('M_KL_Metal', (0.30, 0.31, 0.33), 'nen loa / kim loai'),
    ('M_KL_Wood', (0.25, 0.15, 0.08), 'khung cua / ban gia'),
    ('M_KL_Paper', (0.80, 0.76, 0.64), 'giay'),
    ('M_KL_Figure', (0.70, 0.72, 0.74), 'hinh dang'),
    ('M_KL_Outside', (0.09, 0.11, 0.14), 'ngoai canh dem'),
]


def make_materials():
    step('materials')
    at = unreal.AssetToolsHelpers.get_asset_tools()
    K.eas().make_directory(K.F_MAT)
    base = K.load('/Engine/BasicShapes/BasicShapeMaterial')
    mel = unreal.MaterialEditingLibrary
    out = {}
    for name, rgb, note in MATERIALS:
        path = '%s/%s' % (K.F_MAT, name)
        mi = unreal.load_asset(path)
        if mi is None:
            mi = at.create_asset(name, K.F_MAT, unreal.MaterialInstanceConstant,
                                 unreal.MaterialInstanceConstantFactoryNew())
        if mi is None:
            fail('material %s' % name)
            continue
        mi.set_editor_property('parent', base)
        mel.update_material_instance(mi)
        mel.set_material_instance_vector_parameter_value(
            mi, 'Color', unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
        out[name] = path
    ok('%d material instances in %s' % (len(out), K.F_MAT))
    return out


# --------------------------------------------------------------------------- #
# 3. evidence definition blueprint
# --------------------------------------------------------------------------- #

EVIDENCE_BP = K.F_DATA + '/BP_KL_EvidenceDef'

GETTERS = [('GetTitleStr', 'Title'), ('GetSourceStr', 'SourceText'),
           ('GetBody1Str', 'Body1'), ('GetBody2Str', 'Body2'),
           ('GetBody3Str', 'Body3'), ('GetBody4Str', 'Body4'),
           ('GetClue1Str', 'Clue1'), ('GetClue2Str', 'Clue2'),
           ('GetClue3Str', 'Clue3')]


def build_evidence_def():
    step('BP_KL_EvidenceDef')
    # rebuilt from scratch: a stale class here silently breaks every caller
    for n in ('EVD_SoDiemDanh', 'EVD_Bang021634', 'BP_KL_EvidenceDef'):
        p = '%s/%s' % (K.F_DATA, n)
        if unreal.load_asset(p) is not None:
            try:
                unreal.EditorAssetLibrary.delete_asset(p)
                ok('deleted %s (rebuild)' % p)
            except Exception as exc:
                warn('delete %s: %r' % (p, exc))
    # UDataAsset itself is not Blueprintable in this engine build, so the
    # evidence record derives from UPrimaryDataAsset (a UDataAsset subclass).
    bp, path = K.new_bp(K.F_DATA, 'BP_KL_EvidenceDef', 'PrimaryDataAsset')
    for v in EVIDENCE_FIELDS:
        K.var(bp, v, 'text')
    K.var(bp, 'EvidenceId', 'name')
    K.var(bp, 'IsDocument', 'bool')
    K.var(bp, 'IsAudioRecording', 'bool')
    K.var(bp, 'bDiscovered', 'bool')
    K.var_arr(bp, 'RelatedIds', 'name')

    for fname, var in GETTERS:
        g = BPT.add_function_graph(bp, fname)
        b = K.B(g, '%s.%s' % (bp.get_name(), fname))
        b.ed.set_is_pure_function(True)
        b.clear()
        try:
            b.ed.remove_graph_input_parameter(g, 'ReturnValue')
        except Exception:
            pass
        BPT.add_function_param(g, 'ReturnValue', 'string', False, None)
        gv = b.g(var)
        b.ret(b.text2str(gv, b.out_any(gv).name))
        b.compile(bp, fname)
    BPT.compile_blueprint(bp)
    ok('evidence definition: %s' % path)
    return path


def build_evidence_instances(def_path):
    step('evidence data assets')
    made = []
    for spec in EVIDENCE_DEFS:
        inst, path = K.new_data_asset(K.F_DATA, spec['name'], def_path)
        inst.set_editor_property('EvidenceId', unreal.Name(spec['eid']))
        inst.set_editor_property('Title', unreal.Text(spec['title']))
        inst.set_editor_property('SourceText', unreal.Text(spec['source']))
        for i, line in enumerate(spec['body']):
            inst.set_editor_property('Body%d' % (i + 1), unreal.Text(line))
        for i in range(3):
            line = spec['clue'][i] if i < len(spec['clue']) else ''
            inst.set_editor_property('Clue%d' % (i + 1), unreal.Text(line))
        inst.set_editor_property('IsDocument', spec['is_doc'])
        inst.set_editor_property('IsAudioRecording', spec['is_aud'])
        inst.set_editor_property('bDiscovered', False)
        inst.set_editor_property('RelatedIds', [unreal.Name(r) for r in spec['related']])
        made.append(path)
        ok('%s  (%s)' % (path, spec['eid']))
    return made


# --------------------------------------------------------------------------- #
# 4. cleanup of discovery leftovers
# --------------------------------------------------------------------------- #

TMP_ASSETS = ['TMP14_Caller', 'TMP14_Target', 'TMP24_Target', 'TMP27_Target',
              'TMP37_X', 'TMP38_PrimaryDataAsset', 'TMP38_SaveGame']


def cleanup():
    step('cleanup discovery leftovers')
    for folder, n in ([(K.F_DATA, a) for a in TMP_ASSETS] +
                      [(K.ROOT + '/Input', 'TMP15_IA_Test')]):
        p = '%s/%s' % (folder, n)
        if unreal.load_asset(p) is not None:
            try:
                unreal.EditorAssetLibrary.delete_asset(p)
                ok('deleted %s' % p)
            except Exception as exc:
                warn('delete %s: %r' % (p, exc))


# --------------------------------------------------------------------------- #

def main():
    K.make_folders()
    check_audio()
    make_materials()
    def_path = build_evidence_def()
    build_evidence_instances(def_path)
    cleanup()
    K.save(K.ROOT)


K.run(main)
