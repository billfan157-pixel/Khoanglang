"""Art pass probe 51: can I really author materials and UMG from Python here?"""

import os
import traceback

import unreal

OUT = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\art51'
os.makedirs(OUT, exist_ok=True)
L = []


def p(m=''):
    line = str(m)
    L.append(line)
    unreal.log('A51: ' + line)
    with open(os.path.join(OUT, 'report.txt'), 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def reg_paths(folder):
    out = []
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    try:
        for a in ar.get_assets_by_path(unreal.Name(folder), True, False):
            out.append((str(a.asset_name), str(a.asset_class_path),
                        '%s/%s' % (str(a.package_name), str(a.asset_name))))
    except Exception as exc:
        p('  registry %s raised %r' % (folder, exc))
    return out


def main():
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.make_directory('/Game/KhoangLang/ArtTest')
    mel = unreal.MaterialEditingLibrary

    p('=== A. engine asset inventory ===')
    for folder in ('/Engine/BasicShapes', '/Engine/EngineMeshes', '/Engine/EditorMeshes',
                   '/Engine/EngineFonts', '/Engine/Slate/Fonts', '/Engine/Fonts',
                   '/Engine/EngineMaterials', '/Engine/EngineResources',
                   '/Engine/EditorMaterials'):
        rows = reg_paths(folder)
        keep = [r for r in rows if r[1].rsplit('.', 1)[-1] in
                ('StaticMesh', 'Material', 'Font', 'CompositeFont', 'FontFace',
                 'Texture2D', 'MaterialInstanceConstant', 'SkyLight', 'CurveFloat')]
        p('  %-30s %d assets' % (folder, len(rows)))
        for r in sorted(keep)[:26]:
            p('      %-46s %s' % (r[0], r[1].rsplit('.', 1)[-1]))

    p('')
    p('=== B. author a real material from Python ===')
    name = 'ART_TEST_Surface'
    path = '/Game/KhoangLang/ArtTest/' + name
    existing = unreal.load_asset(path)
    if existing is not None:
        try:
            unreal.EditorAssetLibrary.delete_asset(path)
        except Exception as exc:
            p('  delete: %r' % (exc,))
    at = unreal.AssetToolsHelpers.get_asset_tools()
    mat = at.create_asset(name, '/Game/KhoangLang/ArtTest', unreal.Material,
                          unreal.MaterialFactoryNew())
    p('  created material: %s' % (mat.get_name() if mat else 'None'))
    if mat:
        try:
            mel.delete_all_material_expressions(mat)
            base = mel.create_material_expression(mat, unreal.MaterialExpressionTextureBaseColor, -600, 0)
            p('    create TextureBaseColor -> %s' % (base.get_class().get_name() if base else 'None'))
            tc = mel.create_material_expression(
                mat, unreal.MaterialExpressionTextureSampleParameter2D, -900, 0)
            tc.set_editor_property('parameter_name', 'BaseColor')
            p('    create TextureSampleParameter2D -> %s' % (tc.get_class().get_name() if tc else 'None'))
            nrm = mel.create_material_expression(
                mat, unreal.MaterialExpressionTextureSampleParameter2D, -900, 250)
            nrm.set_editor_property('parameter_name', 'Normal')
            nrm.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
            p('    normal param -> %s' % nrm.get_class().get_name())
            rough = mel.create_material_expression(
                mat, unreal.MaterialExpressionScalarParameter, -900, 500)
            rough.set_editor_property('parameter_name', 'Roughness')
            mel.connect_material_expressions(tc, 'RGB', base, 'RGB')
            mel.connect_material_expressions(nrm, 'RGB', base, 'Normal')
            mel.connect_material_expressions(base, '', mel.get_material_property_input_node(mat, 'BaseColor'), 'RGB')
            p('    connected to BaseColor property node')
            mel.recompile_material(mat)
            mel.update_material_instance(mat)
            p('    material after build: %d expressions' % mel.get_num_material_expressions(mat))
            p('    scalar params: %s' % [str(x) for x in mel.get_scalar_parameter_names(mat)])
            p('    texture params: %s' % [str(x) for x in mel.get_texture_parameter_names(mat)])
        except Exception:
            p(traceback.format_exc())

    p('')
    p('=== C. create a UMG widget blueprint from Python ===')
    wname = 'ART_TEST_Widget'
    wpath = '/Game/KhoangLang/ArtTest/' + wname
    w = unreal.load_asset(wpath)
    if w is not None:
        try:
            unreal.EditorAssetLibrary.delete_asset(wpath)
        except Exception as exc:
            p('  delete widget: %r' % (exc,))
    try:
        fac = unreal.WidgetBlueprintFactory()
        fac.set_editor_property('parent_class', unreal.UserWidget)
        w = at.create_asset(wname, '/Game/KhoangLang/ArtTest',
                           unreal.WidgetBlueprint, fac)
        p('  created widget blueprint: %s [%s]' % (w.get_name() if w else 'None',
                                                  w.get_class().get_name() if w else '-'))
        if w:
            tree = None
            for prop in ('widget_tree',):
                try:
                    tree = w.get_editor_property(prop)
                    p('    %s -> %s' % (prop, tree))
                except Exception as exc:
                    p('    %s raised %r' % (prop, exc))
            if tree is not None:
                canvas = tree.construct_widget(unreal.CanvasPanel, 'RootCanvas')
                p('    construct_widget CanvasPanel -> %s' % (canvas,))
                tb = tree.construct_widget(unreal.TextBlock, 'TitleText')
                tb.set_editor_property('text', unreal.Text('KHOẢNG LẶNG 02:17'))
                p('    construct TextBlock -> %s text=%r' % (tb, tb.get_editor_property('text')))
                sb = tree.construct_widget(unreal.SizeBox, 'Box')
                p('    construct SizeBox -> %s' % (sb,))
                try:
                    tree.root_widget = canvas
                    p('    assigned root_widget')
                except Exception as exc:
                    p('    root_widget assign raised %r' % (exc,))
            unreal.BlueprintEditorLibrary.compile_blueprint(w) \
                if hasattr(unreal, 'BlueprintEditorLibrary') else None
            p('    compiled; status=%s' % w.get_editor_property('status'))
    except Exception:
        p(traceback.format_exc())

    p('')
    p('=== D. texture import path (procedural PNG) ===')
    p('  AssetImportTask available: %s' % hasattr(unreal, 'AssetImportTask'))
    p('  ImageWrapper factory: %s' % [n for n in dir(unreal) if 'Image' in n][:12])

    p('')
    p('=== E. texture generation options ===')
    try:
        p('  unreal.TextureFactory members: %s' %
          ([m for m in dir(unreal.TextureFactory) if not m.startswith('_')],))
    except Exception as exc:
        p('  %r' % (exc,))
    for n in ('TextureRenderTarget2D', 'Texture2D', 'LinearColor', 'Color'):
        p('  unreal.%-26s %s' % (n, hasattr(unreal, n)))

    p('')
    p('=== F. cleanup ===')
    for a in (path, wpath):
        if unreal.load_asset(a) is not None:
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
    p('A51_FATAL')
