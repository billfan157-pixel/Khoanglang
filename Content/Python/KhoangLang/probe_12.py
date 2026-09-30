"""Discovery probe 12: exact pins for the node ids Milestone 1 will actually use.

No 37k node enumeration - only the ids in NODES, so it runs in seconds.
Also proves the Cast-to-Blueprint node id shape and the Key struct for IMC authoring.
"""

import os
import sys
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
sys.path.insert(0, HERE)

OUT_DIR = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p12'
os.makedirs(OUT_DIR, exist_ok=True)
REPORT = []


def p(msg):
    line = str(msg)
    REPORT.append(line)
    unreal.log('KL12: ' + line)
    with open(os.path.join(OUT_DIR, 'report.txt'), 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


NODES = [
    # audio
    'Audio|Components|Audio|SetSound', 'Audio|Components|Audio|Play',
    'Audio|Components|Audio|FadeIn', 'Audio|Components|Audio|FadeOut',
    'Audio|Components|Audio|SetVolumeMultiplier',
    'Audio|Components|Audio|SetLowPassFilterEnabled',
    'Audio|Components|Audio|SetLowPassFilterFrequency',
    'Audio|Components|Audio|SetPaused', 'Audio|Components|Audio|AdjustVolume',
    'Audio|Components|Audio|IsPlaying',
    # trace / find
    'Collision|SphereTraceByChannel', 'Collision|LineTraceByChannel',
    'Actor|GetActorOfClass', 'Actor|GetAllActorsOfClass', 'Actor|GetComponentbyClass',
    'Utilities|ClassIsChildOf', 'Utilities|IsValid', 'Utilities|IsA', 'Utilities|GetClass',
    'Utilities|Select',
    # flow / time
    'Utilities|FlowControl|Delay', 'Utilities|FlowControl|DoOnce',
    'Utilities|FlowControl|Switch|SwitchonString',
    'Utilities|Time|SetTimerbyFunctionName', 'Utilities|Time|GetGameTimeinSeconds',
    # debug / vis
    'Development|PrintString', 'Development|SetHiddeninGame', 'Rendering|SetVisibility',
    'Collision|SetCollisionEnabled', 'Transformation|GetActorLocation',
    'Transformation|GetActorTransform', 'Transformation|GetActorForwardVector',
    # arrays / strings
    'Utilities|Array|Get', 'Utilities|Array|Length', 'Utilities|Array|Contains',
    'Utilities|Array|Add', 'Utilities|Array|IsEmpty',
    'Utilities|Operators|Add', 'Utilities|String|Len', 'Utilities|String|Append',
    'Utilities|String|ToString(Boolean)', 'Utilities|String|ToString(Integer)',
    'Utilities|String|ParseIntoArray',
    # game flow
    'Game|QuitGame', 'Game|OpenLevel(byName)', 'Game|GetPlayerController',
    'Gameplay|GetPlayerController', 'Pawn|GetController', 'Actor|Destroy',
    'Actor|SetActorHiddenInGame', 'Actor|SetActorEnableCollision',
    'Class|SpotLightComponent|SetIntensity', 'Class|SpotLight|GetSpotLightComponent',
    'Class|PointLightComponent|SetIntensity', 'Class|PointLight|GetLightComponent',
    'Class|LightComponent|SetIntensity', 'Class|LightComponent|SetVisibility',
    'Class|AudioComponent|SetAutoDestroy', 'Class|AudioComponent|SetSound',
    'Class|ActorComponent|SetActive',
    'Utilities|Casting|CastToActor', 'Utilities|Casting|CastToHUD',
    'Utilities|Casting|CastToPlayerController', 'Utilities|Casting|CastToStaticMeshActor',
    'Utilities|Text|ToText(String)', 'Utilities|Text|ToText',
    'Utilities|Struct|BreakHitResult', 'Utilities|Struct|MakeLiteralString',
    'Variables|Collision|GetActorLocation',
    'UserInterface|GetOwningPlayer', 'Development|SetTimer',
]


def main():
    from editor_toolset.toolsets import blueprint as BP
    from editor_toolset.toolsets import actor as ACT
    from editor_toolset.toolsets.blueprint import ContainerType

    tmp = {}
    for name, parent in (('TMP12_Actor', unreal.Actor),
                         ('TMP12_HUD', unreal.HUD),
                         ('TMP12_PC', unreal.PlayerController)):
        tmp[name] = BP.BlueprintTools.create('/Game/KhoangLang/Data', name,
                                             parent.static_class())
    # add a component so component-getter / cast shapes are visible
    ACT.ActorTools.add_component(tmp['TMP12_Actor'], unreal.SpotLightComponent.static_class(),
                                 'TestSpot')
    ACT.ActorTools.add_component(tmp['TMP12_Actor'], unreal.AudioComponent.static_class(),
                                 'TestAudio')
    BP.BlueprintTools.compile_blueprint(tmp['TMP12_Actor'])

    g_actor = BP.BlueprintTools.list_graphs(tmp['TMP12_Actor'])[0]
    g_hud = BP.BlueprintTools.list_graphs(tmp['TMP12_HUD'])[0]
    g_pc = BP.BlueprintTools.list_graphs(tmp['TMP12_PC'])[0]

    def dump(graph, ids, tag):
        out = []
        for tid in ids:
            hits = BP.BlueprintTools.find_node_types(graph, tid)
            if not hits:
                out.append('### MISSING %s' % tid)
                continue
            if len(hits) > 1 and not any(h.lower() == tid.lower() for h in hits):
                out.append('### AMBIGUOUS %s -> %s' % (tid, hits[:6]))
                continue
            use = tid if tid in hits else hits[0]
            try:
                ni = BP.BlueprintTools.get_node_type_pins(graph, use)
            except Exception as exc:
                out.append('### ERR %s %r' % (use, exc))
                continue
            ins = ', '.join('%s:%s' % (x.name, x.type_id) for x in ni.input_pins)
            outs = ', '.join('%s:%s' % (x.name, x.type_id) for x in ni.output_pins)
            out.append('%s\n   IN  [%s]\n   OUT [%s]' % (use, ins, outs))
        with open(os.path.join(OUT_DIR, '%s_pins.txt' % tag), 'w', encoding='utf-8') as f:
            f.write('\n'.join(out))
        miss = [l for l in out if l.startswith('###')]
        p('%s: %d ids, %d missing/ambiguous' % (tag, len(ids), len(miss)))
        for m in miss:
            p('   ' + m)

    dump(g_actor, NODES, 'actor')
    dump(g_hud, ['HUD|DrawText', 'HUD|DrawRect', 'HUD|DrawLine', 'Actor|GetOwningPlayerController',
                 'Class|PlayerController|GetHUD', 'Class|PlayerController|GetPlayerViewPoint',
                 'PlayerController|GetHUD', 'Utilities|String|ToString(Text)',
                 'Utilities|Text|ToString'], 'hud')
    dump(g_pc, ['PlayerController|GetHUD', 'Game|GetPlayerController',
                'Class|PlayerController|GetHUD', 'Utilities|Platform|SetWindowTitle',
                'Game|SetInputMode', 'UserInterface|SetInputModeGameAndUI',
                'UserInterface|SetInputModeGameOnly', 'UserInterface|SetInputModeUIOnly',
                'PlayerController|ShowMouseCursor', 'Class|PlayerController|SetPause'], 'pc')

    # cast-to-blueprint shape
    p('')
    p('=== cast to blueprint class ===')
    for probe in ('CastToTMP12Actor', 'CastToBP_KL_', 'CastToStaticMeshActor'):
        p('  %-24s -> %s' % (probe, BP.BlueprintTools.find_node_types(g_actor, probe)[:6]))

    p('')
    p('=== Key struct for IMC authoring ===')
    for attempt, fn in (
        ("unreal.Key(key_name='E')", lambda: unreal.Key(key_name='E')),
        ("unreal.Key()", lambda: unreal.Key()),
    ):
        try:
            k = fn()
            p('  OK %s -> %r  to_tuple=%s' % (attempt, k, k.to_tuple()))
        except Exception as exc:
            p('  FAIL %s -> %r' % (attempt, exc))
    try:
        k = unreal.Key()
        k.set_editor_property('key_name', 'E')
        p("  set_editor_property('key_name','E') -> %r" % k)
    except Exception as exc:
        p('  set_editor_property failed: %r' % (exc,))
    try:
        k = unreal.Key()
        k.import_text('(KeyName="E")')
        p('  import_text -> %r' % k)
    except Exception as exc:
        p('  import_text failed: %r' % (exc,))
    try:
        p('  Key static_struct: %s' % unreal.Key.static_struct())
    except Exception as exc:
        p('  static_struct failed: %r' % (exc,))

    p('')
    p('=== InputMappingContext.map_key signature test ===')
    at = unreal.AssetToolsHelpers.get_asset_tools()
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.make_directory('/Game/KhoangLang/Input')
    ia = at.create_asset('TMP12_IA', '/Game/KhoangLang/Input', unreal.InputAction,
                         unreal.InputAction_Factory())
    imc = at.create_asset('TMP12_IMC', '/Game/KhoangLang/Input',
                          unreal.InputMappingContext, unreal.InputMappingContext_Factory())
    k = unreal.Key()
    k.set_editor_property('key_name', 'E')
    try:
        imc.map_key(ia, k)
        p('  mapped: %s' % [(str(m.key), m.action.get_name())
                            for m in imc.get_editor_property('mappings')])
    except Exception as exc:
        p('  map_key failed: %r' % (exc,))

    p('')
    p('=== add_component results on TMP12_Actor ===')
    cdo = BP.BlueprintTools.get_default_object(tmp['TMP12_Actor'])
    for c in ACT.ActorTools.get_components(cdo):
        p('   %-16s %s' % (c.get_name(), c.get_class().get_name()))

    for name in tmp:
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/' + name)
    for n in ('TMP12_IA', 'TMP12_IMC'):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Input/' + n)

    p('PROBE12_DONE')


try:
    rep = os.path.join(OUT_DIR, 'report.txt')
    if os.path.exists(rep):
        os.remove(rep)
    main()
except Exception:
    p(traceback.format_exc())
    p('PROBE12_FAILED')
