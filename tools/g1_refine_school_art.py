"""Refine only the isolated G1 school's copied materials and lighting.

Run via ue_live.py with PIE stopped AFTER staging the school. This never
modifies source meshes, textures, source materials or other maps. Execution
produces engineering evidence, not an art or performance acceptance claim.
All textures are the project's authored art_tex.py assets; no external assets.
"""
import hashlib
import json
import math
from pathlib import Path
import unreal
from editor_toolset.toolsets.material import MaterialTools

ROOT = Path(unreal.Paths.project_dir())
BASE = '/Game/KhoangLang/Production/G1Canon'
MAP = BASE + '/Lvl_KL_SchoolSlice'
FOLDER = BASE + '/Materials'
SOURCE_MASTER = '/Game/KhoangLang/Production/Materials/M_KL_ART_Surface'
MASTER = FOLDER + '/M_KL_G1_Surface'
MEL = unreal.MaterialEditingLibrary
PIN_BINDINGS = []
# Initial corrective candidate after actual G1_refined_deck.png showed severe
# clipping at +1 EV. This is deliberately exposed for the editor owner's
# measured -3/-4 EV comparison; it is NOT an accepted visual calibration.
# Physical-camera exposure remains disabled, so the installed renderer applies
# compensation as 2**bias. +1 -> -3 is a sixteen-fold exposure reduction.
EXPOSURE_BIAS_EV = -3.0

# Intensity is explicitly lumens for local lights. These are starting values,
# not measured lighting qualification; screenshots and frame times decide.
LIGHTS = {
    'ART_L_Corr': (1050, 620, (.84, .89, 1.0), True),
    'ART_L_Hall0': (1250, 680, (1.0, .93, .82), True),
    'ART_L_Hall1': (950, 650, (1.0, .92, .81), True),
    'ART_L_Hall2': (700, 580, (1.0, .91, .80), True),
    'ART_L_Door': (140, 360, (1.0, .93, .84), False),
    'ART_L_Room0': (1450, 760, (1.0, .93, .83), True),
    'ART_L_Room1': (1150, 740, (1.0, .93, .83), True),
    'ART_L_Shaft0': (900, 1600, (.76, .83, 1.0), True),
    'ART_L_Shaft1': (900, 1600, (.76, .83, 1.0), True),
    'ART_L_ShaftCorr': (380, 900, (.78, .85, 1.0), True),
    'ART_L_CornerHint': (0, 300, (.78, .85, 1.0), False),
}


def save(asset):
    if not unreal.EditorAssetLibrary.save_loaded_asset(asset, False):
        raise RuntimeError('Could not save ' + asset.get_path_name())


def copied(asset, target):
    if not target.startswith(FOLDER + '/'):
        raise RuntimeError('Material destination outside isolated namespace')
    result = (unreal.load_asset(target)
              if unreal.EditorAssetLibrary.does_asset_exist(target)
              else unreal.EditorAssetLibrary.duplicate_asset(
                  asset.get_path_name().split('.')[0], target))
    if result is None:
        raise RuntimeError('Material copy failed: ' + target)
    result.modify()
    return result


def build_master():
    source = unreal.load_asset(SOURCE_MASTER)
    if not isinstance(source, unreal.Material):
        raise RuntimeError('Missing repaired production master')
    mat = copied(source, MASTER)
    # This graph is replaced only in OUR material copy, not in the source.
    MEL.delete_all_material_expressions(mat)

    def node(cls, **properties):
        result = MEL.create_material_expression(mat, cls)
        if result is None:
            raise RuntimeError('Expression creation failed: ' + cls.__name__)
        for key, value in properties.items():
            result.set_editor_property(key, value)
        return result

    def wire(src, dest, pin, output=''):
        # UE's expression INPUT property name is not always its graph pin
        # name. The installed MaterialEditingLibrary.cpp resolves shortened
        # GetInputName() values. Unary expressions can report FName None,
        # displayed by Python as 'None'; the native API accepts '' as input 0.
        declared = [str(value) for value in
                    MEL.get_material_expression_input_names(dest)]
        matches = [name for name in declared if name.casefold() == pin.casefold()]
        if len(matches) == 1:
            resolved = matches[0]
        elif len(declared) == 1 and pin in ('Input', 'VectorInput'):
            resolved = declared[0]
        else:
            raise RuntimeError('Cannot resolve ' + dest.get_class().get_name()
                               + '.' + pin + '; native pins=' + repr(declared))
        if resolved in ('None', ''):
            resolved = ''
        if not MEL.connect_material_expressions(src, output, dest, resolved):
            raise RuntimeError('Graph connection rejected: '
                               + dest.get_class().get_name() + '.' + pin
                               + ' -> ' + repr(resolved))
        PIN_BINDINGS.append({'expression': dest.get_class().get_name(),
                             'requested': pin, 'native': resolved,
                             'declared': declared})

    def scalar(name, value):
        return node(unreal.MaterialExpressionScalarParameter,
                    parameter_name=name, default_value=float(value))

    def vector(name, rgb):
        return node(unreal.MaterialExpressionVectorParameter,
                    parameter_name=name,
                    default_value=unreal.LinearColor(*rgb, 1.0))

    def mask(source_node, channels):
        result = node(unreal.MaterialExpressionComponentMask,
                      r='r' in channels, g='g' in channels,
                      b='b' in channels, a=False)
        wire(source_node, result, 'Input')
        return result

    def binary(cls, a, b):
        result = node(cls)
        wire(a, result, 'A')
        wire(b, result, 'B')
        return result

    def lerp(a, b, alpha):
        result = node(unreal.MaterialExpressionLinearInterpolate)
        wire(a, result, 'A')
        wire(b, result, 'B')
        wire(alpha, result, 'Alpha')
        return result

    def output(src, prop, channel=''):
        if not MEL.connect_material_property(src, channel, prop):
            raise RuntimeError('Material property connection failed')

    uv = node(unreal.MaterialExpressionTextureCoordinate)
    wp = node(unreal.MaterialExpressionWorldPosition)
    normal_ws = node(unreal.MaterialExpressionVertexNormalWS)
    abs_normal = node(unreal.MaterialExpressionAbs)
    wire(normal_ws, abs_normal, 'Input')
    # Architectural faces are axis-aligned before object rotation. Select
    # dominant world plane using vertex normals so UV scale stays centimetres.
    nx = mask(abs_normal, 'r')
    nz = mask(abs_normal, 'b')
    yz, xz, xy = (mask(wp, channels) for channels in ('gb', 'rb', 'rg'))
    wall_projection = lerp(xz, yz, nx)
    world_uv = binary(unreal.MaterialExpressionDivide,
                      lerp(wall_projection, xy, nz),
                      scalar('SurfaceSizeCm', 150))
    mixed_uv = lerp(uv, world_uv, scalar('UseWorldUV', 0))
    detail_uv = binary(unreal.MaterialExpressionMultiply,
                       mixed_uv, scalar('DetailTiling', 1))
    grunge_uv = binary(unreal.MaterialExpressionMultiply,
                       mixed_uv, scalar('GrungeTiling', .24))

    def texture(name, family, suffix, tex_uv, is_normal=False):
        source_texture = unreal.load_asset(
            '/Game/KhoangLang/TexturesArt/T_ART_' + family + '_' + suffix)
        if source_texture is None:
            raise RuntimeError('Missing authored texture: ' + name)
        sample = node(unreal.MaterialExpressionTextureSampleParameter2D,
                      parameter_name=name, texture=source_texture)
        if is_normal:
            sample.set_editor_property('sampler_type',
                unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        wire(tex_uv, sample, 'UVs')
        return sample

    albedo = texture('Detail', 'Plaster', 'A', detail_uv)
    rough_texture = texture('DetailRough', 'Plaster', 'R', detail_uv)
    grunge = texture('Grunge', 'Grunge', 'A', grunge_uv)
    tangent_normal = texture('NormalMap', 'Plaster', 'N', detail_uv, True)
    # Damp staining is restrained and asymmetric in height, and never masks
    # printed evidence. Existing material instances retain their source tints.
    height = binary(unreal.MaterialExpressionDivide, mask(wp, 'b'),
                    scalar('DampHeightCm', 115))
    inverse_height = node(unreal.MaterialExpressionOneMinus)
    wire(height, inverse_height, 'Input')
    bounded_height = node(unreal.MaterialExpressionSaturate)
    wire(inverse_height, bounded_height, 'Input')
    damp = binary(unreal.MaterialExpressionMultiply, bounded_height,
                  scalar('DirtAmount', .30))
    paint = lerp(vector('BaseTint', (.62, .57, .43)),
                 vector('DirtTint', (.29, .27, .22)), damp)
    white = node(unreal.MaterialExpressionConstant3Vector,
                 constant=unreal.LinearColor(1, 1, 1, 1))
    detail_variation = lerp(white, albedo, scalar('DetailAmount', .35))
    dirt_variation = lerp(white, grunge, scalar('GrungeAmount', .12))
    output(binary(unreal.MaterialExpressionMultiply,
                  binary(unreal.MaterialExpressionMultiply,
                         paint, detail_variation), dirt_variation),
           unreal.MaterialProperty.MP_BASE_COLOR)
    texture_r = mask(rough_texture, 'r')
    rough_variation = lerp(scalar('RoughnessFloor', .70),
                          texture_r, scalar('RoughnessVariation', .16))
    rough = binary(unreal.MaterialExpressionMultiply,
                   rough_variation, scalar('Roughness', 1))
    output(rough, unreal.MaterialProperty.MP_ROUGHNESS)
    # Multiplying all three normal channels by strength does not flatten a
    # normal. Lerp from the tangent-space flat normal, then normalize instead.
    # World-projected plaster uses a flat normal until a correct rotated TBN
    # projection is authored; it must not claim nonexistent surface relief.
    flat = node(unreal.MaterialExpressionConstant3Vector,
                constant=unreal.LinearColor(0, 0, 1, 1))
    flattened = lerp(flat, tangent_normal, scalar('NormalStrength', .16))
    normalized = node(unreal.MaterialExpressionNormalize)
    wire(flattened, normalized, 'VectorInput')
    output(normalized, unreal.MaterialProperty.MP_NORMAL)
    output(scalar('Specular', .28), unreal.MaterialProperty.MP_SPECULAR)
    MEL.layout_material_expressions(mat)
    MaterialTools.recompile(mat)  # Native helper raises on shader errors.
    save(mat)
    return mat


def main():
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if editor.get_game_world():
        raise RuntimeError('Stop PIE before refining school art')
    world = editor.get_editor_world()
    if world is None or world.get_path_name().split('.')[0] != MAP:
        raise RuntimeError('Load the isolated G1 school map first')
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor_list = list(actors.get_all_level_actors())
    labels = {a.get_actor_label(): a for a in actor_list}
    missing = set(LIGHTS) - set(labels)
    if missing:
        raise RuntimeError('Unexpected school lighting layout: ' + str(missing))
    # Reject existing invalid transforms instead of propagating them silently.
    for a in actor_list:
        scale = a.get_actor_scale3d()
        if min(abs(scale.x), abs(scale.y), abs(scale.z)) < .0001:
            raise RuntimeError('Zero-scale actor requires separate repair: '
                               + a.get_actor_label())
    unreal.EditorAssetLibrary.make_directory(FOLDER)
    master = build_master()
    world.modify()
    report = {'map': MAP, 'materials': [], 'overrides': [], 'lights': [],
              'provenance': 'Project-authored art_tex.py and existing materials',
              'visual_accepted': False, 'packaged_performance_qualified': False,
              'source_script_sha256': hashlib.sha256(
                  Path(__file__).read_bytes()).hexdigest()}
    report['native_pin_bindings'] = PIN_BINDINGS
    adopted = {}

    def adopt(material):
        if material is None:
            return None
        path = material.get_path_name().split('.')[0]
        if path in adopted:
            return adopted[path]
        if path.startswith(FOLDER + '/'):
            return material
        if not isinstance(material, unreal.MaterialInstanceConstant):
            return material
        if not path.startswith(('/Game/KhoangLang/MaterialsArt/',
                                '/Game/KhoangLang/Production/Materials/')):
            return material
        parent = material.get_editor_property('parent')
        if parent is None:
            raise RuntimeError('Instance has no parent: ' + path)
        parent_path = parent.get_path_name().split('.')[0]
        target = FOLDER + '/' + material.get_name()
        instance = copied(material, target)
        adopted[path] = instance
        if isinstance(parent, unreal.MaterialInstanceConstant):
            new_parent = adopt(parent)
        elif parent.get_name() == 'M_KL_ART_Surface':
            new_parent = master
        else:
            new_parent = parent  # Shared source emissive master is read-only.
        MEL.set_material_instance_parent(instance, new_parent)
        MEL.update_material_instance(instance)
        if instance.get_editor_property('parent') != new_parent:
            raise RuntimeError('Native material parent did not take effect: ' + target)
        name = material.get_name().lower()
        scalar_values = {}
        vector_values = {}
        if new_parent == master or isinstance(new_parent, unreal.MaterialInstanceConstant):
            plaster = any(word in name for word in ('wall', 'ceiling', 'concrete'))
            scalar_values.update(UseWorldUV=1.0 if plaster else 0.0,
                                 SurfaceSizeCm=160, NormalStrength=0 if plaster else .16,
                                 DirtAmount=.30 if 'wall' in name else .06,
                                 DetailAmount=.45 if plaster else 1,
                                 GrungeAmount=.14 if plaster else .05,
                                 RoughnessVariation=.18, RoughnessFloor=.72)
            if plaster:
                scalar_values.update(DetailTiling=1, GrungeTiling=.24, Roughness=1)
            if 'ceiling' in name:
                vector_values['BaseTint'] = (.48, .46, .40, 1)
            if 'wallochre' in name:
                vector_values['BaseTint'] = (.60, .55, .40, 1)
            if 'wallclassroom' in name:
                vector_values['BaseTint'] = (.63, .60, .48, 1)
        elif 'emissive' in parent.get_name().lower():
            # Lamp surfaces remain perceptible without becoming white slabs.
            source_strength = MEL.get_material_instance_scalar_parameter_value(
                material, 'EmissiveStrength')
            scalar_values['EmissiveStrength'] = min(source_strength, 1.25)
        scalar_names = {str(value) for value in MEL.get_scalar_parameter_names(instance)}
        vector_names = {str(value) for value in MEL.get_vector_parameter_names(instance)}
        readbacks = {}
        for key, value in scalar_values.items():
            if key not in scalar_names:
                raise RuntimeError('Missing material parameter: ' + key)
            # Installed UE5.8 MaterialEditingLibrary.cpp writes the scalar,
            # updates the instance, then returns an untouched false flag.
            # Validate actual engine state, never infer failure from that flag.
            MEL.set_material_instance_scalar_parameter_value(instance, key, float(value))
            actual = float(MEL.get_material_instance_scalar_parameter_value(instance, key))
            if not math.isclose(actual, value, rel_tol=1e-6, abs_tol=1e-5):
                raise RuntimeError('Scalar readback mismatch: ' + target + '.' + key
                                   + ' requested=' + str(value) + ' actual=' + str(actual))
            readbacks[key] = actual
        vector_readbacks = {}
        for key, value in vector_values.items():
            if key not in vector_names:
                raise RuntimeError('Missing material vector parameter: ' + key)
            MEL.set_material_instance_vector_parameter_value(instance, key,
                                                              unreal.LinearColor(*value))
            actual = MEL.get_material_instance_vector_parameter_value(instance, key)
            channels = (actual.r, actual.g, actual.b, actual.a)
            if not all(math.isclose(a, v, rel_tol=1e-6, abs_tol=1e-5)
                       for a, v in zip(channels, value)):
                raise RuntimeError('Vector readback mismatch: ' + target + '.' + key)
            vector_readbacks[key] = list(channels)
        MEL.update_material_instance(instance)
        save(instance)
        report['materials'].append({'source': path, 'copy': target,
                                    'scalar_overrides': scalar_values,
                                    'scalar_readbacks': readbacks,
                                    'vector_overrides': vector_values,
                                    'vector_readbacks': vector_readbacks})
        return instance

    for a in actor_list:
        for component in a.get_components_by_class(unreal.StaticMeshComponent):
            for slot in range(component.get_num_materials()):
                old = component.get_material(slot)
                new = adopt(old)
                if old != new:
                    a.modify()
                    component.modify()
                    component.set_material(slot, new)
                    report['overrides'].append({'actor': a.get_actor_label(),
                                               'slot': slot,
                                               'material': new.get_path_name()})
    for label, (intensity, radius, color, shadows) in LIGHTS.items():
        a = labels[label]
        c = a.get_component_by_class(unreal.LocalLightComponent)
        if c is None:
            raise RuntimeError('Not a local light: ' + label)
        a.modify()
        c.modify()
        before = float(c.get_editor_property('intensity'))
        c.set_editor_property('intensity_units', unreal.LightUnits.LUMENS)
        c.set_editor_property('intensity', float(intensity))
        c.set_editor_property('attenuation_radius', float(radius))
        c.set_editor_property('light_color', unreal.Color(
            r=round(color[0]*255), g=round(color[1]*255),
            b=round(color[2]*255), a=255))
        c.set_editor_property('cast_shadows', shadows)
        if isinstance(c, unreal.PointLightComponent):
            c.set_editor_property('use_inverse_squared_falloff', True)
            c.set_editor_property('source_radius', 7.0)
            c.set_editor_property('soft_source_radius', 16.0)
        report['lights'].append({'actor': label, 'previous_intensity': before,
                                'lumens': intensity, 'radius_cm': radius,
                                'shadows': shadows})
    moon = labels.get('ART_Moon')
    if moon is None:
        raise RuntimeError('Expected authored moon light missing')
    moon.modify()
    moon_component = moon.get_component_by_class(unreal.DirectionalLightComponent)
    moon_component.modify()
    moon_component.set_editor_property('intensity', .12)
    moon_component.set_editor_property('light_color',
        unreal.Color(r=199, g=217, b=255, a=255))
    moon_component.set_editor_property('cast_shadows', True)
    report['lights'].append({'actor': 'ART_Moon', 'lux': .12,
                            'shadows': True})
    # Explicit settings override the inherited grade without rewriting config.
    # Neutral grading leaves the palette to lights and surfaces, not a blue wash.
    grade = labels.get('G1_ArtGrade')
    if grade is None:
        grade = actors.spawn_actor_from_class(unreal.PostProcessVolume,
                                              unreal.Vector(0, 0, 150))
        grade.set_actor_label('G1_ArtGrade')
    grade.modify()
    settings = unreal.PostProcessSettings()
    properties = {
        'auto_exposure_method': unreal.AutoExposureMethod.AEM_MANUAL,
        'auto_exposure_apply_physical_camera_exposure': False,
        'auto_exposure_bias': EXPOSURE_BIAS_EV,
        'color_saturation': unreal.Vector4(1, 1, 1, 1),
        'color_contrast': unreal.Vector4(1, 1, 1, 1),
        'color_gamma': unreal.Vector4(1, 1, 1, 1),
        'color_gain': unreal.Vector4(1, 1, 1, 1),
        'color_offset': unreal.Vector4(0, 0, 0, 0),
        'vignette_intensity': .12, 'bloom_intensity': .12,
        'bloom_threshold': 2.0, 'ambient_occlusion_intensity': .30,
        'ambient_occlusion_radius': 45.0, 'ambient_occlusion_power': 1.0,
        'ambient_occlusion_static_fraction': 0.0,
        'motion_blur_amount': 0.0, 'lens_flare_intensity': 0.0,
        'film_grain_intensity': 0.0,
    }
    override_bindings = {}
    for key, value in properties.items():
        # PythonizePropertyName strips UE's boolean b prefix. Discover the
        # exposed spelling instead of assuming the native C++ field spelling.
        override_key = None
        for candidate in ('override_' + key, 'b_override_' + key):
            try:
                settings.get_editor_property(candidate)
            except Exception:
                continue
            override_key = candidate
            break
        if override_key is None:
            raise RuntimeError('Postprocess override is not exposed: ' + key)
        settings.set_editor_property(override_key, True)
        if not settings.get_editor_property(override_key):
            raise RuntimeError('Postprocess override did not take effect: ' + key)
        settings.set_editor_property(key, value)
        override_bindings[key] = override_key
    grade.set_editor_property('settings', settings)
    grade.set_editor_property('priority', 100.0)
    grade.set_editor_property('unbound', True)
    grade.set_editor_property('blend_weight', 1.0)
    if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAP):
        raise RuntimeError('Refined map save failed')
    report['postprocess'] = {'manual_bias_ev': EXPOSURE_BIAS_EV,
                             'physical_exposure': False,
                             'global_grade': 'neutral', 'ao_intensity': .30,
                             'native_override_bindings': override_bindings}
    target = ROOT / 'docs/agent/EVIDENCE/G1_canonical_art_refine.json'
    target.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'materials': len(report['materials']),
                      'overrides': len(report['overrides']),
                      'lights': len(report['lights']),
                      'visual_accepted': False}))


if __name__ == '__main__':
    main()
