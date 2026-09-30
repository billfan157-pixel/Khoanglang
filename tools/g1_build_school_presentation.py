"""Build only isolated G1 player, HUD and game mode; preserve existing assets."""
import json
import array
import hashlib
import math
from pathlib import Path
import sys
import wave
import unreal

ROOT = Path(unreal.Paths.project_dir())
sys.path.insert(0, str(ROOT / 'Content/Python/KhoangLang'))
import kl_core as K
import build_20_blueprints as B

BASE = '/Game/KhoangLang/Production/G1Canon'
LOOP = BASE + '/BP_KL_SchoolLoop'
CHAR = BASE + '/BP_KL_SchoolCharacter'
HUD = BASE + '/BP_KL_SchoolHUD'
GM = BASE + '/BP_KL_SchoolGameMode'


def require_saved(bp, path):
    B.BPT.compile_blueprint(bp, warnings_as_errors=False)
    if bp.get_editor_property('status') == unreal.BlueprintStatus.BS_ERROR:
        raise RuntimeError('Compile failed: ' + path)
    if not K.save(path):
        raise RuntimeError('Save failed: ' + path)


def build_player():
    if not unreal.EditorAssetLibrary.does_asset_exist(CHAR):
        bp = unreal.EditorAssetLibrary.duplicate_asset(
            '/Game/KhoangLang/Production/Blueprints/Player/BP_KL_Character', CHAR)
        if bp is None:
            raise RuntimeError('Player copy failed')
    else:
        bp = unreal.load_asset(CHAR)
    # Preserve template Enhanced Input movement/aim; the school actor owns
    # investigation input. Disable old objective initialization and focus.
    for name in ('InitKL', 'UpdateFocus', 'CheckHeard'):
        g, b, e = B.newfn(bp, name)
        b.ret()
        b.compile(bp, name)
    g, b, e = B.newfn(bp, 'PollKeys')
    pc = B.player_ctrl(b)
    pressed = B.key_pressed(b, 'F', pc)

    def torch(en):
        enabled = B.notb(b, B.bv(b, 'TorchOn'))
        store = b.s('TorchOn')
        b.link(enabled[0], enabled[1], store, 'TorchOn')
        en = B.cont(b, en, store)
        lamp = B.self_comp(b, 'SpotLightComponent')
        hide = B.notb(b, B.bv(b, 'TorchOn'))
        node = b.n(K.F_SET_HIDDEN)
        b.link(lamp[0], lamp[1], node, 'self')
        b.link(hide[0], hide[1], node, 'NewHidden')
        b.setv(node, 'bPropagateToChildren', 'true')
        return B.cont(b, en, node)

    B.iff(b, e, lambda: pressed, then_fn=torch)
    b.ret()
    b.compile(bp, 'G1 torch input')
    K.set_cdo(bp, 'TorchOn', True)
    light = K.find_comp_of(bp, 'SpotLightComponent')
    if light:
        light.set_editor_property('hidden_in_game', False)
    require_saved(bp, CHAR)


def build_hud():
    source_audio=ROOT/'Content/KhoangLang/SourceAudio/S_KL_RollCall.wav'
    with wave.open(str(source_audio),'rb') as source:
        if source.getsampwidth()!=2:
            raise RuntimeError('Waveform display requires verified 16-bit PCM')
        pcm=array.array('h',source.readframes(source.getnframes()))
    envelope=[]
    for index in range(32):
        samples=pcm[len(pcm)*index//32:len(pcm)*(index+1)//32]
        envelope.append(math.sqrt(sum(float(v)*v for v in samples)/max(1,len(samples)))/32768)
    peak=max(envelope) or 1
    envelope=[v/peak for v in envelope]
    (ROOT/'docs/agent/EVIDENCE/G1_waveform_source.json').write_text(json.dumps({
        'source':'Content/KhoangLang/SourceAudio/S_KL_RollCall.wav',
        'sha256':hashlib.sha256(source_audio.read_bytes()).hexdigest(),
        'method':'32 equal-duration unweighted PCM RMS bins, normalized to peak bin',
        'scope':'Stored source envelope plus scene playback clock; not live microphone or in-game mix',
        'normalized_rms':envelope},indent=2),encoding='utf-8')
    bp, path = K.new_bp(BASE, 'BP_KL_SchoolHUD', 'HUD')
    graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    b = K.B(graph, 'G1 School HUD')
    b.clear(keep_prefixes=())
    event = b.n('AddEvent|EventReceiveDrawHUD')
    # Connected double literals avoid integer promotion of screen fractions.
    def scalar(value):
        node = b.c('/Script/Engine.KismetSystemLibrary:MakeLiteralDouble')
        b.setv(node, 'Value', str(value))
        return node

    def size(fraction, axis):
        node = b.c('/Script/Engine.KismetMathLibrary:Multiply_DoubleDouble')
        b.link(event, axis, node, 'A')
        b.link(scalar(fraction), 'ReturnValue', node, 'B')
        return node

    def scale(base):
        return size(base / 720.0, 'SizeY')

    def rect(en, rgba, x, y, w, h):
        node = b.n('HUD|DrawRect')
        for pin, fraction, axis in (('ScreenX', x, 'SizeX'),
                ('ScreenY', y, 'SizeY'), ('ScreenW', w, 'SizeX'),
                ('ScreenH', h, 'SizeY')):
            b.link(size(fraction, axis), 'ReturnValue', node, pin)
        col = B.color(b, *rgba)
        b.link(col[0], col[1], node, 'RectColor')
        return B.cont(b, en, node)

    def text(en, value, x, y, base=1.4, rgb=(.92, .90, .82)):
        node = b.n('HUD|DrawText')
        if isinstance(value, str):
            b.setv(node, 'Text', value)
        else:
            b.link(value[0], value[1], node, 'Text')
        b.link(size(x, 'SizeX'), 'ReturnValue', node, 'ScreenX')
        b.link(size(y, 'SizeY'), 'ReturnValue', node, 'ScreenY')
        b.link(scale(base), 'ReturnValue', node, 'Scale')
        b.setv(node, 'bScalePosition', 'false')
        b.setv(node, 'Font', K.FONT + '.Roboto')
        col = B.color(b, *rgb)
        b.link(col[0], col[1], node, 'TextColor')
        return B.cont(b, en, node)

    actor = b.n('Actor|GetActorOfClass')
    b.setv(actor, 'ActorClass', K.cls_path(LOOP))
    e = B.cont(b, (event, 'then'), actor)
    is_valid = b.c(K.F_ISVALID)
    b.link(actor, 'ReturnValue', is_valid, 'Object')

    def query(name):
        node = B.callbp(b, LOOP, name)
        b.link(actor, 'ReturnValue', node, 'self')
        return (node, 'ReturnValue')

    def draw(en):
        en = rect(en, (.008, .012, .016, .80), .02, .02, .96, .105)
        en = text(en, query('GetHeader'), .035, .033, 1.5)
        en = text(en, query('GetStatus'), .035, .078, 1.25, (.72,.86,.81))
        en = text(en, '+', .494, .485, 1.15)
        # Time progress and marked interruptions in the current roll-call
        # display are captions, not a claim of measured audio waveform data.
        en = rect(en, (.04,.06,.065,.88), .035,.77,.32,.016)
        phase = query('GetWavePhase')
        marker = b.c('/Script/Engine.KismetMathLibrary:Multiply_DoubleDouble')
        b.link(phase[0],phase[1],marker,'A')
        b.link(size(.32,'SizeX'),'ReturnValue',marker,'B')
        line = b.n('HUD|DrawRect')
        for pin,value,axis in (('ScreenX',.035,'SizeX'),('ScreenY',.77,'SizeY'),('ScreenH',.016,'SizeY')):
            b.link(size(value,axis),'ReturnValue',line,pin)
        b.link(marker,'ReturnValue',line,'ScreenW')
        col=B.color(b,.42,.68,.63,1)
        b.link(col[0],col[1],line,'RectColor')
        en=B.cont(b,en,line)
        for index,amplitude in enumerate(envelope):
            height=.027*amplitude+.002
            en=rect(en,(.60,.80,.74,.95),.035+index*.010,.778-height/2,.004,height)
        # The two blank roll-call positions are explicitly authored cut marks.
        for x in (.327,.344):
            en=rect(en,(.87,.65,.40,1),x,.759,.002,.038)
        en = rect(en, (.008,.012,.016,.88), .035,.80,.93,.085)
        en = text(en, query('GetPrompt'), .05,.806,1.45,(.77,.90,.84))
        en = text(en, query('GetCaption'), .05,.847,1.5)
        en = text(en, 'WASD đi · Chuột nhìn · E tương tác · Q đổi kênh · F đèn pin',
                  .035,.899,1.3)
        en = text(en, query('GetFooter'), .035,.933,1.3,(.77,.80,.78))
        en = text(en, query('GetFooter2'), .035,.967,1.3,(.77,.80,.78))

        def dossier(show):
            show=rect(show,(.012,.018,.023,.96),.07,.17,.86,.57)
            show=text(show,'SỔ ĐỐI CHỨNG',.09,.194,1.55,(.74,.88,.82))
            for index in range(1,9):
                show=text(show,query('GetBody%d'%index),.09,.248+(index-1)*.055,1.35)
            return show
        return B.iff(b,en,lambda:query('GetDossierOpen'),then_fn=dossier)

    B.iff(b,e,lambda:(is_valid,'ReturnValue'),then_fn=draw)
    b.compile(bp,'responsive G1 display')
    if K.FAILS:
        raise RuntimeError(str(K.FAILS))
    require_saved(bp,path)


def main():
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
        raise RuntimeError('Stop PIE before building')
    if not unreal.EditorAssetLibrary.does_asset_exist(LOOP):
        raise RuntimeError('Build G1 school loop first')
    unreal.EditorAssetLibrary.make_directory(BASE)
    if not globals().get('G1_HUD_ONLY', False):
        build_player()
    build_hud()
    if globals().get('G1_HUD_ONLY', False):
        print('G1_HUD_ONLY_SAVED')
        return
    bp,path=K.new_bp(BASE,'BP_KL_SchoolGameMode',K.BP_TPL_GM)
    defaults=K.cdo(bp)
    defaults.set_editor_property('default_pawn_class',K.bp_class(CHAR))
    defaults.set_editor_property('hud_class',K.bp_class(HUD))
    defaults.set_editor_property('player_controller_class',K.bp_class(K.BP_TPL_PC))
    require_saved(bp,path)
    if K.FAILS:
        raise RuntimeError(str(K.FAILS))
    report={p:str(unreal.load_asset(p).get_editor_property('status')) for p in (CHAR,HUD,GM)}
    (ROOT/'docs/agent/EVIDENCE/G1_canonical_presentation_build.json').write_text(
        json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))

if __name__=='__main__':
    main()
