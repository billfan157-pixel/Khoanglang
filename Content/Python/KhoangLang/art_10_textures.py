"""Khoang Lang 02:17 - art pass step 1: generate and import the textures.

Each surface family exports albedo / roughness / normal at 256x256.  Roughness
and normal are imported linear (sRGB off); albedo is sRGB.  All of it is
generated from noise in art_tex.py - no downloaded or photographed art.

Run headless:  run_ue_script.ps1 art_10_textures.py
"""

import os
import sys

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import kl_core as K  # noqa: E402
import art_tex as T  # noqa: E402
from kl_core import step, ok, warn, fail  # noqa: E402

F_TEX = K.ROOT + '/TexturesArt'
STAGE = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\arttex'


def import_png(png_path, asset_name, srgb):
    at = unreal.AssetToolsHelpers.get_asset_tools()
    path = '%s/%s' % (F_TEX, asset_name)
    task = unreal.AssetImportTask()
    task.set_editor_property('filename', png_path)
    task.set_editor_property('destination_path', F_TEX)
    task.set_editor_property('destination_name', asset_name)
    task.set_editor_property('automated', True)
    task.set_editor_property('save', True)
    task.set_editor_property('replace_existing', True)
    at.import_asset_tasks([task])
    tex = unreal.load_asset(path)
    if tex is None:
        fail('import %s' % asset_name)
        return None
    for prop, val in (('srgb', srgb),
                      ('compression_settings',
                       unreal.TextureCompressionSettings.TC_NORMALMAP
                       if asset_name.endswith('_N') else
                       unreal.TextureCompressionSettings.TC_DEFAULT),
                      ('mip_gen_settings',
                       unreal.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP),
                      ('address_x', unreal.TextureAddress.TA_WRAP),
                      ('address_y', unreal.TextureAddress.TA_WRAP),
                      ('filter', unreal.TextureFilter.TF_BILINEAR),
                      ('never_stream', False)):
        try:
            tex.set_editor_property(prop, val)
        except Exception as exc:
            warn('%s.%s: %r' % (asset_name, prop, str(exc)[:70]))
    return tex


def main():
    K.make_folders()
    K.eas().make_directory(F_TEX)
    if not os.path.isdir(STAGE):
        os.makedirs(STAGE)
    step('generate + import art textures')
    made = 0
    for name, builder, srgb in T.TEXTURES:
        try:
            maps = builder()
        except Exception as exc:
            fail('%s generation: %r' % (name, exc))
            continue
        entry = []
        for kind, rows in maps.items():
            if kind == 'height':
                h = len(rows)
                w = len(rows[0])
                nrows = T.normal_rows(rows, w, h, 2.4)
                png = os.path.join(STAGE, '%s_N.png' % name)
                T.write_png(png, w, h, nrows)
                import_png(png, '%s_N' % name, False)
                entry.append('N')
            else:
                h = len(rows)
                w = len(rows[0]) // 3
                png = os.path.join(STAGE, '%s_%s.png' % (name, kind))
                T.write_png(png, w, h, rows)
                import_png(png, '%s_%s' % (name, kind[0].upper()), srgb)
                entry.append(kind[0].upper())
            made += 1
        ok('%-20s -> %s' % (name, ', '.join(entry)))
    K.save(F_TEX)
    ok('%d texture assets imported into %s' % (made, F_TEX))


K.run(main)
