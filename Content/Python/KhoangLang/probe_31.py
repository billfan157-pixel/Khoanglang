"""Discovery probe 31: the node set the Milestone 1 build needs."""

import os
import sys
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
sys.path.insert(0, HERE)

OUT_DIR = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p31'
os.makedirs(OUT_DIR, exist_ok=True)


def p(msg):
    line = str(msg)
    unreal.log('KL31: ' + line)
    with open(os.path.join(OUT_DIR, 'report.txt'), 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


PATHS = [
    # camera / transform
    '/Script/Engine.PlayerCameraManager:GetCameraLocation',
    '/Script/Engine.PlayerCameraManager:GetCameraRotation',
    '/Script/Engine.PlayerCameraManager:GetCameraViewPoint',
    '/Script/Engine.Actor:K2_GetActorRotation',
    '/Script/Engine.Actor:RotatorFromActor',
    '/Script/Engine.SceneComponent:GetComponentLocation',
    '/Script/Engine.SceneComponent:GetForwardVector',
    '/Script/Engine.SceneComponent:GetRightVector',
    '/Script/Engine.SceneComponent:K2_AttachToComponent',
    # math
    '/Script/Engine.KismetMathLibrary:GetForwardVector',
    '/Script/Engine.KismetMathLibrary:GetRightVector',
    '/Script/Engine.KismetMathLibrary:VectorMultiply_VectorFloat',
    '/Script/Engine.KismetMathLibrary:Add_VectorVector',
    '/Script/Engine.KismetMathLibrary:VectorDistance',
    '/Script/Engine.KismetMathLibrary:Clamp',
    '/Script/Engine.KismetMathLibrary:BranchFloat',
    '/Script/Engine.KismetMathLibrary:Max',
    '/Script/Engine.KismetMathLibrary:IntPlus_Int',
    '/Script/Engine.KismetMathLibrary:Conv_BoolToString',
    '/Script/Engine.KismetMathLibrary:Conv_IntToString',
    '/Script/Engine.KismetMathLibrary:EqualEqual_FloatFloat',
    # gameplay
    '/Script/Engine.GameplayStatics:PlaySoundAtLocation',
    '/Script/Engine.GameplayStatics:PlaySound2D',
    '/Script/Engine.GameplayStatics:GetPlayerPawn',
    '/Script/Engine.GameplayStatics:SetGamePaused',
    '/Script/Engine.GameplayStatics:GetTimeSeconds',
    '/Script/Engine.GameplayStatics:HasBegunPlay',
    '/Script/Engine.GameplayStatics:IsGamePaused',
    '/Script/Engine.ActorComponent:Activate',
    '/Script/Engine.ActorComponent:Deactivate',
    '/Script/Engine.ActorComponent:SetActive',
    '/Script/Engine.ActorComponent:IsActive',
    '/Script/Engine.SceneComponent:IsVisible',
    '/Script/Engine.Actor:HasTag',
    '/Script/Engine.Actor:K2_DestroyActor',
    '/Script/Engine.GameplayStatics:SpawnSoundAtLocation',
    '/Script/Engine.Actor:Tags',
    # misc
    '/Script/Engine.PlayerController:ClientMessage',
    '/Script/Engine.PlayerController:SetPause',
    '/Script/Engine.PlayerController:IsPaused',
    '/Script/Engine.InputComponent:GetInputActionInstance',
    '/Script/Engine.AudioComponent:SetPaused',
    '/Script/Engine.AudioComponent:IsPlaying',
    '/Script/Engine.AudioComponent:AdjustVolume',
    '/Script/Engine.AudioComponent:SetIntParameter',
    '/Script/Engine.LevelBlueprint:HandleBeginOverlap',
    '/Script/Engine.WorldSettings:NotifyBeginOverlap',
    '/Script/Engine.Actor:DispatchBeginOverlap',
    '/Script/Engine.GameplayStatics:DispatchBeginOverlap',
    '/Script/Engine.GameplayStatics:GetActorLocation',
    '/Script/Engine.GameplayStatics:GetAllActorsWithTag',
]

NAMES = [
    # vector / rotator math by action-name id
    'Math|Vector|VectorMultiply',
    'Math|Vector|Add',
    'Math|Vector|Subtract',
    'Math|Vector|Scale',
    'Math|Vector|Dot',
    'Math|Vector|VectorLength',
    'Transformation|GetActorForwardVector',
    'Transformation|GetActorLocation',
    'Transformation|GetActorRightVector',
    'Transformation|GetActorRotation',
    'Transformation|GetActorTransform',
    # HUD events
    'AddEvent|EventDrawHUD',
    'AddEvent|EventBeginPlay',
    'AddEvent|EventTick',
    'AddEvent|EventEndPlay',
    'AddEvent|EventDestroyed',
    'AddEvent|EventInputTouch',
    'Utilities|FlowControl|Branch',
    'Utilities|FlowControl|DoOnce',
    'Utilities|FlowControl|ForLoop',
    'Utilities|FlowControl|Switch|SwitchonString',
    'Utilities|FlowControl|DoIfFalse',
    'Utilities|FlowControl|ForEachLoop',
    'Utilities|Delay',
    'Utilities|Delay|Delay',
    'Utilities|Timer|SetTimer',
    'Utilities|Timer|ClearTimer',
    'Utilities|Timer|IsTimerActive',
    # audio component
    'Audio|Components|Audio|SetVolumeMultiplier',
    'Audio|Components|Audio|Play',
    'Audio|Components|Audio|SetSound',
    'Audio|Components|Audio|FadeIn',
    'Audio|Components|Audio|FadeOut',
    'Audio|Components|Audio|SetLowPassFilterEnabled',
    'Audio|Components|Audio|SetLowPassFilterFrequency',
    'Audio|Components|Audio|Stop',
    'Audio|Components|Audio|AdjustVolume',
    'Audio|Components|Audio|IsPlaying',
    'Audio|Components|Audio|SetPaused',
    # light
    'Rendering|Components|Light|SetIntensity',
    'Rendering|Components|Light|SetLightColor',
    'Rendering|Components|SpotLight|SetInnerConeAngle',
    'Rendering|Components|SpotLight|SetAttenuationRadius',
    'Rendering|Components|Scene|SetVisibility',
    'Rendering|Components|Scene|SetHiddenInGame',
    'Development|SetHiddeninGame',
    'Development|PrintString',
    'Development|DrawDebugLine',
    # gameplay
    'Gameplay|Components|Audio|PlaySoundAtLocation',
    'Gameplay|GameplayStatics|PlaySoundAtLocation',
    'Gameplay|GameplayStatics|GetAllActorsOfClass',
    'Gameplay|GameplayStatics|GetPlayerController',
    'Gameplay|GameplayStatics|GetPlayerPawn',
    'Gameplay|GameplayStatics|OpenLevel',
    'Gameplay|GameplayStatics|SetGamePaused',
    'Actor|GetAllActorsOfClass',
    'Actor|HasTag',
    'Actor|DestroyActor',
    'Actor|GetActorLocation',
    'Actor|SetActorHiddenInGame',
    'Actor|GetComponentbyClass',
    # casting to an existing blueprint class
    'Utilities|Casting|CastToBP_FirstPersonCharacter',
    'Utilities|Casting|CastToBP_FirstPersonPlayerController',
    'Utilities|Casting|CastToHUD',
    'Utilities|Casting|CastToAudioComponent',
    'Utilities|Casting|CastToStaticMeshComponent',
    'Utilities|Casting|CastToPointLightComponent',
    'Utilities|Casting|CastToSceneComponent',
    'Utilities|Casting|CastToBP_FirstPersonGameMode',
    'Utilities|Casting|CastToSoundWave',
    # collision
    'Collision|SphereTraceByChannel',
    'Collision|LineTraceByChannel',
    'Collision|BreakHitResult',
    'Collision|SetActorEnableCollision',
    'Collision|GetActorAtLocation',
    # array / string / text
    'Utilities|Array|Add',
    'Utilities|Array|Get',
    'Utilities|Array|Length',
    'Utilities|Array|IsEmpty',
    'Utilities|Array|ContainsItem',
    'Utilities|Array|Remove',
    'Utilities|String|MakeLiteralString',
    'Utilities|String|ToString(Text)',
    'Utilities|Text|ToText(String)',
    'Utilities|Text|Conv_StringToText',
    'Utilities|Select',
    'Utilities|Operators|Equal(==)',
    'Utilities|Operators|NotEqual(!=)',
    'Utilities|Class|IsChildOf',
    'Utilities|Class|ClassIsChildOf',
    'Utilities|Name|Conv_NameToString',
    'Utilities|Name|ToName(String)',
    'Utilities|Enum|ByteToEnumE',
    # HUD
    'HUD|DrawText',
    'HUD|DrawRect',
    'HUD|DrawLine',
    'HUD|ShowDebug',
    'Class|HUD|DrawText',
    # misc
    'Math|Integer|Add',
    'Math|Integer|int',
    'Math|Integer|Increment',
    'Math|Color|MakeColor',
    'Math|Color|LinearColorToColor',
    'Input|AddMappingContext',
    'Input|RemoveMappingContext',
    'PlayerController|Input|IsInputKeyDown',
    'Input|IsInputKeyDown',
    'LocalPlayerSubsystems|GetEnhancedInputLocalPlayerSubsystem',
    'Game|QuitGame',
    'Game|OpenLevel(byName)',
    'Game|SetGamePaused',
    'Game|PrintToLog',
]


def pins(node):
    from editor_toolset.toolsets import blueprint as BP
    ni = BP.BlueprintTools.get_node_infos([node])[0]
    ins = ', '.join('%s:%s' % (x.name, x.type_id) for x in ni.input_pins)
    outs = ', '.join('%s:%s' % (x.name, x.type_id) for x in ni.output_pins)
    return 'IN [%s] OUT [%s]' % (ins, outs)


def main():
    from editor_toolset.toolsets import blueprint as BP
    from editor_toolset.toolsets.blueprint import _get_node_type_id
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.make_directory('/Game/KhoangLang/Data')
    for n in ('TMP31',):
        if unreal.load_asset('/Game/KhoangLang/Data/' + n):
            unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/' + n)
    bp = BP.BlueprintTools.create('/Game/KhoangLang/Data', 'TMP31', unreal.Actor.static_class())
    BP.BlueprintTools.compile_blueprint(bp)
    g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)

    p('=== A. add_call_function_node ===')
    for path in PATHS:
        try:
            n = ed.add_call_function_node(path)
        except Exception as exc:
            p('  RAISE %s  %r' % (path, exc))
            continue
        if n is None:
            p('  MISS  %s' % path)
            continue
        p('  OK    %-62s %r' % (path, _get_node_type_id(n)))
        p('        %s' % pins(n))
        ed.remove_nodes([n])

    p('')
    p('=== B. create_node_from_name ===')
    for nid in NAMES:
        try:
            n = ed.create_node_from_name(nid, unreal.Vector2D(0, 0), [], None)
        except Exception as exc:
            p('  RAISE %-58s %r' % (nid, exc))
            continue
        if n is None:
            p('  MISS  %s' % nid)
            continue
        p('  OK    %-58s %r' % (nid, _get_node_type_id(n)))
        p('        %s' % pins(n))
        ed.remove_nodes([n])

    p('')
    p('=== C. graph editor member fns present ===')
    for m in sorted(dir(ed)):
        if not m.startswith('_'):
            p('  %s' % m)

    p('')
    p('=== D. cleanup ===')
    unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP31')
    p('PROBE31_DONE')


try:
    rep = os.path.join(OUT_DIR, 'report.txt')
    if os.path.exists(rep):
        os.remove(rep)
    main()
except Exception:
    p(traceback.format_exc())
    p('PROBE31_DONE_FATAL')
