"""Khoang Lang 02:17 - Milestone 1, pass 1: content + Blueprints.

Run with:
  UnrealEditor-Cmd.exe <project> -run=pythonscript -script=<this file> -unattended -nullrhi
"""

import os
import sys
import traceback

import unreal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else '')
sys.path.insert(0, r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang')

import kl_kit as K  # noqa: E402
from kl_kit import (BP, ACT, ROOT, F_AUDIO, F_MAT, F_DATA, F_CORE, F_UI,  # noqa: E402
                    T, V, bpfn, getv, setv, log, step, done, load, find_type,
                    new_bp, event_graph, fn_graph, set_cdo, make_cdo_text,
                    make_cdo_bool, make_cdo_float, make_cdo_color, make_cdo_object,
                    compile_bp, instance_editable)

from editor_toolset.toolsets.blueprint import ContainerType  # noqa: E402

PROJECT = unreal.Paths.project_dir()
SRC_AUDIO = PROJECT + 'Content' + '/' + 'KhoangLang' + '/' + 'SourceAudio'
REPORT_PATH = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\build_assets.txt'

# --------------------------------------------------------------------------- #
# Player-facing copy (Vietnamese, canon wording)
# --------------------------------------------------------------------------- #

OBJECTIVE_START = 'Mục tiêu: vào Trường tiểu học số 3, tìm sổ điểm danh đêm 21/9/2002.'
OBJECTIVE_TAPE = 'Có tiếng loa ở hành lang. Bấm [Q] để bật NGHE LỌC, nghe lại đoạn băng.'
OBJECTIVE_CORROBORATE = 'Đối chứng: 65 giọng trả lời với 63 tên trong sổ. Mở sổ tay [Tab].'
OBJECTIVE_RETURN = 'Sự thống nhất đã rõ. Quay lại phòng học 3 và bật NGHE LỌC.'
OBJECTIVE_REVEAL = 'Có thứ gì đó trong lớp. Giữ NGHE LỌC và nhìn vào góc cuối.'
OBJECTIVE_END = 'Tiếp tục giữ nguyên ký ức, hoặc làm nó sai đi. (Hết phần thử nghiệm.)'

SUB_LISTEN_ON = 'NGHE LỌC: lớp nhiễu bị bóp nghẹt, các giọng dưới đáy băng tách ra.'
SUB_LISTEN_OFF = 'NGHE THƯỜNG: âm thanh đi qua lớp vữa và tiếng mưa, không ngõi được gì.'

EVD_DOC_TITLE = 'Sổ điểm danh tập kết - 21/9/2002'
EVD_DOC_SOURCE = 'Nguồn: quần thầm cô Vân, phòng học 3, Trường tiểu học số 3.'
EVD_DOC_BODY = (
    'Sổ bìa cứng, bìa còn dính nước. Cô Vân ghi tên lần lượt lúc 00:30-01:30 đêm lũ.\n'
    'Cuối trang, bút chì nhạt hơn: "63 + 2".\n'
    'Hai dòng cuối không có tên, chỉ có dấu chấm, và bên cạnh chữ "ghi sau".\n'
    'Không có dòng nào ghi "đã ra khỏi hầm".'
)
EVD_DOC_CLUE = (
    '63 tên có thực, cộng 2 người đi cuối hàng không tên. Tổng 65.\n'
    'Sổ này đếm NGƯỜI ĐẾM ĐƯỢC, không đếm người đã trả lời.'
)

EVD_TAPE_TITLE = 'Băng thu 02:16:34 (bản phát)'
EVD_TAPE_SOURCE = 'Nguồn: thu từ loa hành lang Trường tiểu học số 3, tuyến loa Trường học.'
EVD_TAPE_BODY = (
    'Giọng tổng đài đọc: "Kiểm tra lần cuối. Những người còn ở lại, xin hãy lên tiếng."\n'
    'Sau đó là một khối tiếng. Ở chế độ NGHE THƯỜNG chỉ còn một lớp nhiễu.\n'
    'Ở chế độ NGHE LỌC, các câu trả lời tách ra: "Còn! Còn ở đây!".\n'
    'Hai giọng nhỏ nhất nằm sát đáy băng, gần như không ai nghe thấy.\n'
    'Một giọng trẻ con bị cắt cụt: "Còn! Còn em ở..."'
)
EVD_TAPE_CLUE = (
    'Bản phát không bị xóa. 65 câu trả lời vẫn còn, bị chôn dưới lớp nhiễu.\n'
    'Nghe hết câu chưa đủ. Phải đối chứng với một nguồn độc lập - tức là những cái tên trong sổ.'
)

CORROBORATION_LINES = [
    'ĐỐI CHỨNG - nguồn A: sổ điểm danh của cô Vân, 63 tên + 2 dòng trống chì.',
    'ĐỐI CHỨNG - nguồn B: băng 02:16:34, 65 giọng đã trả lời (đếm được sau khi lọc).',
    'Hai con số không khớp, và sự khác biệt nằm đúng bằng hai dòng trống.',
    'Bản tin chính thức ghi 63 nạn nhân. Con số đó là số người được đếm tên,',
    'không phải số người đã cất tiếng. Có hai mẹ con công nhân không có tên trong sổ nào.',
    '',
    'Luật P1: bản ghi không đồng nghĩa với sự thật. Nghe hết câu là bước một.',
    'Đối chứng nguồn độc lập mới là bước hai.',
]

ENDING_LINES = [
    'Hết thử nghiệm Milestone 1 - Trường tiểu học số 3',
    '',
    'Bạn đã nghe được thứ vốn bị chôn, đọc được thứ vốn bị bỏ trống,',
    'và đối chứng hai nguồn độc lập để thấy con số bị báo cáo sai.',
    '',
    'Phần còn lại của câu chuyện vẫn chưa được trả lời ở đây:',
    'ai được đếm, ai được nghe, và ai có quyền kể lại.',
    '',
    '[Enter] về màn hình tiêu đề    [Esc] thoát',
]

EVIDENCE_DEFS = [
    # (asset name, id, title, source, body, clue, is_doc, is_audio)
    ('EVD_SoDiemDanh', 'EVD_DOC_ROLLCALL', EVD_DOC_TITLE, EVD_DOC_SOURCE,
     EVD_DOC_BODY, EVD_DOC_CLUE, True, False),
    ('EVD_BangThu0216', 'EVD_TAPE_0216', EVD_TAPE_TITLE, EVD_TAPE_SOURCE,
     EVD_TAPE_BODY, EVD_TAPE_CLUE, False, True),
]


# --------------------------------------------------------------------------- #
# 1. audio import
# --------------------------------------------------------------------------- #

def import_audio():
    step('import placeholder audio')
    at = unreal.AssetToolsHelpers.get_asset_tools()
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.make_directory(F_AUDIO)
    if not os.path.isdir(SRC_AUDIO):
        raise RuntimeError('missing source audio dir: ' + SRC_AUDIO)
    files = sorted(f for f in os.listdir(SRC_AUDIO) if f.lower().endswith('.wav'))
    for fn in files:
        name = os.path.splitext(fn)[0]
        task = unreal.AssetImportTask()
        task.set_editor_property('filename', os.path.join(SRC_AUDIO, fn))
        task.set_editor_property('destination_path', F_AUDIO)
        task.set_editor_property('destination_name', name)
        task.set_editor_property('automated', True)
        task.set_editor_property('save', True)
        task.set_editor_property('replace_existing', True)
        at.import_asset_tasks([task])
    names = []
    for fn in files:
        name = os.path.splitext(fn)[0]
        a = unreal.load_asset('%s/%s' % (F_AUDIO, name))
        if a is None:
            raise RuntimeError('audio import failed: ' + name)
        # loop the beds so they can be played indefinitely
        if name in ('S_KL_Ambience_Hall', 'S_KL_NoiseMask', 'S_KL_ClarityTone', 'S_KL_SpeakerHum'):
            try:
                a.set_editor_property('looping', True)
            except Exception:
                pass
        try:
            a.set_editor_property('bLooping', True)
        except Exception:
            pass
        names.append(name)
    done('imported %d sound waves: %s' % (len(names), ', '.join(names)))
    return names


# --------------------------------------------------------------------------- #
# 2. materials
# --------------------------------------------------------------------------- #

def import_materials():
    step('create material instances')
    at = unreal.AssetToolsHelpers.get_asset_tools()
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.make_directory(F_MAT)
    base = load('/Engine/BasicShapes/BasicShapeMaterial')
    mel = unreal.MaterialEditingLibrary
    specs = [
        ('M_KL_Wall',    (0.34, 0.36, 0.31), 'tuong hoc tro, am mau'),
        ('M_KL_Floor',   (0.20, 0.19, 0.18), 'san betong'),
        ('M_KL_Ceil',    (0.26, 0.27, 0.25), 'tran nhua'),
        ('M_KL_Desk',    (0.26, 0.15, 0.08), 'ban hoc go'),
        ('M_KL_Board',   (0.03, 0.09, 0.06), 'bang den'),
        ('M_KL_Metal',   (0.30, 0.31, 0.33), 'nen/loa'),
        ('M_KL_Wood',    (0.22, 0.13, 0.07), 'khung cua'),
        ('M_KL_Paper',   (0.78, 0.74, 0.62), 'giay so'),
        ('M_KL_Figure',  (0.72, 0.74, 0.76), 'hinh dang'),
    ]
    out = {}
    for name, rgb, note in specs:
        path = '%s/%s' % (F_MAT, name)
        mi = unreal.load_asset(path)
        if mi is None:
            mi = at.create_asset(name, F_MAT, unreal.MaterialInstanceConstant,
                                 unreal.MaterialInstanceConstantFactoryNew())
        mi.set_editor_property('parent', base)
        mel.update_material_instance(mi)
        mel.set_material_instance_vector_parameter_value(
            mi, 'Color', unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
        out[name] = path
    done('materials: %s' % ', '.join(sorted(out)))
    return out


# --------------------------------------------------------------------------- #
# 3. data assets
# --------------------------------------------------------------------------- #

def build_evidence_def():
    step('BP_KL_EvidenceDef (data-driven evidence record)')
    bp = new_bp(F_DATA, 'BP_KL_EvidenceDef', unreal.DataAsset)
    T_ = BP.BlueprintTools
    T_.add_variable(bp, 'EvidenceId', 'name')
    T_.add_variable(bp, 'Title', 'text')
    T_.add_variable(bp, 'SourceText', 'text')
    T_.add_variable(bp, 'BodyText', 'text')
    T_.add_variable(bp, 'ClueText', 'text')
    T_.add_variable(bp, 'IsDocument', 'bool')
    T_.add_variable(bp, 'IsAudioRecording', 'bool')
    T_.add_variable(bp, 'RelatedIds', 'name', None, ContainerType.ARRAY)
    T_.add_variable(bp, 'bDiscovered', 'bool')
    instance_editable(bp, ['EvidenceId', 'Title', 'SourceText', 'BodyText', 'ClueText',
                           'IsDocument', 'IsAudioRecording', 'RelatedIds'])

    g = event_graph(bp)
    K.find_type(g, 'Utilities|Text|ToText', required=False)
    code = '\n'.join([
        '(event GetId (return (Variables|Default|GetEvidenceId)))',
        '(event GetTitle (return (Variables|Default|GetTitle)))',
        '(event GetSourceText (return (Variables|Default|GetSourceText)))',
        '(event GetBodyText (return (Variables|Default|GetBodyText)))',
        '(event GetClueText (return (Variables|Default|GetClueText)))',
        '(event IsDoc (return (Variables|Default|GetIsDocument)))',
        '(event IsAud (return (Variables|Default|GetIsAudioRecording)))',
        '(event IsDiscovered (return (Variables|Default|GetbDiscovered)))',
        '(event MarkDiscovered (Variables|Default|SetbDiscovered true))',
        '(event GetRelatedIds (return (Variables|Default|GetRelatedIds)))',
    ])
    T_.write_graph_dsl(g, code)
    compile_bp(bp, '(evidence def)')
    return bp


def build_evidence_instances(da_bp):
    step('evidence data assets')
    at = unreal.AssetToolsHelpers.get_asset_tools()
    made = []
    for (name, eid, title, source, body, clue, is_doc, is_aud) in EVIDENCE_DEFS:
        path = '%s/%s' % (F_DATA, name)
        inst = unreal.load_asset(path)
        if inst is None:
            inst = at.create_asset(name, F_DATA, unreal.DataAsset,
                                   unreal.DataAssetFactory())
            inst.set_editor_property('DataAssetClass',
                                     unreal.load_class(
                                         None, '%s/BP_KL_EvidenceDef.BP_KL_EvidenceDef_C' % F_DATA))
        assert inst.get_class().get_name() == 'BP_KL_EvidenceDef', (
            '%s is not a BP_KL_EvidenceDef' % name)
        inst.set_editor_property('EvidenceId', unreal.Name(eid))
        inst.set_editor_property('Title', unreal.Text(title))
        inst.set_editor_property('SourceText', unreal.Text(source))
        inst.set_editor_property('BodyText', unreal.Text(body))
        inst.set_editor_property('ClueText', unreal.Text(clue))
        inst.set_editor_property('IsDocument', is_doc)
        inst.set_editor_property('IsAudioRecording', is_aud)
        inst.set_editor_property('bDiscovered', False)
        rel = ['EVD_TAPE_0216'] if is_doc else ['EVD_DOC_ROLLCALL']
        inst.set_editor_property('RelatedIds', [unreal.Name(r) for r in rel])
        made.append(path)
        log('   %s -> %s' % (name, path))
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.save_directory(F_DATA, only_if_is_dirty=False, recursive=True)
    done('evidence assets: %s' % ', '.join(made))
    return made


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #

def main():
    K.make_folders()
    import_audio()
    import_materials()
    da_bp = build_evidence_def()
    build_evidence_instances(da_bp)
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.save_directory(ROOT, only_if_is_dirty=False, recursive=True)
    done('pass 1 complete')
    K.write_report(REPORT_PATH)
    return True


RESULT = 'FAILED'
try:
    if os.path.exists(REPORT_PATH):
        os.remove(REPORT_PATH)
    main()
    RESULT = 'OK'
except Exception:
    K.log(traceback.format_exc())
    K.log('RESULT=FAILED')
finally:
    try:
        K.write_report(None)
    except Exception:
        pass
    unreal.log('KLBUILD_RESULT: ' + RESULT)
