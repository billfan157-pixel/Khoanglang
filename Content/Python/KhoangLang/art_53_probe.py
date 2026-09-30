"""Art pass probe 53: mesh authoring, post-process, texture import, world position."""

import os
import struct
import traceback
import zlib

import unreal

OUT = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\art53'
os.makedirs(OUT, exist_ok=True)
L = []


def p(m=''):
    line = str(m)
    L.append(line)
    unreal.log('A53: ' + line)
    with open(os.path.join(OUT, 'report.txt'), 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def write_png(path, w, h, rgb_rows):
    """Minimal RGB PNG writer, no third-party imaging library."""
    raw = b''.join(b'\x00' + bytes(row) for row in rgb_rows)

    def chunk(tag, data):
        c = tag + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c))

    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(raw, 6))
    png += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)
    return len(png)


def main():
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.make_directory('/Game/KhoangLang/ArtTest')
    at = unreal.AssetToolsHelpers.get_asset_tools()

    p('=== A. mesh authoring surface ===')
    for n in ('MeshDescription', 'StaticMesh', 'EditorStaticMeshLibrary',
              'StaticMeshEditorSubsystem', 'MeshModifier', 'EditorSkeletalMeshLibrary',
              'SkeletalMesh', 'GeometryScriptLibrary_MeshBasicEditFunctions',
              'ModelingModeManager'):
        p('  unreal.%-46s %s' % (n, hasattr(unreal, n)))
    for n in ('EditorStaticMeshLibrary', 'StaticMeshEditorSubsystem'):
        o = getattr(unreal, n, None)
        if o is not None:
            p('  %s: %s' % (n, sorted(m for m in dir(o) if not m.startswith('_'))))
    try:
        p('  MeshDescription members: %s' %
          sorted(m for m in dir(unreal.MeshDescription) if not m.startswith('_')))
    except Exception as exc:
        p('  MeshDescription: %r' % (exc,))
    try:
        p('  StaticMesh members: %s' % (
            sorted(m for m in dir(unreal.StaticMesh) if not m.startswith('_'))[:60],))
    except Exception as exc:
        p('  %r' % (exc,))

    p('')
    p('=== B. post process settings ===')
    try:
        s = unreal.PostProcessSettings()
        p('  constructed PostProcessSettings')
        p('  members sample: %s' % ([m for m in dir(s) if 'bloom' in m.lower()
                                      or 'exposure' in m.lower()
                                      or 'vignette' in m.lower()
                                      or 'grain' in m.lower()
                                      or 'fringe' in m.lower()][:30],))
        p('  all settable: %s' % ([m for m in dir(s) if not m.startswith('_')][:120],))
    except Exception as exc:
        p('  PostProcessSettings: %r' % (exc,))
    p('  PostProcessComponent members: %s' %
      ([m for m in dir(unreal.PostProcessComponent) if not m.startswith('_')],))

    p('')
    p('=== C. write + import a procedural PNG ===')
    tmp = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\art53'
    w = h = 32
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            row += [min(255, x * 8), min(255, y * 8), 128]
        rows.append(row)
    n = write_png(os.path.join(tmp, 'test_tex.png'), w, h, rows)
    p('  wrote %d byte png' % n)
    tpath = '/Game/KhoangLang/ArtTest/ART_TEST_Tex'
    if unreal.load_asset(tpath):
        unreal.EditorAssetLibrary.delete_asset(tpath)
    task = unreal.AssetImportTask()
    task.set_editor_property('filename', os.path.join(tmp, 'test_tex.png'))
    task.set_editor_property('destination_path', '/Game/KhoangLang/ArtTest')
    task.set_editor_property('destination_name', 'ART_TEST_Tex')
    task.set_editor_property('automated', True)
    task.set_editor_property('save', True)
    task.set_editor_property('replace_existing', True)
    at.import_asset_tasks([task])
    t = unreal.load_asset(tpath)
    p('  imported: %s [%s]' % (t.get_name() if t else None,
                              t.get_class().get_name() if t else '-'))
    if t:
        for prop, val in (('srgb', True), ('compression_settings',
                                           unreal.TextureCompressionSettings.TC_DEFAULT),
                          ('mip_gen_settings',
                           unreal.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP),
                          ('address_x', unreal.TextureAddress.TA_WRAP),
                          ('address_y', unreal.TextureAddress.TA_WRAP),
                          ('filter', unreal.TextureFilter.TF_BILINEAR)):
            try:
                t.set_editor_property(prop, val)
                p('    %s = %s ok' % (prop, val))
            except Exception as exc:
                p('    %s -> %r' % (prop, str(exc)[:90]))
        p('    size = %s' % (t.blueprint_get_size_x(),))
        p('    size = %dx%d' % (t.get_editor_property('imported_size').x,
                                t.get_editor_property('imported_size').y))

    p('')
    p('=== D. world position expression + procedural weathering graph ===')
    mel = unreal.MaterialEditingLibrary
    mname = 'ART_TEST_Dirty'
    mpath = '/Game/KhoangLang/ArtTest/' + mname
    if unreal.load_asset(mpath):
        unreal.EditorAssetLibrary.delete_asset(mpath)
    mat = at.create_asset(mname, '/Game/KhoangLang/ArtTest', unreal.Material,
                          unreal.MaterialFactoryNew())
    try:
        mel.delete_all_material_expressions(mat)
        wpos = mel.create_material_expression(mat, unreal.MaterialExpressionWorldPosition,
                                              -1600, 0)
        p('    WorldPosition expr = %s' % (wpos.get_class().get_name() if wpos else None))
        p('    WorldPosition attrs: %s' %
          ([a for a in dir(wpos) if 'offset' in a.lower() or 'type' in a.lower()],))
        for prop in ('shader_offsets', 'world_position_shader_offset'):
            try:
                wpos.set_editor_property(prop, 0)
                p('    set %s = 0' % prop)
                break
            except Exception as exc:
                p('    %s -> %r' % (prop, str(exc)[:100]))
        mask = mel.create_material_expression(mat, unreal.MaterialExpressionComponentMask,
                                              -1400, 0)
        p('    ComponentMask = %s' % (mask.get_class().get_name() if mask else None))
        if mask:
            for prop, val in (('r', True), ('g', False), ('b', False), ('a', False)):
                try:
                    mask.set_editor_property(prop, val)
                except Exception as exc:
                    p('      mask.%s -> %r' % (prop, str(exc)[:80]))
        inv = mel.create_material_expression(mat, unreal.MaterialExpressionOneMinus,
                                             -1200, 0)
        div = mel.create_material_expression(mat, unreal.MaterialExpressionDivide,
                                             -1000, 0)
        mel.connect_material_expressions(mask, '', inv, 'Input')
        mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -1200, 200)
        const = [n for n in [mel.create_material_expression(
            mat, unreal.MaterialExpressionConstant, -1200, 200)]][0]
        const.set_editor_property('r', 0.35)
        mel.connect_material_expressions(inv, '', div, 'A')
        mel.connect_material_expressions(const, '', div, 'B')
        tint = mel.create_material_expression(mat, unreal.MaterialExpressionVectorParameter,
                                              -700, 100)
        tint.set_editor_property('parameter_name', 'DirtTint')
        tint.set_editor_property('default_value', unreal.LinearColor(0.35, 0.32, 0.26, 1.0))
        lerp = mel.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate,
                                              -450, 0)
        mel.connect_material_expressions(tint, '', lerp, 'B')
        mel.connect_material_expressions(div, '', lerp, 'A')
        col = mel.create_material_expression(mat, unreal.MaterialExpressionVectorParameter,
                                             -700, -200)
        col.set_editor_property('parameter_name', 'BaseTint')
        col.set_editor_property('default_value', unreal.LinearColor(0.70, 0.62, 0.42, 1.0))
        mel.connect_material_expressions(col, '', lerp, 'A2' if mel.get_inputs_for_material_expression(
            lerp).find('A2') else lerp, 'A')
        mel.connect_material_property(lerp, '', unreal.MaterialProperty.MP_BASE_COLOR)
        mel.layout_material_expressions(mat)
        mel.recompile_material(mat)
        p('    expressions=%d vector params=%s' % (
            mel.get_num_material_expressions(mat),
            [str(x) for x in mel.get_vector_parameter_names(mat)]))
        p('    lerp inputs: %s' % (mel.get_inputs_for_material_expression(lerp),))
    except Exception:
        p(traceback.format_exc())

    p('')
    p('=== E. cleanup ===')
    for a in (mpath, tpath):
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
    p('A53_FATAL')
