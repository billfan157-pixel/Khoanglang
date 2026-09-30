"""Discovery probe 28: the function-path table the hand-built graphs will use."""

import os
import sys
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
sys.path.insert(0, HERE)

OUT_DIR = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p28'
os.makedirs(OUT_DIR, exist_ok=True)
REPORT = []


def p(msg):
    line = str(msg)
    REPORT.append(line)
    unreal.log('KL28: ' + line)
    with open(os.path.join(OUT_DIR, 'report.txt'), 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


PATHS = [
    # actor / transform
    '/Script/Engine.Actor:GetActorLocation',
    '/Script/Engine.Actor:GetActorTransform',
    '/Script/Engine.Actor:GetActorForwardVector',
    '/Script/Engine.Actor:SetActorHiddenInGame',
    '/Script/Engine.Actor:GetComponentByClass',
    # controller / pawn
    '/Script/Engine.Pawn:GetController',
    '/Script/Engine.PlayerController:GetPawn',
    '/Script/Engine.PlayerController:GetControlledPawn',
    '/Script/Engine.PlayerController:GetPlayerViewPoint',
    '/Script/Engine.PlayerController:GetControlRotation',
    '/Script/Engine.PlayerController:GetHUD',
    '/Script/Engine.PlayerController:WasInputKeyJustPressed',
    '/Script/Engine.PlayerController:IsInputKeyDown',
    # gameplay statics
    '/Script/Engine.GameplayStatics:SphereTraceSingleByChannel',
    '/Script/Engine.GameplayStatics:GetAllActorsOfClass',
    '/Script/Engine.GameplayStatics:GetActorOfClass',
    '/Script/Engine.GameplayStatics:QuitGame',
    '/Script/Engine.GameplayStatics:OpenLevel',
    '/Script/Engine.GameplayStatics:GetPlayerController',
    '/Script/Engine.GameplayStatics:ProjectWorldLocationToScreen',
    # kismet
    '/Script/Engine.KismetSystemLibrary:PrintString',
    '/Script/Engine.KismetSystemLibrary:Delay',
    '/Script/Engine.KismetSystemLibrary:LineTraceSingle',
    '/Script/Engine.KismetSystemLibrary:SphereTraceByChannel',
    '/Script/Engine.KismetSystemLibrary:GetForwardVector',
    '/Script/Engine.KismetSystemLibrary:ClassIsChildOf',
    '/Script/Engine.KismetSystemLibrary:IsValid',
    '/Script/Engine.KismetSystemLibrary:Conv_StringToText',
    # audio
    '/Script/Engine.AudioComponent:Play',
    '/Script/Engine.AudioComponent:SetSound',
    '/Script/Engine.AudioComponent:SetVolumeMultiplier',
    '/Script/Engine.AudioComponent:FadeIn',
    '/Script/Engine.AudioComponent:FadeOut',
    '/Script/Engine.AudioComponent:SetLowPassFilterEnabled',
    '/Script/Engine.AudioComponent:SetLowPassFilterFrequency',
    '/Script/Engine.AudioComponent:Stop',
    # scene / lights
    '/Script/Engine.SceneComponent:SetVisibility',
    '/Script/Engine.SpotLightComponent:SetIntensity',
    '/Script/Engine.SpotLightComponent:SetInnerConeAngle',
    '/Script/Engine.PointLightComponent:SetIntensity',
    '/Script/Engine.PointLightComponent:SetAttenuationRadius',
    '/Script/Engine.LightComponent:SetIntensity',
    '/Script/Engine.StaticMeshComponent:SetStaticMesh',
    '/Script/Engine.StaticMeshComponent:SetMaterial',
    # input
    '/Script/EnhancedInput.EnhancedInputLocalPlayerSubsystem:AddMappingContext',
    '/Script/EnhancedInput.EnhancedInputLocalPlayerSubsystem:RemoveMappingContext',
    '/Script/EnhancedInput.EnhancedInputComponent:BindAction',
    # misc
    '/Script/Engine.HUD:DrawText',
    '/Script/Engine.HUD:DrawRect',
    '/Script/Engine.HUD:DrawLine',
    '/Script/Engine.HUD:GetOwningPlayerController',
    '/Script/Engine.PlayerController:ProjectWorldLocationToScreen',
    '/Script/Engine.GameplayStatics:DoesSaveGameExist',
    '/Script/Engine.GameplayStatics:GetGameTimeInSeconds',
    '/Script/Engine.MathLibrary:VInterpTo',
    '/Script/Engine.MathLibrary:VectorDistance',
    '/Script/Engine.MathLibrary:Dot_VectorFloat',
    '/Script/Engine.MathLibrary:FindLookAtRotation',
    '/Script/Engine.MathLibrary:Clamp',
    '/Script/Engine.MathLibrary:Abs',
]

NAMES = [
    'Utilities|Casting|CastToPlayerController',
    'Utilities|Casting|CastToBP_KL_Journal',
    'AddEvent|EventTick',
    'AddEvent|EventBeginPlay',
    'AddEvent|EventDestroyed',
    'Utilities|FlowControl|ForLoop',
    'Utilities|FlowControl|DoOnce',
    'Utilities|Time|SetTimerbyFunctionName',
    'Utilities|Time|GetGameTimeinSeconds',
    'Utilities|String|PrintString',
    'Utilities|String|Left',
    'Utilities|String|Mid',
    'Utilities|String|Len',
    'Utilities|Array|Get(aref)',
    'Utilities|Array|Length',
    'Utilities|Array|IsEmpty',
    'Utilities|Array|Add',
    'Utilities|Array|ContainsItem',
    'Utilities|Map|Length',
    'Utilities|Select',
    'Utilities|Operators|Add',
    'Utilities|Operators|Equal(==)',
    'Utilities|Operators|NotEqual(!=)',
    'Utilities|Operators|AndBoolean',
    'Utilities|Text|ToText(String)',
    'Utilities|String|ToString(Text)',
    'Math|Color|MakeColor',
    'Math|Vector|MakeVector',
    'Math|Integer|int',
    'Math|Integer|Add',
    'Collision|BreakHitResult',
    'Collision|SetActorEnableCollision',
    'Rendering|Components|Light|SetIntensity',
    'Development|PrintString',
    'Development|SetHiddeninGame',
    'Game|QuitGame',
    'Game|OpenLevel(byName)',
    'Actor|GetAllActorsOfClass',
    'Audio|Components|Audio|SetLowPassFilterEnabled',
    'Audio|Components|Audio|FadeOut',
    'Actor|GetComponentbyClass',
    'Collision|SphereTraceByChannel',
    'Collision|MultiSphereTraceByChannel',
    'Utilities|FlowControl|DoOnce',
    'Input|AddMappingContext',
    'LocalPlayerSubsystems|GetEnhancedInputLocalPlayerSubsystem',
    'PlayerController|LocalPlayerSubsystems|GetEnhancedInputLocalPlayerSubsystem',
    'HUD|DrawText',
    'HUD|DrawRect',
    'Pawn|GetPlayerViewPoint',
    'Class|GameModeBase|SetHUDClass',
    'Class|GameModeBase|SetDefaultPawnClass',
    'Class|GameModeBase|SetPlayerControllerClass',
]


def main():
    from editor_toolset.toolsets import blueprint as BP
    from editor_toolset.toolsets.blueprint import _get_node_type_id
    BPT = BP.BlueprintTools
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.make_directory('/Game/KhoangLang/Data')
    if unreal.load_asset('/Game/KhoangLang/Data/TMP28_PC'):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP28_PC')
    pc = BPT.create('/Game/KhoangLang/Data', 'TMP28_PC', unreal.load_class(
        None, '/Game/FirstPerson/Blueprints/'
              'BP_FirstPersonPlayerController.BP_FirstPersonPlayerController_C'))
    BPT.compile_blueprint(pc)
    g = unreal.BlueprintEditorLibrary.find_event_graph(pc)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)

    p('=== A. add_call_function_node paths ===')
    good, bad = [], []
    for path in PATHS:
        try:
            n = ed.add_call_function_node(path)
        except Exception as exc:
            p('  RAISE %-64s %r' % (path, exc))
            bad.append(path)
            continue
        if n is None:
            bad.append(path)
            continue
        ni = BPT.get_node_infos([n])[0]
        ins = ', '.join('%s:%s' % (x.name, x.type_id) for x in ni.input_pins)
        outs = ', '.join('%s:%s' % (x.name, x.type_id) for x in ni.output_pins)
        p('  OK  %s\n        IN  [%s]\n        OUT [%s]' % (path, ins, outs))
        good.append(path)
        ed.remove_nodes([n])
    p('  good=%d bad=%d' % (len(good), len(bad)))
    p('  bad: %s' % bad)

    p('')
    p('=== B. create_node_from_name ids ===')
    for nid in NAMES:
        try:
            n = ed.create_node_from_name(nid, unreal.Vector2D(0, 0), [], None)
        except Exception as exc:
            p('  RAISE %-58s %r' % (nid, exc))
            continue
        if n is None:
            p('  MISS %s' % nid)
            continue
        ni = BPT.get_node_infos([n])[0]
        ins = ', '.join('%s:%s' % (x.name, x.type_id) for x in ni.input_pins)
        outs = ', '.join('%s:%s' % (x.name, x.type_id) for x in ni.output_pins)
        p('  OK   %-58s %s\n        IN  [%s]\n        OUT [%s]' % (nid, _get_node_type_id(n),
                                                                 ins, outs))
        ed.remove_nodes([n])

    p('')
    p('=== C. cast node to a blueprint class that exists ===')
    for nid in ('Utilities|Casting|CastToBP_KL_Journal',
                'Utilities|Casting|CastToPlayerController',
                'Utilities|Casting|CastToHUD'):
        n = ed.create_node_from_name(nid, unreal.Vector2D(0, 0), [], None)
        if n is None:
            p('  MISS %s' % nid)
            continue
        ni = BPT.get_node_infos([n])[0]
        p('  OK %s: IN [%s] OUT [%s]' % (
            nid,
            ', '.join('%s:%s' % (x.name, x.type_id) for x in ni.input_pins),
            ', '.join('%s:%s' % (x.name, x.type_id) for x in ni.output_pins)))
        ed.remove_nodes([n])

    p('')
    p('=== D. FKey struct pin: set a default value and read it back ===')
    n = ed.add_call_function_node('/Script/Engine.PlayerController:WasInputKeyJustPressed')
    if n:
        ni = BPT.get_node_infos([n])[0]
        p('  pins: %s' % [(x.name, x.type_id) for x in ni.input_pins])
        keypin = next(x for x in ni.input_pins if x.name == 'Key')
        for val in ('(KeyName="E")', '((KeyName="E"))'):
            try:
                BPT.set_pin_value(keypin.pin_id, val)
                p('    set %-16s -> now %r' % (val, BPT.get_pin_value(keypin.pin_id)))
            except Exception as exc:
                p('    set %-16s raised %r' % (val, exc))
        ed.remove_nodes([n])

    p('')
    p('=== cleanup ===')
    unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP28_PC')
    p('PROBE28_DONE')


try:
    rep = os.path.join(OUT_DIR, 'report.txt')
    if os.path.exists(rep):
        os.remove(rep)
    main()
except Exception:
    p(traceback.format_exc())
    p('PROBE28_DONE_FATAL')
