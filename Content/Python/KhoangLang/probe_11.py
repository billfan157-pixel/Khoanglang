"""Discovery probe 11: verify every engine/toolset API Milestone 1 depends on.

Answers, with no guessing:
  1. Input asset factories (InputAction / InputMappingContext) available to Python.
  2. Fonts that can render Vietnamese diacritics for the HUD.
  3. Complete node type id lists per graph context (written to *_nodes.txt).
  4. Exact pin names/types for the node ids Milestone 1 will use.
  5. Component tree of the First Person template character.
  6. Level creation / actor spawn / save APIs.
  7. HUD drawing entry points.
  8. Whether a Blueprint Interface can be created headless.
"""

import os
import re
import sys
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
sys.path.insert(0, HERE)

OUT_DIR = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p11'
os.makedirs(OUT_DIR, exist_ok=True)

REPORT = []


def p(msg):
    line = str(msg)
    REPORT.append(line)
    unreal.log('KL11: ' + line)
    with open(os.path.join(OUT_DIR, 'report.txt'), 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


def guard(label, fn):
    try:
        return fn()
    except Exception as exc:
        p('  !! %s FAILED: %r' % (label, exc))
        return None


def dump_nodes(bp, graph, tag):
    from editor_toolset.toolsets import blueprint as BP
    try:
        allids = sorted(set(BP.BlueprintTools.find_node_types(graph, '')))
    except Exception as exc:
        p('  !! find_node_types(%s) failed: %r' % (tag, exc))
        return []
    path = os.path.join(OUT_DIR, '%s_nodes.txt' % tag)
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(allids))
    p('  %-22s %5d node types -> %s' % (tag, len(allids), os.path.basename(path)))
    return allids


def pin_dump(graph, type_ids, tag):
    from editor_toolset.toolsets import blueprint as BP
    out = []
    for tid in type_ids:
        try:
            ni = BP.BlueprintTools.get_node_type_pins(graph, tid)
        except Exception as exc:
            out.append('!! %s -> %r' % (tid, exc))
            continue
        ins = ', '.join('%s:%s' % (x.name, x.type_id) for x in ni.input_pins)
        outs = ', '.join('%s:%s' % (x.name, x.type_id) for x in ni.output_pins)
        out.append('%s\n   IN  [%s]\n   OUT [%s]' % (tid, ins, outs))
    path = os.path.join(OUT_DIR, '%s_pins.txt' % tag)
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))
    p('  pins -> %s (%d ids)' % (os.path.basename(path), len(type_ids)))
    return out


KEYWORDS = [
    'ToText', 'Conv_StringToText', 'Conv_TextToString', 'StringConv', 'PrintString',
    'PlaySound', 'SetSound', 'SetVolume', 'FadeIn', 'FadeOut',
    'AudioComponent', 'SoundMix', 'StopAudio',
    'SphereTrace', 'LineTrace', 'TraceWorld', 'GetHitResult',
    'GetAllActorsOfClass', 'GetActorOfClass', 'GetActorLocation', 'GetActorRotation',
    'GetActorTransform', 'GetComponent', 'StaticMeshComponent',
    'Casting|CastTo', 'IsValid', 'Delay', 'SwitchOnBool', 'SwitchOnString', 'SwitchOnInt',
    'QuitGame', 'SetInputMode', 'ShowMouseCursor', 'GetPlayerController',
    'EnhancedInput', 'MappingContext', 'InputAction',
    'DrawText', 'DrawRect', 'DrawLine', 'AddMessage', 'ConsoleCommand',
    'SetTimer', 'GetWorldTime', 'KillZ', 'DestroyActor',
    'SpawnActor', 'SetPaused', 'OpenLevel', 'GetGameplayStatics',
    'SetVisibility', 'SetHiddenInGame', 'SetScalarParameterValueOnMaterials',
    'SetMaterial', 'SetStaticMesh', 'SetCollisionEnabled', 'SetMobility',
    'Length', 'Empty', 'Append', 'Contains', 'Get', 'Set', 'Remove',
    'Conv_IntToString', 'Conv_BoolToString', 'Format', 'Trim', 'LeftChop',
    'Select', 'IsEmpty', 'EqualEqual_StrStr', 'EqualEqual',
    'Dot', 'VectorDistance', 'Normalize', 'VInterpTo', 'SetActorLocationAndRotation',
    'ControllerYaw', 'AddController', 'FOV', 'FieldOfView',
    'Widget', 'Viewport', 'Cursor', 'Focus',
    'BlueprintImplementableEvent', 'CallFunction', 'Self',
    'Random', 'LineTraceSingleByChannel', 'CapsuleTrace',
    'SetCollisionResponseToChannel', 'SetGenerateOverlapEvents',
    'SetSimulatePhysics', 'SetMobility',
    'GameplayStatics|GetPlayerController', 'Utility', 'Utilities|',
    'Matinee', 'Timeline', 'Sequence', 'LevelSequence',
    'GetDateTime', 'ToSeconds',
    'SaveGame', 'PlayerState', 'Save',
    'DataTable', 'PrimaryDataAsset', 'AssetManager',
    'GetName', 'GetClass', 'IsA', 'ClassIsChildOf',
    'SoundMixBlueprint', 'Submix', 'Reverb',
    'StaticMeshActor', 'PointLight', 'SpotLight', 'ExponentialHeightFog', 'SkyLight',
    'LevelScript', 'LevelBlueprint', 'Teleport',
    'Start', 'Stop', 'Pause', 'Resume', 'End',
    'Turn', 'Look', 'Interact', 'Use', 'Press',
]


def matched_pins(graph, allids, keywords, cap=4):
    low = [(i, i.lower()) for i in allids]
    chosen = []
    for kw in keywords:
        k = kw.lower()
        hits = [i for i, il in low if k in il]
        for h in hits[:cap]:
            if h not in chosen:
                chosen.append(h)
    return chosen


def dump_template_components():
    from editor_toolset.toolsets import actor as ACT
    from editor_toolset.toolsets import blueprint as BP
    p('')
    p('=== 5. First Person template component trees ===')
    for path in ('/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter',
                 '/Game/FirstPerson/Blueprints/BP_FirstPersonPlayerController',
                 '/Game/FirstPerson/Blueprints/BP_FirstPersonCameraManager',
                 '/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode'):
        bp = unreal.load_asset(path)
        if bp is None:
            p('  %s MISSING' % path)
            continue
        cdo = BP.BlueprintTools.get_default_object(bp)
        p('--- %s  (cdo=%s)' % (path, cdo.get_class().get_name()))
        for c in guard('components ' + path, lambda: ACT.ActorTools.get_components(cdo)) or []:
            try:
                rel = c.get_editor_property('relative_location')
                rot = c.get_editor_property('relative_rotation')
                att = c.get_attach_parent()
                p('    %-28s %-34s rel=%s rot=%s parent=%s'
                  % (c.get_name(), c.get_class().get_name(),
                     rel, rot, att.get_name() if att else '-'))
            except Exception as exc:
                p('    %-28s %-34s (%r)' % (c.get_name(), c.get_class().get_name(), exc))
        # input action bindings still declared on the character
        if 'Character' in path:
            p('  -- declared input action bindings on the class defaults --')
            for pname in ('input_action_bindings', 'input_axis_bindings'):
                try:
                    arr = cdo.get_editor_property(pname) if hasattr(cdo, 'get_editor_property') else None
                    p('     %s = %s' % (pname, arr))
                except Exception as exc:
                    p('     %s : %r' % (pname, exc))


def main():
    from editor_toolset.toolsets import blueprint as BP
    p('python %s' % sys.version.replace('\n', ' '))
    p('ue %s' % unreal.SystemLibrary.get_engine_version())

    p('')
    p('=== 1. Input asset factories ===')
    for nm in sorted(n for n in dir(unreal) if re.search(
            r'Input.*Factory|Factory.*Input|InputAction|InputMappingContext|EnhancedInput', n)):
        p('  unreal.%-42s %s' % (nm, type(getattr(unreal, nm)).__name__))
    for cls_name in ('InputAction', 'InputMappingContext', 'InputActionFactory',
                     'InputMappingContextFactory', 'InputActionFactoryNew',
                     'InputMappingContextFactoryNew', 'EnhancedInputUserSettings',
                     'BlueprintInterfaceFactory', 'InterfaceFactory', 'Interface'):
        p('  has %-34s %s' % (cls_name, hasattr(unreal, cls_name)))
    ia = guard('InputMappingContext class', lambda: unreal.load_class(
        None, '/Script/EnhancedInput.InputMappingContext'))
    p('  /Script/EnhancedInput.InputMappingContext -> %s' % (ia.get_name() if ia else None))
    iact = guard('InputAction class', lambda: unreal.load_class(
        None, '/Script/EnhancedInput.InputAction'))
    p('  /Script/EnhancedInput.InputAction -> %s' % (iact.get_name() if iact else None))
    if iact:
        p('  InputAction props: %s' % sorted(
            x.lower() for x in dir(iact) if not x.startswith('_'))[:60])
    if ia:
        p('  IMC methods: %s' % sorted(
            x for x in dir(ia) if not x.startswith('_')))
    p('  unreal.InputAction: %s' % (sorted(x for x in dir(unreal.InputAction)
                                          if not x.startswith('_')) if hasattr(unreal, 'InputAction') else 'n/a'))
    p('  unreal.InputMappingContext: %s'
      % (sorted(x for x in dir(unreal.InputMappingContext) if not x.startswith('_'))
         if hasattr(unreal, 'InputMappingContext') else 'n/a'))
    p('  unreal.EnhancedInputKey: %s'
      % (sorted(x for x in dir(unreal.EnhancedInputKey) if not x.startswith('_'))
         if hasattr(unreal, 'EnhancedInputKey') else 'n/a'))
    p('  unreal.InputMappingContextInfo: %s'
      % (sorted(x for x in dir(unreal.InputMappingContextInfo) if not x.startswith('_'))
         if hasattr(unreal, 'InputMappingContextInfo') else 'n/a'))
    p('  unreal.Key: %s' % hasattr(unreal, 'Key'))
    if hasattr(unreal, 'Key'):
        p('  unreal.Key members: %s' % sorted(x for x in dir(unreal.Key) if not x.startswith('_')))
    p('  unreal.InputKey: %s' % hasattr(unreal, 'InputKey'))
    if hasattr(unreal, 'InputKey'):
        p('  unreal.InputKey members: %s' % sorted(
            x for x in dir(unreal.InputKey) if not x.startswith('_')))
    p('  unreal.InputActionKeyMapping: %s' % sorted(
        x for x in dir(unreal.InputActionKeyMapping) if not x.startswith('_')))
    p('  unreal.InputActionValueType members: %s' % [
        m for m in dir(unreal.InputActionValueType) if not m.startswith('_')])
    p('  unreal.InputAction_Factory doc: %s' % unreal.InputAction_Factory.__doc__)
    p('  unreal.InputMappingContext_Factory doc: %s' % unreal.InputMappingContext_Factory.__doc__)
    p('  unreal.map_key doc: %s' % unreal.InputMappingContext.map_key.__doc__)
    p('  unreal.BlueprintInterfaceFactory: %s  doc=%s'
      % (hasattr(unreal, 'BlueprintInterfaceFactory'),
         getattr(unreal, 'BlueprintInterfaceFactory').__doc__))

    # prove an InputAction + IMC can be authored from Python
    p('  -- authoring test --')
    try:
        at = unreal.AssetToolsHelpers.get_asset_tools()
        eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
        eas.make_directory('/Game/KhoangLang/Input')
        ia_path = '/Game/KhoangLang/Input/TMP11_IA_Test'
        if unreal.load_asset(ia_path):
            unreal.EditorAssetLibrary.delete_asset(ia_path)
        act = at.create_asset('TMP11_IA_Test', '/Game/KhoangLang/Input',
                              unreal.InputAction, unreal.InputAction_Factory())
        p('  created InputAction: %s' % act)
        act.set_editor_property('value_type', unreal.InputActionValueType.BOOLEAN)
        imc_path = '/Game/KhoangLang/Input/TMP11_IMC_Test'
        if unreal.load_asset(imc_path):
            unreal.EditorAssetLibrary.delete_asset(imc_path)
        imc = at.create_asset('TMP11_IMC_Test', '/Game/KhoangLang/Input',
                              unreal.InputMappingContext, unreal.InputMappingContext_Factory())
        p('  created IMC: %s' % imc)
        key = unreal.Key('E')
        p('  unreal.Key("E") -> %r' % (key,))
        imc.map_key(key, act)
        imc.map_key(unreal.Key('Q'), act)
        p('  mappings after map_key: %s' % [(str(m.key), m.action.get_name())
                                             for m in imc.get_editor_property('mappings')])
        eas.save_directory('/Game/KhoangLang/Input', only_if_is_dirty=False, recursive=True)
        p('  saved. reload check: %s'
          % [(str(m.key), m.action.get_name()) for m in
             unreal.load_asset(imc_path).get_editor_property('mappings')])
    except Exception as exc:
        p('  !! authoring test failed: %r' % (exc,))
        p(traceback.format_exc())

    p('')
    p('=== 2. Engine fonts ===')
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    for a in sorted(ar.get_assets_by_path('/Engine/EngineFonts', recursive=True),
                    key=lambda x: str(x.package_name)):
        p('  %-56s %s' % (a.package_name, a.asset_class_path.asset_name))
    p('  RobotoDistanceField loaded: %s'
      % bool(unreal.load_asset('/Engine/EngineFonts/RobotoDistanceField')))
    for cand in ('/Engine/EngineFonts/RobotoRegular', '/Engine/EngineFonts/RobotoBold',
                 '/Engine/EngineFonts/LegacyRuntime', '/Engine/EngineFonts/DroidSansFallback'):
        p('  %-46s %s' % (cand, 'OK' if unreal.load_asset(cand) else 'MISSING'))

    p('')
    p('=== 3/4. graph contexts: node id lists + pin dumps ===')
    contexts = [
        ('Actor', unreal.Actor, 'BP_KL_Interactable'),
        ('Character', unreal.Character, 'BP_KL_Interactable'),
        ('PlayerController', unreal.PlayerController, 'BP_KL_Interactable'),
        ('HUD', unreal.HUD, 'BP_KL_Interactable'),
        ('DataAsset', unreal.DataAsset, 'BP_KL_Interactable'),
        ('GameModeBase', unreal.GameModeBase, 'BP_KL_Interactable'),
    ]
    for tag, parent, folder in contexts:
        bp = BP.BlueprintTools.create('/Game/KhoangLang/Data', 'TMP11_' + tag, parent.static_class())
        g = BP.BlueprintTools.list_graphs(bp)[0]
        allids = dump_nodes(bp, g, tag)
        picks = matched_pins(g, allids, KEYWORDS, cap=3)
        pin_dump(g, picks, tag)
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP11_' + tag)

    p('')
    p('=== 6. level / actor APIs ===')
    p('  unreal.LevelEditorSubsystem: %s' % hasattr(unreal, 'LevelEditorSubsystem'))
    if hasattr(unreal, 'LevelEditorSubsystem'):
        p('  LevelEditorSubsystem methods: %s' % sorted(
            x for x in dir(unreal.LevelEditorSubsystem) if not x.startswith('_')))
    p('  unreal.EditorActorSubsystem: %s' % hasattr(unreal, 'EditorActorSubsystem'))
    if hasattr(unreal, 'EditorActorSubsystem'):
        p('  EditorActorSubsystem methods: %s' % sorted(
            x for x in dir(unreal.EditorActorSubsystem) if not x.startswith('_')))
    p('  unreal.EditorLevelUtils: %s' % hasattr(unreal, 'EditorLevelUtils'))
    p('  unreal.StaticMeshActor: %s' % hasattr(unreal, 'StaticMeshActor'))
    for nm in ('PointLight', 'SpotLight', 'DirectionalLight', 'SkyLight',
               'ExponentialHeightFog', 'PlayerStart', 'BoxTrigger', 'Volume',
               'SoundActor', 'AmbientSound', 'LevelInstance'):
        p('  actor class %-22s %s' % (nm, hasattr(unreal, nm)))
    p('  unreal.SpotLightComponent: %s  unreal.PointLightComponent: %s'
      % (hasattr(unreal, 'SpotLightComponent'), hasattr(unreal, 'PointLightComponent')))
    p('  unreal.SoundMix: %s  unreal.SoundMixBlueprint: %s'
      % (hasattr(unreal, 'SoundMix'), hasattr(unreal, 'SoundMixBlueprint')))
    p('  unreal.SoundAttenuation: %s' % hasattr(unreal, 'SoundAttenuation'))
    p('  unreal.AudioComponent: %s' % hasattr(unreal, 'AudioComponent'))
    if hasattr(unreal, 'AudioComponent'):
        p('  AudioComponent setters: %s' % sorted(
            x for x in dir(unreal.AudioComponent) if x.startswith('set_')))

    p('')
    p('=== 7. HUD API ===')
    if hasattr(unreal, 'HUD'):
        p('  unreal.HUD methods: %s' % sorted(
            x for x in dir(unreal.HUD) if not x.startswith('_')))

    p('')
    p('=== 8. DataAsset / PrimaryDataAsset ===')
    p('  unreal.PrimaryDataAsset: %s' % hasattr(unreal, 'PrimaryDataAsset'))
    p('  unreal.DataAssetFactory: %s' % hasattr(unreal, 'DataAssetFactory'))

    dump_template_components()

    p('')
    p('=== 9. existing /Game content state ===')
    for a in sorted(ar.get_assets_by_path('/Game', recursive=True),
                    key=lambda x: str(x.package_name)):
        p('  %-58s %s' % (a.package_name, a.asset_class_path.asset_name))

    p('PROBE11_DONE')


try:
    rep = os.path.join(OUT_DIR, 'report.txt')
    if os.path.exists(rep):
        os.remove(rep)
    main()
except Exception:
    p(traceback.format_exc())
    p('PROBE11_FAILED')
