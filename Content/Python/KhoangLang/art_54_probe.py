"""Art pass probe 54: prove the weathering material graph builds and binds textures."""

import os
import traceback

import unreal

OUT = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\art54'
os.makedirs(OUT, exist_ok=True)
L = []


def p(m=''):
    line = str(m)
    L.append(line)
    unreal.log('A54: ' + line)
    with open(os.path.join(OUT, 'report.txt'), 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def main():
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.make_directory('/Game/KhoangLang/ArtTest')
    at = unreal.AssetToolsHelpers.get_asset_tools()
    mel = unreal.MaterialEditingLibrary

    mname = 'ART_TEST_Plaster'
    mpath = '/Game/KhoangLang/ArtTest/' + mname
    if unreal.load_asset(mpath):
        unreal.EditorAssetLibrary.delete_asset(mpath)
    mat = at.create_asset(mname, '/Game/KhoangLang/ArtTest', unreal.Material,
                          unreal.MaterialFactoryNew())
    p('material: %s' % (mat.get_name() if mat else None))
    try:
        mel.delete_all_material_expressions(mat)
        E = mel.create_material_expression

        # world height -> 0 at floor, 1 at ceiling
        wpos = E(mat, unreal.MaterialExpressionWorldPosition, -2200, 200)
        p('  WorldPosition attrs: %s' % ([a for a in dir(wpos)
                                          if 'offset' in a.lower() or 'shader' in a.lower()],))
        for prop in ('shader_offsets', 'world_position_shader_offset'):
            try:
                wpos.set_editor_property(prop, 0)
                p('  wpos.%s = 0 (AbsolutePosition)' % prop)
                break
            except Exception as exc:
                p('  wpos.%s -> %r' % (prop, str(exc)[:90]))
        mask = E(mat, unreal.MaterialExpressionComponentMask, -2000, 200)
        p('  ComponentMask attrs: %s' % ([a for a in dir(mask) if a in
                                          ('r', 'g', 'b', 'a')],))
        mask.set_editor_property('r', True)
        mask.set_editor_property('g', False)
        mask.set_editor_property('b', False)
        mask.set_editor_property('a', False)
        mel.connect_material_expressions(wpos, '', mask, '')
        p('  mask outputs: %s' % (mel.get_material_expression_output_names(mask),))
        p('  mask inputs: %s' % (mel.get_inputs_for_material_expression(mask),))

        inv = E(mat, unreal.MaterialExpressionOneMinus, -1800, 200)
        mel.connect_material_expressions(mask, '', inv, 'Input')
        k = E(mat, unreal.MaterialExpressionConstant, -1800, 400)
        k.set_editor_property('r', 1.6)
        p('  OneMinus inputs: %s' % (mel.get_inputs_for_material_expression(inv),))
        mul = E(mat, unreal.MaterialExpressionMultiply, -1600, 200)
        mel.connect_material_expressions(inv, '', mul, 'A')
        mel.connect_material_expressions(k, '', mul, 'B')
        p('  Multiply inputs: %s' % (mel.get_inputs_for_material_expression(mul),))

        # detail texture, tiled
        tc = E(mat, unreal.MaterialExpressionTextureCoordinate, -2200, -300)
        det = E(mat, unreal.MaterialExpressionTextureSampleParameter2D, -2000, -300)
        det.set_editor_property('parameter_name', 'Detail')
        tiling = E(mat, unreal.MaterialExpressionMultiply, -2200, -500)
        mel.connect_material_expressions(tc, '', tiling, 'A')
        mel.connect_material_expressions(k, '', tiling, 'B')
        p('  TextureCoordinate outputs: %s' %
          (mel.get_material_expression_output_names(tc),))
        mel.connect_material_expressions(tiling, '', det, 'UVs' if
                                          'UVs' in mel.get_inputs_for_material_expression(det)
                                          else 'Coordinates')
        p('  Detail inputs: %s' % (mel.get_inputs_for_material_expression(det),))

        # base colour = Lerp(dirtTint, BaseTint, heightMask) * detail
        base = E(mat, unreal.MaterialExpressionVectorParameter, -1400, -500)
        base.set_editor_property('parameter_name', 'BaseTint')
        base.set_editor_property('default_value', unreal.LinearColor(0.72, 0.66, 0.48, 1.0))
        dirt = E(mat, unreal.MaterialExpressionVectorParameter, -1400, -700)
        dirt.set_editor_property('parameter_name', 'DirtTint')
        dirt.set_editor_property('default_value', unreal.LinearColor(0.30, 0.27, 0.21, 1.0))
        lerp = E(mat, unreal.MaterialExpressionLinearInterpolate, -1100, -400)
        p('  LinearInterpolate inputs: %s' % (mel.get_inputs_for_material_expression(lerp),))
        mel.connect_material_expressions(mul, '', lerp, 'Alpha')
        mel.connect_material_expressions(dirt, '', lerp, 'A')
        mel.connect_material_expressions(base, '', lerp, 'B')
        tintmul = E(mat, unreal.MaterialExpressionMultiply, -800, -400)
        mel.connect_material_expressions(lerp, '', tintmul, 'A')
        mel.connect_material_expressions(det, 'RGB', tintmul, 'B')
        mel.connect_material_property(tintmul, '', unreal.MaterialProperty.MP_BASE_COLOR)

        # roughness: param modulated by height
        rgh = E(mat, unreal.MaterialExpressionScalarParameter, -800, 200)
        rgh.set_editor_property('parameter_name', 'Roughness')
        rgh.set_editor_property('default_value', 0.9)
        rgvar = E(mat, unreal.MaterialExpressionVectorParameter, -800, 0)
        rgvar.set_editor_property('parameter_name', 'RoughnessTint')
        rgvar.set_editor_property('default_value', unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
        rghmul = E(mat, unreal.MaterialExpressionMultiply, -600, 150)
        mel.connect_material_expressions(rgh, '', rghmul, 'A')
        mel.connect_material_expressions(rgvar, '', rghmul, 'B')
        mel.connect_material_property(rghmul, 'R', unreal.MaterialProperty.MP_ROUGHNESS)

        # normal from the detail texture
        nrm = E(mat, unreal.MaterialExpressionTextureSampleParameter2D, -800, 500)
        nrm.set_editor_property('parameter_name', 'NormalMap')
        try:
            nrm.set_editor_property('sampler_type',
                                    unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
            p('  normal sampler set')
        except Exception as exc:
            p('  normal sampler -> %r' % (exc,))
        nscale = E(mat, unreal.MaterialExpressionScalarParameter, -800, 750)
        nscale.set_editor_property('parameter_name', 'NormalStrength')
        nscale.set_editor_property('default_value', 1.0)
        nmul = E(mat, unreal.MaterialExpressionMultiply, -600, 600)
        mel.connect_material_expressions(nscale, '', nmul, 'A')
        mel.connect_material_expressions(nrm, 'RGB', nmul, 'B')
        mel.connect_material_property(nmul, '', unreal.MaterialProperty.MP_NORMAL)

        mel.layout_material_expressions(mat)
        mel.recompile_material(mat)
        p('  expressions: %d  shaders: %d' % (mel.get_num_material_expressions(mat),
                                              mel.get_num_shader_types(mat)))
        p('  vector params : %s' % [str(x) for x in mel.get_vector_parameter_names(mat)])
        p('  scalar params : %s' % [str(x) for x in mel.get_scalar_parameter_names(mat)])
        p('  texture params: %s' % [str(x) for x in mel.get_texture_parameter_names(mat)])
        p('  used textures : %s' % [str(x) for x in mel.get_material_used_textures(mat)])

        ipath = '/Game/KhoangLang/ArtTest/ART_TEST_Plaster_MI'
        if unreal.load_asset(ipath):
            unreal.EditorAssetLibrary.delete_asset(ipath)
        mi = at.create_asset('ART_TEST_Plaster_MI', '/Game/KhoangLang/ArtTest',
                             unreal.MaterialInstanceConstant,
                             unreal.MaterialInstanceConstantFactoryNew())
        mi.set_editor_property('parent', mat)
        mel.update_material_instance(mi)
        mel.set_material_instance_vector_parameter_value(
            mi, 'BaseTint', unreal.LinearColor(0.8, 0.7, 0.45, 1.0))
        mel.set_material_instance_scalar_parameter_value(mi, 'Roughness', 0.85)
        p('  MI created: %s  base=%r rough=%r' % (
            mi.get_name(),
            mel.get_material_instance_vector_parameter_value(mi, 'BaseTint'),
            mel.get_material_instance_scalar_parameter_value(mi, 'Roughness')))
    except Exception:
        p(traceback.format_exc())

    p('')
    p('=== cleanup ===')
    for a in (mpath, '/Game/KhoangLang/ArtTest/ART_TEST_Plaster_MI'):
        if unreal.load_asset(a):
            try:
                unreal.EditorAssetLibrary.delete_asset(a)
                p('  deleted %s' % a)
            except Exception as exc:
                p('  delete %s: %r' % (a, exc))
    p('DONE')


try:
    rep = os.path.join(OUT, 'report.txt')
    if os.path.exists(rep):
        os.remove(rep)
    main()
except Exception:
    p(traceback.format_exc())
    p('A54_FATAL')
