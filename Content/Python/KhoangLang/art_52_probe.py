"""Art pass probe 52: exact class/property names for materials and UMG."""

import os
import traceback

import unreal

OUT = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\art52'
os.makedirs(OUT, exist_ok=True)
L = []


def p(m=''):
    line = str(m)
    L.append(line)
    unreal.log('A52: ' + line)
    with open(os.path.join(OUT, 'report.txt'), 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def main():
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.make_directory('/Game/KhoangLang/ArtTest')

    p('=== A. MaterialExpression classes exposed to Python ===')
    names = sorted(n for n in dir(unreal) if n.startswith('MaterialExpression'))
    p('  count %d' % len(names))
    for n in names:
        p('    %s' % n)

    p('')
    p('=== B. MaterialProperty / connection enums ===')
    p('  MaterialProperty: %s' % ([str(e) for e in dir(unreal.MaterialProperty)
                                   if not e.startswith('_')],))
    p('  connect_material_property doc: %r' %
      (unreal.MaterialEditingLibrary.connect_material_property.__doc__,))
    p('  create_material_expression doc: %r' %
      (unreal.MaterialEditingLibrary.create_material_expression.__doc__,))
    p('  get_material_property_input_node doc: %r' %
      (unreal.MaterialEditingLibrary.get_material_property_input_node.__doc__,))

    p('')
    p('=== C. build a working textured material ===')
    at = unreal.AssetToolsHelpers.get_asset_tools()
    mel = unreal.MaterialEditingLibrary
    name = 'ART_TEST_Surface'
    path = '/Game/KhoangLang/ArtTest/' + name
    if unreal.load_asset(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mat = at.create_asset(name, '/Game/KhoangLang/ArtTest', unreal.Material,
                          unreal.MaterialFactoryNew())
    try:
        mel.delete_all_material_expressions(mat)
        tc = mel.create_material_expression(
            mat, unreal.MaterialExpressionTextureSampleParameter2D, -900, 0)
        tc.set_editor_property('parameter_name', 'BaseColor')
        nrm = mel.create_material_expression(
            mat, unreal.MaterialExpressionTextureSampleParameter2D, -900, 300)
        nrm.set_editor_property('parameter_name', 'Normal')
        try:
            nrm.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        except Exception as exc:
            p('    sampler_type: %r' % (exc,))
        rgh = mel.create_material_expression(
            mat, unreal.MaterialExpressionScalarParameter, -900, 600)
        rgh.set_editor_property('parameter_name', 'Roughness')
        rgh.set_editor_property('default_value', 0.85)
        mult = mel.create_material_expression(
            mat, unreal.MaterialExpressionMultiply, -500, 0)
        mel.connect_material_expressions(rgh, '', mult, 'A')
        mel.connect_material_expressions(tc, 'RGB', mult, 'B')
        for expr, out, prop in ((tc, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR),
                                (nrm, 'RGB', unreal.MaterialProperty.MP_NORMAL),
                                (mult, '', unreal.MaterialProperty.MP_ROUGHNESS)):
            try:
                mel.connect_material_property(expr, out, prop)
                p('    connected %s -> %s' % (expr.get_class().get_name(), prop))
            except Exception as exc:
                p('    connect_material_property %s raised %r' % (prop, exc))
        mel.layout_material_expressions(mat)
        mel.recompile_material(mat)
        p('    expressions: %d' % mel.get_num_material_expressions(mat))
        p('    texture params: %s' % [str(x) for x in mel.get_texture_parameter_names(mat)])
        p('    scalar params : %s' % [str(x) for x in mel.get_scalar_parameter_names(mat)])
        p('    shaders: %d' % mel.get_num_shader_types(mat))
    except Exception:
        p(traceback.format_exc())

    p('')
    p('=== D. material instance from it ===')
    ipath = '/Game/KhoangLang/ArtTest/ART_TEST_MI'
    if unreal.load_asset(ipath):
        unreal.EditorAssetLibrary.delete_asset(ipath)
    mi = at.create_asset('ART_TEST_MI', '/Game/KhoangLang/ArtTest',
                         unreal.MaterialInstanceConstant,
                         unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property('parent', mat)
    mel.update_material_instance(mi)
    mel.set_material_instance_scalar_parameter_value(mi, 'Roughness', 0.7)
    p('    MI parent=%s roughness=%r' % (mi.get_editor_property('parent').get_name(),
                                         mel.get_material_instance_scalar_parameter_value(
                                             mi, 'Roughness')))

    p('')
    p('=== E. UMG: WidgetBlueprint property names ===')
    wname = 'ART_TEST_Widget'
    wpath = '/Game/KhoangLang/ArtTest/' + wname
    if unreal.load_asset(wpath):
        unreal.EditorAssetLibrary.delete_asset(wpath)
    fac = unreal.WidgetBlueprintFactory()
    fac.set_editor_property('parent_class', unreal.UserWidget)
    w = at.create_asset(wname, '/Game/KhoangLang/ArtTest', unreal.WidgetBlueprint, fac)
    p('  widget: %s' % (w.get_name() if w else None))
    if w:
        for prop in ('widget_tree', 'WidgetTree', 'widget_tree_'):  # noqa
            pass
        p('  WidgetBlueprint attributes: %s' % ([a for a in dir(w) if not a.startswith('_')],))
        for prop in ('widget_tree', 'ubergraph_pages', 'widget_animations'):
            try:
                p('    %s = %r' % (prop, w.get_editor_property(prop)))
            except Exception as exc:
                p('    %s -> %r' % (prop, str(exc)[:110]))
        try:
            gc = w.generated_class()
            p('    generated_class = %s' % (gc,))
        except Exception as exc:
            p('    generated_class -> %r' % (exc,))

    p('')
    p('=== F. engine asset names (raw) ===')
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    for folder in ('/Engine/BasicShapes', '/Engine/EngineMeshes', '/Engine/EngineFonts',
                   '/Engine/EngineMaterials', '/Engine/EngineResources'):
        try:
            rows = [(str(a.asset_name), str(a.asset_class_path)) for a in
                    ar.get_assets_by_path(unreal.Name(folder), True, False)]
            p('  %-28s %s' % (folder, sorted(x[0] for x in rows)))
        except Exception as exc:
            p('  %-28s raised %r' % (folder, exc))

    p('')
    p('=== G. cleanup ===')
    for a in (path, ipath, wpath):
        if unreal.load_asset(a):
            try:
                unreal.EditorAssetLibrary.delete_asset(a)
            except Exception as exc:
                p('  delete %s %r' % (a, exc))
    p('DONE')


try:
    rep = os.path.join(OUT, 'report.txt')
    if os.path.exists(rep):
        os.remove(rep)
    main()
except Exception:
    p(traceback.format_exc())
    p('A52_FATAL')
