"""Build a native-parent G1 player/game mode without template dependencies.

Creates only two new assets; existing copied/template assets remain intact.
Runtime is Blueprint Tick + native CharacterMovement, camera, and light.
Input polling is provisional until physical input/capture and remapping are
qualified. Run only with PIE stopped, preferably from an empty editor map.
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

BASE = '/Game/KhoangLang/Production/G1Canon'
PLAYER = BASE + '/BP_KL_SchoolPlayer'
HUD = BASE + '/BP_KL_SchoolHUD'
GAME_MODE = BASE + '/BP_KL_SchoolNativeGameMode'
REPORT = ROOT / 'docs/agent/EVIDENCE/G1_native_player_build.json'


def scalar(b, value):
    n = b.c('/Script/Engine.KismetSystemLibrary:MakeLiteralDouble')
    b.setv(n, 'Value', str(value))
    return n, 'ReturnValue'


def wire(b, ref, node, pin):
    b.link(ref[0], ref[1], node, pin)


def arithmetic(b, function, left, right):
    n = b.c('/Script/Engine.KismetMathLibrary:' + function)
    # Establish a scalar B before Unreal can promote its wildcard operator.
    wire(b, right, n, 'B')
    wire(b, left, n, 'A')
    return n, 'ReturnValue'


def finish(b, entry):
    result = b.ret()
    if b.has_in(result, 'execute'):
        b.link(entry[0], entry[1], result, 'execute')


def native_component(bp, name):
    component = K.find_comp_of(bp, name)
    if component is None:
        raise RuntimeError('Native player missing component: ' + name)
    return component


def build_player():
    bp, path = K.new_bp(BASE, 'BP_KL_SchoolPlayer', 'Character')
    # Fail instead of accidentally extending an earlier copied asset.
    # Installed EditorToolset get_parent uses the exposed native
    # Blueprint.get_blueprint_parent_class(); ParentClass is not a property.
    parent = K.BPT.get_parent(bp)
    if parent.get_path_name() != '/Script/Engine.Character':
        raise RuntimeError('SchoolPlayer must inherit native Character: ' + parent.get_path_name())
    K.var(bp, 'TorchOn', 'bool', editable=True)
    K.var(bp, 'MouseSensitivity', 'float', editable=True)
    K.var(bp, 'bInvertMouseY', 'bool', editable=True)
    K.var_obj(bp, 'NativeControllerRef', 'PlayerController')
    signatures = {
        'Move': [('LeftRight', 'float'), ('ForwardBackward', 'float')],
        'Aim': [('Yaw', 'float'), ('Pitch', 'float')],
        'InitNativePlayer': (), 'PollNativeInput': (), 'ToggleLamp': (),
    }
    for name, params in signatures.items():
        H.newfn(bp, name, params)
    K.BPT.compile_blueprint(bp)
    if bp.get_editor_property('status') == unreal.BlueprintStatus.BS_ERROR or K.FAILS:
        raise RuntimeError('Native player API declaration failed: ' + repr(K.FAILS))

    defaults = K.cdo(bp)
    for name, value in (('TorchOn', True), ('MouseSensitivity', .18),
                        ('bInvertMouseY', False),
                        ('use_controller_rotation_yaw', True),
                        ('use_controller_rotation_pitch', False),
                        ('use_controller_rotation_roll', False)):
        defaults.set_editor_property(name, value)
    capsule = native_component(bp, 'CapsuleComponent')
    capsule.set_capsule_size(30., 88., False)
    capsule.set_collision_profile_name('Pawn', False)
    capsule.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    movement = native_component(bp, 'CharacterMovementComponent')
    for name, value in (('max_walk_speed', 220.), ('max_acceleration', 1024.),
                        ('braking_deceleration_walking', 1600.),
                        ('orient_rotation_to_movement', False),
                        ('use_controller_desired_rotation', False)):
        K.comp_set(movement, name, value, 'native CharacterMovement')
    # Native Character has a mesh component but no content/animation dependency.
    mesh = K.find_comp_of(bp, 'SkeletalMeshComponent')
    if mesh is not None:
        mesh.set_skeletal_mesh_asset(None)
        mesh.set_editor_property('anim_class', None)
        mesh.set_editor_property('hidden_in_game', True)
        mesh.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    camera = K.add_comp(bp, 'CameraComponent', 'SchoolCamera', parent=capsule)
    if camera is None:
        raise RuntimeError('Could not add native camera')
    for name, value in (('relative_location', unreal.Vector(0., 0., 64.)),
                        ('relative_rotation', unreal.Rotator(0., 0., 0.)),
                        ('use_pawn_control_rotation', True), ('field_of_view', 80.)):
        K.comp_set(camera, name, value, 'native camera')
    lamp = K.add_comp(bp, 'SpotLightComponent', 'SchoolLamp', parent=camera)
    if lamp is None:
        raise RuntimeError('Could not add native lamp')
    for name, value in (('relative_location', unreal.Vector(8., 5., -5.)),
                        ('relative_rotation', unreal.Rotator(0., 0., 0.)),
                        ('intensity_units', unreal.LightUnits.LUMENS),
                        ('intensity', 600.), ('attenuation_radius', 1200.),
                        ('inner_cone_angle', 18.), ('outer_cone_angle', 36.),
                        ('cast_shadows', True), ('visible', True),
                        ('hidden_in_game', False),
                        ('light_color', unreal.Color(255, 239, 216, 255))):
        K.comp_set(lamp, name, value, 'native flashlight')
    for line in K.LOG:
        if 'set_parent_component ' in line and 'WARN' in line:
            K.fail('Native camera/lamp attachment failed: ' + line)
    if K.FAILS:
        raise RuntimeError('Native component configuration failed: ' + repr(K.FAILS))

    # Shared movement API: debug traversal and actual key polling use this body.
    g, b, e = H.newfn(bp, 'Move', signatures['Move'])
    rotation = b.c('/Script/Engine.Pawn:GetControlRotation')
    split = b.c('/Script/Engine.KismetMathLibrary:BreakRotator')
    b.link(rotation, 'ReturnValue', split, 'InRot')
    planar = b.c('/Script/Engine.KismetMathLibrary:MakeRotator')
    b.setv(planar, 'Pitch', '0.0')
    b.setv(planar, 'Roll', '0.0')
    b.link(split, 'Yaw', planar, 'Yaw')
    forward = b.c('/Script/Engine.KismetMathLibrary:GetForwardVector')
    right = b.c('/Script/Engine.KismetMathLibrary:GetRightVector')
    for direction in (forward, right):
        b.link(planar, 'ReturnValue', direction, 'InRot')
    for direction, param in ((forward, 'ForwardBackward'), (right, 'LeftRight')):
        node = b.c('/Script/Engine.Pawn:AddMovementInput')
        b.link(direction, 'ReturnValue', node, 'WorldDirection')
        b.link_param(g, param, node, 'ScaleValue')
        b.setv(node, 'bForce', 'false')
        e = H.cont(b, e, node)
    finish(b, e)

    g, b, e = H.newfn(bp, 'Aim', signatures['Aim'])
    for function, param in (('AddControllerYawInput', 'Yaw'),
                            ('AddControllerPitchInput', 'Pitch')):
        node = b.c('/Script/Engine.Pawn:' + function)
        b.link_param(g, param, node, 'Val')
        e = H.cont(b, e, node)
    finish(b, e)

    g, b, e = H.newfn(bp, 'ToggleLamp')
    enabled = H.notb(b, H.bv(b, 'TorchOn'))
    store = b.s('TorchOn')
    wire(b, enabled, store, 'TorchOn')
    e = H.cont(b, e, store)
    component = H.self_comp(b, 'SpotLightComponent')
    node = b.c('/Script/Engine.SceneComponent:SetHiddenInGame')
    wire(b, component, node, 'self')
    wire(b, H.notb(b, H.bv(b, 'TorchOn')), node, 'NewHidden')
    b.setv(node, 'bPropagateToChildren', 'true')
    e = H.cont(b, e, node)
    finish(b, e)

    g, b, e = H.newfn(bp, 'InitNativePlayer')
    controller = H.player_ctrl(b)
    store = b.s('NativeControllerRef')
    wire(b, controller, store, 'NativeControllerRef')
    e = H.cont(b, e, store)
    valid = b.c(K.F_ISVALID)
    wire(b, H.bv(b, 'NativeControllerRef'), valid, 'Object')
    def input_mode(entry):
        node = b.c('/Script/UMG.WidgetBlueprintLibrary:SetInputMode_GameOnly')
        wire(b, H.bv(b, 'NativeControllerRef'), node, 'PlayerController')
        b.setv(node, 'bFlushInput', 'false')
        return H.cont(b, entry, node)
    e = H.iff(b, e, lambda: (valid, 'ReturnValue'), then_fn=input_mode)
    finish(b, e)

    g, b, e = H.newfn(bp, 'PollNativeInput')
    controller = H.bv(b, 'NativeControllerRef')
    valid = b.c(K.F_ISVALID)
    wire(b, controller, valid, 'Object')
    def poll(entry):
        def down(key):
            node = b.c('/Script/Engine.PlayerController:IsInputKeyDown')
            wire(b, controller, node, 'self')
            b.setv(node, 'Key', '(KeyName="%s")' % key)
            return H.selb(b, scalar(b, 0.), scalar(b, 1.), (node, 'ReturnValue'))
        longitudinal = arithmetic(b, 'Subtract_DoubleDouble', down('W'), down('S'))
        lateral = arithmetic(b, 'Subtract_DoubleDouble', down('D'), down('A'))
        move = H.callbp(b, PLAYER, 'Move')
        wire(b, longitudinal, move, 'ForwardBackward')
        wire(b, lateral, move, 'LeftRight')
        entry = H.cont(b, entry, move)
        mouse = b.c('/Script/Engine.PlayerController:GetInputMouseDelta')
        wire(b, controller, mouse, 'self')
        if b.has_in(mouse, 'execute'):
            entry = H.cont(b, entry, mouse)
        yaw = arithmetic(b, 'Multiply_DoubleDouble', (mouse, 'DeltaX'), H.bv(b, 'MouseSensitivity'))
        pitch = arithmetic(b, 'Multiply_DoubleDouble', (mouse, 'DeltaY'), H.bv(b, 'MouseSensitivity'))
        sign = H.selb(b, scalar(b, -1.), scalar(b, 1.), H.bv(b, 'bInvertMouseY'))
        pitch = arithmetic(b, 'Multiply_DoubleDouble', pitch, sign)
        aim = H.callbp(b, PLAYER, 'Aim')
        wire(b, yaw, aim, 'Yaw')
        wire(b, pitch, aim, 'Pitch')
        entry = H.cont(b, entry, aim)
        return H.iff(b, entry, lambda: H.key_pressed(b, 'F', controller),
                     then_fn=lambda en: H.cont(b, en, H.callbp(b, PLAYER, 'ToggleLamp')))
    e = H.iff(b, e, lambda: (valid, 'ReturnValue'), then_fn=poll)
    finish(b, e)

    graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    b = K.B(graph, 'SchoolPlayer.NativeEvents')
    b.clear(keep_prefixes=())
    begin = b.ev('BeginPlay')
    tick = b.ev('Tick')
    b.link(begin, 'then', H.callbp(b, PLAYER, 'InitNativePlayer'), 'execute')
    b.link(tick, 'then', H.callbp(b, PLAYER, 'PollNativeInput'), 'execute')
    if not b.compile(bp, 'native school movement/camera/lamp') or K.FAILS:
        raise RuntimeError('Native player final compilation failed: ' + repr(K.FAILS))
    if not K.save(path):
        raise RuntimeError('Native player save failed')
    return bp


def build_game_mode():
    if not unreal.EditorAssetLibrary.does_asset_exist(HUD):
        raise RuntimeError('Existing school HUD is required')
    bp, path = K.new_bp(BASE, 'BP_KL_SchoolNativeGameMode', 'GameModeBase')
    parent = K.BPT.get_parent(bp)
    if parent.get_path_name() != '/Script/Engine.GameModeBase':
        raise RuntimeError('SchoolNativeGameMode must have native GameModeBase parent')
    defaults = K.cdo(bp)
    defaults.set_editor_property('default_pawn_class', K.bp_class(PLAYER))
    defaults.set_editor_property('hud_class', K.bp_class(HUD))
    defaults.set_editor_property('player_controller_class', K.native('PlayerController'))
    defaults.set_editor_property('start_players_as_spectators', False)
    b = K.B(unreal.BlueprintEditorLibrary.find_event_graph(bp), 'NativeGameMode')
    if not b.compile(bp, 'native school GameModeBase') or K.FAILS:
        raise RuntimeError('Native game mode compilation failed: ' + repr(K.FAILS))
    if not K.save(path):
        raise RuntimeError('Native game mode save failed')
    return bp


def main():
    report = {'status': 'building', 'player': PLAYER, 'game_mode': GAME_MODE}
    K.FAILS.clear()
    try:
        if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
            raise RuntimeError('Stop PIE before native player build')
        unreal.EditorAssetLibrary.make_directory(BASE)
        player = build_player()
        game_mode = build_game_mode()
        if K.FAILS:
            raise RuntimeError('Native build failures: ' + repr(K.FAILS))
        report.update(status='built', blueprint_status={
            PLAYER: str(player.get_editor_property('status')),
            GAME_MODE: str(game_mode.get_editor_property('status'))},
            parents={PLAYER: '/Script/Engine.Character', GAME_MODE: '/Script/Engine.GameModeBase'},
            controller='/Script/Engine.PlayerController', hud=HUD,
            walk_speed_cm_s=220, camera_eye_above_capsule_cm=64, camera_fov_deg=80,
            flashlight={'lumens': 600, 'radius_cm': 1200},
            runtime='Blueprint Tick; native CharacterMovement; no Python',
            input='Provisional WASD/mouse/F polling; physical capture/remapping not qualified',
            scope='New assets only; original/copied assets preserved', failures=list(K.FAILS))
    except Exception as exc:
        report.update(status='failed', error=repr(exc), failures=list(K.FAILS))
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        raise
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
