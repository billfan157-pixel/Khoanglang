"""Discovery probe 32: HUD draw event, components, level creation."""

import os
import sys
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
sys.path.insert(0, HERE)

OUT_DIR = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p32'
os.makedirs(OUT_DIR, exist_ok=True)


def p(msg):
    line = str(msg)
    unreal.log('KL32: ' + line)
    with open(os.path.join(OUT_DIR, 'report.txt'), 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


def pins(node):
    from editor_toolset.toolsets import blueprint as BP
    ni = BP.BlueprintTools.get_node_infos([node])[0]
    ins = ', '.join('%s:%s' % (x.name, x.type_id) for x in ni.input_pins)
    outs = ', '.join('%s:%s' % (x.name, x.type_id) for x in ni.output_pins)
    return 'IN [%s] OUT [%s]' % (ins, outs)


PATHS = [
    '/Script/Engine.ActorComponent:GetOwner',
    '/Script/Engine.ActorComponent:K2_DestroyComponent',
    '/Script/Engine.PrimitiveComponent:SetCollisionEnabled',
    '/Script/Engine.PrimitiveComponent:SetCollisionResponseToChannel',
    '/Script/Engine.PrimitiveComponent:SetGenerateOverlapEvents',
    '/Script/Engine.SceneComponent:SetVisibility',
    '/Script/Engine.SceneComponent:K2_GetComponentLocation',
    '/Script/Engine.SceneComponent:GetComponentTransform',
    '/Script/Engine.StaticMeshComponent:SetStaticMesh',
    '/Script/Engine.StaticMeshComponent:SetMaterial',
    '/Script/Engine.KismetMathLibrary:Multiply_FloatFloat',
    '/Script/Engine.KismetMathLibrary:Add_FloatFloat',
    '/Script/Engine.KismetMathLibrary:Conv_TextToString',
    '/Script/Engine.KismetMathLibrary:Less_FloatFloat',
    '/Script/Engine.KismetMathLibrary:Greater_FloatFloat',
    '/Script/Engine.KismetMathLibrary:BranchFloatFloat',
    '/Script/Engine.HUD:Canvas',
    '/Script/Engine.PlayerController:WasInputKeyJustPressed',
    '/Script/Engine.PlayerController:WasInputKeyJustReleased',
    '/Script/Engine.GameplayStatics:GetPlayerController',
    '/Script/Engine.GameplayStatics:GetPlayerController_',
    '/Script/Engine.GameplayStatics:StaticClass',
    '/Script/Engine.Actor:GetInstigator',
    '/Script/Engine.PlayerController:PlayerCameraManager',
    '/Script/Engine.GameplayStatics:GetGameplayC',
    '/Script/Engine.GameplayStatics:EnableInput',
    '/Script/Engine.GameplayStatics:Execute_ConsoleCommand',
    '/Script/Engine.GameplayStatics:SetSoundMixClassOverride',
    '/Script/Engine.Actor:BlueprintInitializeComponent',
    '/Script/Engine.ActorComponent:RegisterComponent',
    '/Script/Engine.GameplayStatics:SetSoundMixOverride',
    '/Script/Engine.SoundMix',
    '/Script/Engine.GameplayStatics:GetSoundMixClassOverride',
]

NAMES = [
    'Utilities|Struct|BreakVector',
    'Utilities|Struct|MakeVector',
    'Utilities|Struct|MakeRotator',
    'Utilities|Struct|BreakRotator',
    'Utilities|Struct|MakeLinearColor',
    'Utilities|Struct|BreakLinearColor',
    'Utilities|FlowControl|ForEachLoop',
    'Utilities|FlowControl|ForLoop',
    'Utilities|FlowControl|DoOnce',
    'Utilities|Math|Float|*',
    'Utilities|Math|Float|Multiply',
    'Math|Float|*',
    'Math|Float|Multiply_FloatFloat',
    'Math|Float|Add',
    'Math|Integer|Add',
    'Math|Integer|int',
    'Math|Integer|Subtract',
    'Math|Boolean|And',
    'Math|Boolean|Or',
    'Math|Boolean|Not',
    'Math|Boolean|BooleanAND',
    'Audio|Components|Audio|SetSound',
    'Audio|Components|Audio|Play',
    'Rendering|Components|SpotLight|SetInnerConeAngle',
    'Rendering|Components|SpotLight|SetOuterConeAngle',
    'Rendering|Components|SpotLight|SetAttenuationRadius',
    'Rendering|Components|SpotLight|SetIntensity',
    'Rendering|Components|Light|SetIntensity',
    'Rendering|Components|Light|SetLightColor',
    'Components|Activation|Activate',
    'Components|Activation|Deactivate',
    'Components|Activation|IsActive',
    'Component|ActorComponent|GetOwner',
    'Component|SceneComponent|SetVisibility',
    'Component|SpotLight|SetIntensity',
    'HUD|DrawText',
    'Class|HUD|GetOwningPlayerController',
    'Utilities|Text|IsEmpty',
    'Utilities|String|IsEmpty',
    'Utilities|String|EqualEqual',
    'Utilities|String|Equal',
    'Utilities|String|Len',
]


def main():
    from editor_toolset.toolsets import blueprint as BP
    from editor_toolset.toolsets import actor as ACT
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.make_directory('/Game/KhoangLang/Data')
    for n in ('TMP32_Act', 'TMP32_Comp'):
        if unreal.load_asset('/Game/KhoangLang/Data/' + n):
            unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/' + n)

    bp = BP.BlueprintTools.create('/Game/KhoangLang/Data', 'TMP32_Act',
                                  unreal.Actor.static_class())
    BP.BlueprintTools.compile_blueprint(bp)
    g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)

    p('=== A. paths ===')
    for path in PATHS:
        try:
            n = ed.add_call_function_node(path)
        except Exception as exc:
            p('  RAISE %-56s %r' % (path, exc))
            continue
        if n is None:
            p('  MISS  %s' % path)
            continue
        p('  OK    %-56s' % path)
        p('        %s' % pins(n))
        ed.remove_nodes([n])

    p('')
    p('=== B. names ===')
    for nid in NAMES:
        try:
            n = ed.create_node_from_name(nid, unreal.Vector2D(0, 0), [], None)
        except Exception as exc:
            p('  RAISE %-52s %r' % (nid, exc))
            continue
        if n is None:
            p('  MISS  %s' % nid)
            continue
        p('  OK    %-52s %s' % (nid, pins(n)))
        ed.remove_nodes([n])

    p('')
    p('=== C. HUD blueprint: can we get a Draw HUD event? ===')
    hud = BP.BlueprintTools.create('/Game/KhoangLang/Data', 'TMP32_Comp',
                                  unreal.HUD.static_class())
    BP.BlueprintTools.compile_blueprint(hud)
    hg = unreal.BlueprintEditorLibrary.find_event_graph(hud)
    hed = unreal.BlueprintGraphEditor.get_graph_editor(hg)
    p('  existing nodes: %s' % [n.get_class().get_name() for n in hed.list_all_nodes()])
    for cand in ('ReceiveDrawHUD', 'DrawHUD', 'EventDrawHUD'):
        try:
            n = hed.find_event_node(cand)
        except Exception as exc:
            n = 'EXC %r' % (exc,)
        p('  find_event_node(%s) -> %s' % (cand, n))
    p('  add_custom_event_node(DrawHUD) ->')
    try:
        n = hed.add_custom_event_node('DrawHUD')
        p('    %s' % (n,))
    except Exception as exc:
        p('    raised %r' % (exc,))
    p('  add_dispatcher_event_node usage probe')
    for args in ((), ('ReceiveDrawHUD',), ('DrawHUD',)):
        try:
            n = hed.add_dispatcher_event_node(*args)
            p('    %s -> %s' % (args, n))
            if n:
                p('      %s' % pins(n))
                hed.remove_nodes([n])
        except Exception as exc:
            p('    %s raised %r' % (args, exc))
    p('  add_macro_node probe')
    for mid in ('ForEachLoop', 'ForLoop', 'DoOnce', 'Delay', 'LibraryFunction'):
        try:
            n = hed.add_macro_node(mid, unreal.Vector2D(0, 0), False)
            p('    %s -> %s' % (mid, n))
            if n:
                p('      %s' % pins(n))
                hed.remove_nodes([n])
        except Exception as exc:
            p('    %s raised %r' % (mid, exc))

    p('')
    p('=== D. add_component on an actor BP ===')
    for cname, ccls in (('SpotLight', unreal.SpotLightComponent),
                        ('PointLight', unreal.PointLightComponent),
                        ('AudioComp', unreal.AudioComponent),
                        ('Sphere', unreal.SphereComponent),
                        ('Box', unreal.BoxComponent),
                        ('StaticMesh', unreal.StaticMeshComponent),
                        ('SkyLight', unreal.SkyLightComponent),
                        ('ExponentialHeightFog', unreal.ExponentialHeightFogComponent),
                        ('PostProcess', unreal.PostProcessComponent),
                        ('InstancedStaticMesh', unreal.InstancedStaticMeshComponent)):
        try:
            c = ACT.ActorTools.add_component(bp, ccls.static_class(), 'KL_' + cname)
            p('  OK %-24s -> %s' % (cname, c))
            if c is not None:
                p('     class=%s' % c.get_class().get_name())
        except Exception as exc:
            p('  RAISE %-24s %r' % (cname, exc))
    BP.BlueprintTools.compile_blueprint(bp)
    p('  status: %s' % bp.get_editor_property('status'))
    p('  scs components: %s' % [
        c.get_name() for c in ACT.ActorTools.get_components(
            BP.BlueprintTools.get_default_object(bp))])

    p('')
    p('=== E. SceneTools / level api ===')
    from editor_toolset.toolsets import scene as SCENE
    p('  SceneTools members: %s' % [m for m in dir(SCENE.SceneTools) if not m.startswith('_')])
    p('  EditorLevelLibrary: new_level=%s load_level=%s' % (
        hasattr(unreal.EditorLevelLibrary, 'new_level'),
        hasattr(unreal.EditorLevelLibrary, 'load_level')))
    p('  does /Game/KhoangLang/Maps exist: %s' % (
        unreal.EditorAssetLibrary.does_directory_exist('/Game/KhoangLang/Maps'),))

    p('')
    p('=== F. cleanup ===')
    unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP32_Act')
    unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP32_Comp')
    p('PROBE32_DONE')


try:
    rep = os.path.join(OUT_DIR, 'report.txt')
    if os.path.exists(rep):
        os.remove(rep)
    main()
except Exception:
    p(traceback.format_exc())
    p('PROBE32_DONE_FATAL')
