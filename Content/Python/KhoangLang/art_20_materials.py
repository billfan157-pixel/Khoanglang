"""Khoang Lang 02:17 - art pass step 2: master materials and instances.

Two masters are authored from Python through MaterialEditingLibrary:
  M_KL_ART_Surface  - tiling detail + large-scale grunge + world-height dirt
                      gradient, so a flat painted wall reads as an aged,
                      water-marked rural school wall.
  M_KL_ART_Emissive - lamp tubes and indicator lamps.
Every surface in the level is a Material Instance of the first, so the whole
palette stays tunable from one graph.

Run headless:  run_ue_script.ps1 art_20_materials.py
"""

import os
import sys

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import kl_core as K  # noqa: E402
from kl_core import step, ok, warn, fail  # noqa: E402

F_MAT = K.ROOT + '/MaterialsArt'
F_TEX = K.ROOT + '/TexturesArt'
MEL = unreal.MaterialEditingLibrary

MASTER = 'M_KL_ART_Surface'
MASTER_EM = 'M_KL_ART_Emissive'


# --------------------------------------------------------------------------- #
# graph helpers
# --------------------------------------------------------------------------- #

def inputs_of(mat, expr):
    try:
        return list(MEL.get_inputs_for_material_expression(mat, expr))
    except Exception:
        return []


def wire(mat, src, src_out, dst, want):
    """Connect, tolerating the different input names UE reports per node."""
    names = inputs_of(mat, dst)
    candidates = [want]
    if '' not in candidates:
        candidates.append('')
    candidates += [n for n in names if n not in candidates]
    last = None
    for target in candidates:
        try:
            MEL.connect_material_expressions(src, src_out, dst, target)
            return True
        except Exception as exc:
            last = exc
    fail('connect %s.%s -> %s: %r' % (src.get_class().get_name(), src_out,
                                       dst.get_class().get_name(), str(last)[:70]))
    return False


def prop(mat, expr, out, material_property):
    try:
        return MEL.connect_material_property(expr, out, material_property)
    except Exception as exc:
        fail('connect_material_property %s: %r' % (material_property, exc))
        return False


def vec_param(E, x, y, name, default):
    n = E(unreal.MaterialExpressionVectorParameter, x, y)
    n.set_editor_property('parameter_name', name)
    n.set_editor_property('default_value', unreal.LinearColor(*default))
    return n


def sca_param(E, x, y, name, default):
    n = E(unreal.MaterialExpressionScalarParameter, x, y)
    n.set_editor_property('parameter_name', name)
    n.set_editor_property('default_value', float(default))
    return n


def tex_param(E, x, y, name, normal=False):
    n = E(unreal.MaterialExpressionTextureSampleParameter2D, x, y)
    n.set_editor_property('parameter_name', name)
    if normal:
        try:
            n.set_editor_property('sampler_type',
                                  unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        except Exception as exc:
            warn('sampler_type: %r' % (str(exc)[:60],))
    return n


def const(E, x, y, r):
    n = E(unreal.MaterialExpressionConstant, x, y)
    n.set_editor_property('r', float(r))
    return n


def absolute_world_position(mat, E):
    """WorldPosition forced to absolute (no shader offset), so a wall's dirt
    gradient is measured from the real floor level, not from the object."""
    wp = E(unreal.MaterialExpressionWorldPosition, -2600, 300)
    enum = None
    for attr in dir(unreal):
        if 'WorldPosition' in attr and 'Offset' in attr:
            enum = getattr(unreal, attr)
            break
    applied = False
    if enum is not None:
        for member in dir(enum):
            if 'ABSOLUTE' in member.upper():
                try:
                    wp.set_editor_property('world_position_shader_offset',
                                           getattr(enum, member))
                    applied = True
                    break
                except Exception:
                    continue
    if not applied:
        warn('absolute world position not applied; using shader offset as-is')
    mask = E(unreal.MaterialExpressionComponentMask, -2400, 300)
    for prop_name, val in (('r', False), ('g', False), ('b', True), ('a', False)):
        try:
            mask.set_editor_property(prop_name, val)
        except Exception:
            pass
    wire(mat, wp, '', mask, '')
    return mask

# --------------------------------------------------------------------------- #
# masters
# --------------------------------------------------------------------------- #

def build_master():
    step('master material %s' % MASTER)
    path = '%s/%s' % (F_MAT, MASTER)
    if unreal.load_asset(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    at = unreal.AssetToolsHelpers.get_asset_tools()
    mat = at.create_asset(MASTER, F_MAT, unreal.Material, unreal.MaterialFactoryNew())
    MEL.delete_all_material_expressions(mat)

    def E(cls, x, y):
        return MEL.create_material_expression(mat, cls, x, y)

    # ---- world height -> 0 at the floor ---------------------------------- #
    mask = absolute_world_position(mat, E)
    inv = E(unreal.MaterialExpressionOneMinus, -2200, 300)
    wire(mat, mask, '', inv, 'Input')
    k1 = const(E, -2200, 480, 1.35)
    hm = E(unreal.MaterialExpressionMultiply, -2000, 320)
    wire(mat, inv, '', hm, 'A')
    wire(mat, k1, '', hm, 'B')
    clampn = E(unreal.MaterialExpressionSaturate, -1850, 320)
    wire(mat, hm, '', clampn, 'Input')

    # ---- tiling coordinates ----------------------------------------------- #
    uv = E(unreal.MaterialExpressionTextureCoordinate, -2600, -200)
    det_scale = sca_param(E, -2600, -420, 'DetailTiling', 1.0)
    det_uv = E(unreal.MaterialExpressionMultiply, -2400, -260)
    wire(mat, uv, '', det_uv, 'A')
    wire(mat, det_scale, '', det_uv, 'B')
    gr_scale = sca_param(E, -2600, -660, 'GrungeTiling', 0.18)
    gr_uv = E(unreal.MaterialExpressionMultiply, -2400, -500)
    wire(mat, uv, '', gr_uv, 'A')
    wire(mat, gr_scale, '', gr_uv, 'B')

    # ---- textures ---------------------------------------------------------- #
    det = tex_param(E, -2200, -260, 'Detail')
    wire(mat, det_uv, '', det, 'UVs')
    det_r = tex_param(E, -2200, -60, 'DetailRough')
    wire(mat, det_uv, '', det_r, 'UVs')
    grunge = tex_param(E, -2200, -520, 'Grunge')
    wire(mat, gr_uv, '', grunge, 'UVs')
    nrm = tex_param(E, -2200, 120, 'NormalMap', normal=True)
    wire(mat, det_uv, '', nrm, 'UVs')

    # ---- base colour: dirt low, paint high, x detail, x grunge -------------- #
    base = vec_param(E, -1900, -900, 'BaseTint', (0.80, 0.71, 0.50, 1.0))
    dirt = vec_param(E, -1900, -1120, 'DirtTint', (0.32, 0.28, 0.21, 1.0))
    dirt_amt = sca_param(E, -1900, -1320, 'DirtAmount', 1.0)
    hm2 = E(unreal.MaterialExpressionMultiply, -2050, -1100)
    wire(mat, clampn, '', hm2, 'A')
    wire(mat, dirt_amt, '', hm2, 'B')
    lerp = E(unreal.MaterialExpressionLinearInterpolate, -1700, -900)
    wire(mat, hm2, '', lerp, 'Alpha')
    wire(mat, dirt, '', lerp, 'A')
    wire(mat, base, '', lerp, 'B')
    m1 = E(unreal.MaterialExpressionMultiply, -1450, -700)
    wire(mat, lerp, '', m1, 'A')
    wire(mat, det, 'RGB', m1, 'B')
    m2 = E(unreal.MaterialExpressionMultiply, -1250, -700)
    wire(mat, m1, '', m2, 'A')
    wire(mat, grunge, 'RGB', m2, 'B')
    prop(mat, m2, '', unreal.MaterialProperty.MP_BASE_COLOR)

    # ---- roughness --------------------------------------------------------- #
    rgh = sca_param(E, -1700, 200, 'Roughness', 0.9)
    rgh_var = vec_param(E, -1700, 40, 'RoughnessTint', (1.0, 1.0, 1.0, 1.0))
    rm = E(unreal.MaterialExpressionMultiply, -1450, 200)
    wire(mat, rgh, '', rm, 'A')
    wire(mat, rgh_var, '', rm, 'B')
    rm2 = E(unreal.MaterialExpressionMultiply, -1250, 200)
    wire(mat, rm, '', rm2, 'A')
    wire(mat, det_r, 'R', rm2, 'B')
    prop(mat, rm2, 'R', unreal.MaterialProperty.MP_ROUGHNESS)

    # ---- normal ------------------------------------------------------------ #
    n_str = sca_param(E, -1700, 500, 'NormalStrength', 1.0)
    nm = E(unreal.MaterialExpressionMultiply, -1450, 480)
    wire(mat, n_str, '', nm, 'A')
    wire(mat, nrm, 'RGB', nm, 'B')
    prop(mat, nm, '', unreal.MaterialProperty.MP_NORMAL)

    # ---- specular / metallic stay default (dielectric) --------------------- #

    MEL.layout_material_expressions(mat)
    MEL.recompile_material(mat)
    ok('%s: %d expressions, vector=%s scalar=%s texture=%s' % (
        MASTER, MEL.get_num_material_expressions(mat),
        sorted(str(x) for x in MEL.get_vector_parameter_names(mat)),
        sorted(str(x) for x in MEL.get_scalar_parameter_names(mat)),
        sorted(str(x) for x in MEL.get_texture_parameter_names(mat))))
    return path


def build_master_emissive():
    step('master material %s' % MASTER_EM)
    path = '%s/%s' % (F_MAT, MASTER_EM)
    if unreal.load_asset(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    at = unreal.AssetToolsHelpers.get_asset_tools()
    mat = at.create_asset(MASTER_EM, F_MAT, unreal.Material, unreal.MaterialFactoryNew())
    MEL.delete_all_material_expressions(mat)

    def E(cls, x, y):
        return MEL.create_material_expression(mat, cls, x, y)

    tint = vec_param(E, -800, 0, 'EmissiveTint', (1.0, 0.92, 0.74, 1.0))
    strength = sca_param(E, -800, 200, 'EmissiveStrength', 6.0)
    m = E(unreal.MaterialExpressionMultiply, -500, 100)
    wire(mat, tint, '', m, 'A')
    wire(mat, strength, '', m, 'B')
    prop(mat, m, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    dark = vec_param(E, -800, -250, 'BaseTint', (0.35, 0.34, 0.32, 1.0))
    prop(mat, dark, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.layout_material_expressions(mat)
    MEL.recompile_material(mat)
    ok('%s built' % MASTER_EM)
    return path


# --------------------------------------------------------------------------- #
# instances
# --------------------------------------------------------------------------- #

INSTANCES = [
    # name, family, base tint, dirt tint, rough, detail tiling, grunge tiling,
    # normal strength
    ('MI_ART_WallOchre', 'Plaster', (0.82, 0.73, 0.50), (0.30, 0.26, 0.19), 0.92,
     0.55, 0.12, 0.9),
    ('MI_ART_WallWainscot', 'Plaster', (0.30, 0.38, 0.28), (0.16, 0.20, 0.15), 0.86,
     0.60, 0.14, 0.9),
    ('MI_ART_WallClassroom', 'Plaster', (0.84, 0.78, 0.58), (0.33, 0.29, 0.21), 0.90,
     0.50, 0.10, 0.9),
    ('MI_ART_WallExt', 'PlasterExt', (0.66, 0.61, 0.47), (0.24, 0.22, 0.18), 0.94,
     0.40, 0.09, 1.1),
    ('MI_ART_Concrete', 'Concrete', (0.46, 0.46, 0.45), (0.19, 0.19, 0.18), 0.88,
     0.35, 0.13, 1.0),
    ('MI_ART_Floor', 'FloorTile', (0.46, 0.45, 0.42), (0.20, 0.20, 0.19), 0.78,
     0.28, 0.10, 0.8),
    ('MI_ART_Ceiling', 'Ceiling', (0.84, 0.82, 0.76), (0.36, 0.31, 0.22), 0.92,
     0.45, 0.11, 0.8),
    ('MI_ART_Wood', 'Wood', (0.46, 0.28, 0.13), (0.18, 0.11, 0.06), 0.70,
     0.60, 0.20, 1.0),
    ('MI_ART_WoodDark', 'Wood', (0.30, 0.18, 0.09), (0.12, 0.08, 0.04), 0.66,
     0.55, 0.18, 1.0),
    ('MI_ART_DoorGreen', 'WoodPaintGreen', (1.0, 1.0, 1.0), (0.20, 0.26, 0.19), 0.66,
     0.50, 0.16, 1.0),
    ('MI_ART_ShutterBlue', 'WoodPaintBlue', (1.0, 1.0, 1.0), (0.16, 0.20, 0.26), 0.64,
     0.55, 0.18, 1.0),
    ('MI_ART_Chalk', 'Chalk', (1.0, 1.0, 1.0), (0.10, 0.16, 0.12), 0.90,
     0.40, 0.10, 0.5),
    ('MI_ART_Metal', 'Metal', (0.40, 0.41, 0.42), (0.20, 0.19, 0.17), 0.44,
     0.45, 0.16, 0.9),
    ('MI_ART_MetalRust', 'MetalRust', (0.36, 0.34, 0.31), (0.22, 0.15, 0.10), 0.66,
     0.40, 0.15, 1.1),
    ('MI_ART_Paper', 'Paper', (0.88, 0.85, 0.76), (0.52, 0.45, 0.33), 0.92,
     0.25, 0.09, 0.6),
    ('MI_ART_Stone', 'Concrete', (0.38, 0.38, 0.36), (0.16, 0.16, 0.15), 0.90,
     0.30, 0.12, 1.0),
]

EMISSIVE_INSTANCES = [
    ('MI_ART_Tube', (1.0, 0.94, 0.78), 5.5),
    ('MI_ART_TubeCold', (0.72, 0.84, 1.0), 3.0),
    ('MI_ART_TubeDead', (0.30, 0.30, 0.28), 0.4),
    ('MI_ART_Indicator', (0.45, 0.95, 0.55), 4.0),
]

SIGN_MI = ('MI_ART_Sign', 'Sign')


def build_instances(master_path):
    step('material instances')
    at = unreal.AssetToolsHelpers.get_asset_tools()
    parent = unreal.load_asset(master_path)
    grunge = unreal.load_asset('%s/T_ART_Grunge_A' % F_TEX)
    for (name, family, base, dirt, rough, dt, gt, ns) in INSTANCES:
        path = '%s/%s' % (F_MAT, name)
        mi = unreal.load_asset(path)
        if mi is None:
            mi = at.create_asset(name, F_MAT, unreal.MaterialInstanceConstant,
                                 unreal.MaterialInstanceConstantFactoryNew())
        mi.set_editor_property('parent', parent)
        MEL.update_material_instance(mi)
        for suffix, param in (('A', 'Detail'), ('R', 'DetailRough'), ('N', 'NormalMap')):
            tex = unreal.load_asset('%s/T_ART_%s_%s' % (F_TEX, family, suffix))
            if tex is None:
                fail('%s: missing T_ART_%s_%s' % (name, family, suffix))
                continue
            MEL.set_material_instance_texture_parameter_value(mi, param, tex)
        MEL.set_material_instance_texture_parameter_value(mi, 'Grunge', grunge)
        MEL.set_material_instance_vector_parameter_value(
            mi, 'BaseTint', unreal.LinearColor(base[0], base[1], base[2], 1.0))
        MEL.set_material_instance_vector_parameter_value(
            mi, 'DirtTint', unreal.LinearColor(dirt[0], dirt[1], dirt[2], 1.0))
        MEL.set_material_instance_scalar_parameter_value(mi, 'Roughness', rough)
        MEL.set_material_instance_scalar_parameter_value(mi, 'NormalStrength', ns)
        MEL.set_material_instance_scalar_parameter_value(mi, 'DetailTiling', dt)
        MEL.set_material_instance_scalar_parameter_value(mi, 'GrungeTiling', gt)
        MEL.set_material_instance_scalar_parameter_value(mi, 'DirtAmount', 1.0)
    ok('%d surface instances' % len(INSTANCES))

    # sign: flat unlit-ish panel, no normal
    sname, sfamily = SIGN_MI
    path = '%s/%s' % (F_MAT, sname)
    mi = unreal.load_asset(path)
    if mi is None:
        mi = at.create_asset(sname, F_MAT, unreal.MaterialInstanceConstant,
                             unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property('parent', parent)
    MEL.update_material_instance(mi)
    for suffix, param in (('A', 'Detail'), ('R', 'DetailRough')):
        tex = unreal.load_asset('%s/T_ART_%s_%s' % (F_TEX, sfamily, suffix))
        if tex:
            MEL.set_material_instance_texture_parameter_value(mi, param, tex)
    MEL.set_material_instance_texture_parameter_value(mi, 'Grunge', grunge)
    MEL.set_material_instance_vector_parameter_value(
        mi, 'BaseTint', unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
    MEL.set_material_instance_vector_parameter_value(
        mi, 'DirtTint', unreal.LinearColor(0.55, 0.62, 0.52, 1.0))
    MEL.set_material_instance_scalar_parameter_value(mi, 'DirtAmount', 0.35)
    MEL.set_material_instance_scalar_parameter_value(mi, 'Roughness', 0.45)
    MEL.set_material_instance_scalar_parameter_value(mi, 'DetailTiling', 1.0)
    MEL.set_material_instance_scalar_parameter_value(mi, 'GrungeTiling', 0.35)
    MEL.set_material_instance_scalar_parameter_value(mi, 'NormalStrength', 0.2)
    ok('%s built' % sname)

    em = unreal.load_asset('%s/%s' % (F_MAT, MASTER_EM))
    for name, tint, strength in EMISSIVE_INSTANCES:
        path = '%s/%s' % (F_MAT, name)
        mi = unreal.load_asset(path)
        if mi is None:
            mi = at.create_asset(name, F_MAT, unreal.MaterialInstanceConstant,
                                 unreal.MaterialInstanceConstantFactoryNew())
        mi.set_editor_property('parent', em)
        MEL.update_material_instance(mi)
        MEL.set_material_instance_vector_parameter_value(
            mi, 'EmissiveTint', unreal.LinearColor(tint[0], tint[1], tint[2], 1.0))
        MEL.set_material_instance_scalar_parameter_value(mi, 'EmissiveStrength', strength)
    ok('%d emissive instances' % len(EMISSIVE_INSTANCES))
    K.save(F_MAT)


def main():
    K.make_folders()
    K.eas().make_directory(F_MAT)
    m = build_master()
    build_master_emissive()
    build_instances(m)


K.run(main)
