"""Art pass probe 50: what does this editor/project actually support?

Answers the questions that decide the whole art pass:
  * what surface detail is reachable through materials
  * what mesh / texture / font libraries exist
  * is UMG constructible from Python
  * can screenshots be taken
  * what the current renderer, fog and GI settings are
"""

import os
import sys
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
if HERE not in sys.path:
    sys.path.insert(0, HERE)

OUT = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\art50'
os.makedirs(OUT, exist_ok=True)
L = []


def p(m=''):
    line = str(m)
    L.append(line)
    unreal.log('A50: ' + line)
    with open(os.path.join(OUT, 'report.txt'), 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def main():
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)

    p('=== A. MaterialEditingLibrary surface ===')
    mel = unreal.MaterialEditingLibrary
    p('  functions: %s' % sorted(m for m in dir(mel) if not m.startswith('_')))

    p('')
    p('=== B. engine material parameters (can I drive PBR?) ===')
    mel = unreal.MaterialEditingLibrary
    cands = [
        '/Engine/BasicShapes/BasicShapeMaterial',
        '/Engine/EngineMaterials/DefaultMaterial',
        '/Engine/EngineMaterials/DefaultDiffuse',
        '/Engine/EngineMaterials/DefaultPostProcess',
        '/Engine/EngineMaterials/WorldGridMaterial',
        '/Engine/EngineMaterials/DeferredDecalDefaultMaterial',
        '/Engine/EditorMaterials/EditorMaterial',
        '/Engine/EngineMaterials/PhysicalMaterial',
        '/Engine/EngineMaterials/DefaultPhysicalMaterial',
    ]
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    extra = []
    for path in ('/Engine/EngineMaterials', '/Engine/EditorMaterials',
                 '/Engine/EngineResources', '/Engine/BasicShapes',
                 '/Engine/EditorMeshes', '/Engine/EngineMeshes'):
        try:
            for a in ar.get_assets_by_path(unreal.Name(path), True, False):
                extra.append(str(a.get_object_path()).split('.')[0])
        except Exception as exc:
            p('  registry %s: %r' % (path, exc))
    cands = cands + sorted(set(extra))
    seen = set()
    for path in cands:
        if path in seen:
            continue
        seen.add(path)
        a = unreal.load_asset(path)
        if a is None:
            continue
        cn = a.get_class().get_name()
        if cn not in ('Material', 'MaterialInstanceConstant'):
            continue
        try:
            scalars = [str(x) for x in mel.get_scalar_parameter_names(a)]
            vecs = [str(x) for x in mel.get_vector_parameter_names(a)]
            texs = [str(x) for x in mel.get_texture_parameter_names(a)]
        except Exception as exc:
            p('  %-62s params raised %r' % (path, exc))
            continue
        p('  %-62s scalar=%s vector=%s texture=%s' % (path, scalars, vecs, texs))

    p('')
    p('=== C. static meshes available ===')
    meshes = {}
    for path in ('/Engine/BasicShapes', '/Engine/EngineMeshes', '/Engine/EditorMeshes',
                 '/Engine/EngineResources', '/Game'):
        try:
            for a in ar.get_assets_by_path(unreal.Name(path), True, False):
                fp = str(a.get_object_path()).split('.')[0]
                if a.get_class().get_name() == 'StaticMesh':
                    meshes[fp] = a
        except Exception:
            pass
    for k in sorted(meshes):
        p('  %-64s tris=%s' % (k, meshes[k].get_editor_property('static_materials') and ''))
    p('  total static meshes found: %d' % len(meshes))

    p('')
    p('=== D. fonts ===')
    fonts = {}
    for path in ('/Engine/EngineFonts', '/Engine/Slate/Fonts', '/Engine/Fonts',
                 '/Game'):
        try:
            for a in ar.get_assets_by_path(unreal.Name(path), True, False):
                fp = str(a.get_object_path()).split('.')[0]
                if a.get_class().get_name() in ('Font', 'CompositeFont', 'FontFace'):
                    fonts[fp] = a
        except Exception:
            pass
    for k in sorted(fonts):
        p('  %-60s [%s]' % (k, fonts[k].get_class().get_name()))

    p('')
    p('=== E. UMG / widgets constructible from python? ===')
    for n in ('WidgetBlueprint', 'WidgetBlueprintFactory', 'WidgetBlueprintGeneratedClass',
              'UserWidget', 'WidgetTree', 'CanvasPanel', 'TextBlock', 'Image',
              'Button', 'SizeBox', 'Border', 'Widget', 'CommonUI', 'BlueprintFactory',
              'EditorUtilityWidget', 'WidgetComponent'):
        p('  unreal.%-32s %s' % (n, hasattr(unreal, n)))
    try:
        p('  unreal.WidgetBlueprintFactory members: %s' %
          ([m for m in dir(unreal.WidgetBlueprintFactory) if not m.startswith('_')],))
    except Exception as exc:
        p('  WidgetBlueprintFactory unavailable: %r' % (exc,))
    p('  UnrealEdLibrary members: %s' % (
        [m for m in dir(unreal.UnrealEdSubsystem) if not m.startswith('_')],))
    try:
        p('  EditorUtilityLibrary members: %s' % (
            [m for m in dir(unreal.EditorUtilityLibrary) if not m.startswith('_')],))
    except Exception as exc:
        p('  no EditorUtilityLibrary: %r' % (exc,))

    p('')
    p('=== F. screenshot / render capture ===')
    try:
        p('  AutomationLibrary: %s' % ([m for m in dir(unreal.AutomationLibrary)
                                        if not m.startswith('_')],))
    except Exception as exc:
        p('  no AutomationLibrary: %r' % (exc,))
    for n in ('EditorLevelLibrary', 'AutomationLibrary', 'EditorAssetLibrary',
              'TextureRenderTarget2D', 'Canvas', 'WidgetLayoutLibrary'):
        p('  unreal.%-28s %s' % (n, hasattr(unreal, n)))

    p('')
    p('=== G. post process / fog / GI config ===')
    gvars = unreal.SystemLibrary.get_engine_version()
    p('  engine: %s' % gvars)
    for cvar in ('r.DynamicGlobalIlluminationMethod', 'r.ReflectionMethod',
                 'r.Shadow.Virtual.Enable', 'r.VolumetricFog', 'r.DefaultFeature.MotionBlur',
                 'r.SkinCache.CompileShaders', 'r.GenerateMeshDistanceFields',
                 'r.Nanite', 'r.AntiAliasingMethod', 'r.DefaultFeature.AutoExposure',
                 'r.Lumen.HardwareRayTracing', 'r.Shadow.MaxResolution',
                 'r.Shadow.MaxCascades', 'r.GBufferFormat'):
        try:
            p('  %-42s = %r' % (cvar, unreal.SystemLibrary.get_console_variable_string_value(cvar)))
        except Exception as exc:
            p('  %-42s : %r' % (cvar, exc))

    p('')
    p('=== H. current prototype level art state ===')
    if not unreal.EditorLevelLibrary.load_level('/Game/KhoangLang/Maps/Lvl_KL_School3'):
        p('  FAILED to load level')
        return
    world = unreal.EditorLevelLibrary.get_editor_world()
    from editor_toolset.toolsets import actor as ACT
    acts = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    p('  actors: %d' % len(acts))
    mats = {}
    lights = []
    for a in acts:
        cn = a.get_class().get_name()
        for c in ACT.ActorTools.get_components(a):
            cc = c.get_class().get_name()
            if cc == 'StaticMeshComponent':
                sm = c.get_editor_property('static_mesh')
                ov = c.get_editor_property('override_materials')
                for o in ov:
                    if o:
                        mats.setdefault(o.get_name(), 0)
                        mats[o.get_name()] += 1
                p('  MESH %-22s mesh=%-12s scale=%s mats=%s' % (
                    a.get_name(), sm.get_name() if sm else 'None',
                    [round(v, 2) for v in c.get_editor_property('relative_scale3d')],
                    [o.get_name() if o else 'None' for o in ov]))
            if 'LightComponent' in cc:
                lights.append((a.get_name(), cc, c.get_editor_property('intensity'),
                               tuple(round(v, 2) for v in
                                     (c.get_editor_property('light_color').r,
                                      c.get_editor_property('light_color').g,
                                      c.get_editor_property('light_color').b)),
                               c.get_editor_property('cast_shadows')))
    p('  material usage: %s' % sorted(mats.items(), key=lambda x: -x[1]))
    p('  lights:')
    for l in lights:
        p('    %-26s %-22s int=%-8s col=%s shadows=%s' % l)
    p('  volume/atmosphere components:')
    for a in acts:
        for c in ACT.ActorTools.get_components(a):
            cn = c.get_class().get_name()
            if 'Fog' in cn or 'Sky' in cn or 'PostProcess' in cn or 'Audio' in cn:
                p('    %-26s %s' % (a.get_name(), cn))
    ws = world.get_world_settings()
    for prop in ('default_fog_mode', 'kill_z', 'default_ambient_occlusion'):
        try:
            p('  WorldSettings %s = %r' % (prop, ws.get_editor_property(prop)))
        except Exception as exc:
            p('  WorldSettings %s : %r' % (prop, exc))
    p('DONE')


try:
    rep = os.path.join(OUT, 'report.txt')
    if os.path.exists(rep):
        os.remove(rep)
    main()
except Exception:
    p(traceback.format_exc())
    p('A50_FATAL')
