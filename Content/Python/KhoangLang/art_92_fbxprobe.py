"""Probe the FBX import option names this UE build actually exposes.

Enum identifiers and option field names move between engine versions, so the
import script reads them instead of guessing. This probe prints the real list.

Run:  run_ue_script.ps1 -Script art_92_fbxprobe.py
"""

import unreal

LOG = []


def log(m):
    LOG.append(str(m))
    unreal.log('FBXPROBE: ' + str(m))


def props(cls):
    try:
        return sorted([p for p in dir(cls) if not p.startswith('_')
                       and p not in ('get_editor_property',
                                     'set_editor_property', 'copy',
                                     'set')])
    except Exception as exc:
        return ['ERR %r' % (exc,)]


log('FbxImportUI: %s' % props(unreal.FbxImportUI))
log('FbxStaticMeshImportData: %s' % props(unreal.FbxStaticMeshImportData))
log('AssetImportTask: %s' % props(unreal.AssetImportTask))
log('StaticMesh: %s' % sorted(
    [p for p in dir(unreal.StaticMesh)
     if 'mesh_description' in p or 'description' in p or 'bounds' in p
     or 'source' in p]))

ui = unreal.FbxImportUI()
log('FbxImportUI instance editor props:')
for p in ['mesh_type_to_import', 'original_import_type', 'import_mesh',
          'import_as_skeletal', 'import_animations', 'import_materials',
          'import_textures', 'create_physics_asset', 'static_mesh_import_data',
          'mesh_type', 'import_type']:
    try:
        log('  %s = %r' % (p, ui.get_editor_property(p)))
    except Exception as exc:
        log('  %s -> %s' % (p, str(exc)[:110]))

smd = unreal.FbxStaticMeshImportData()
log('FbxStaticMeshImportData instance editor props:')
for p in ['combine_meshes', 'generate_lightmap_u_vs', 'auto_generate_collision',
          'remove_degenerates', 'import_uniform_scale', 'use_t0_as_ref_pose',
          'convert_scene', 'bake_scale', 'rotation', 'location', 'scale',
          'mesh_name_to_import', 'import_mesh_lo_ds', 'normal_import_method',
          'use_tangents', 'threshold_position', 'threshold_normal']:
    try:
        log('  %s = %r' % (p, smd.get_editor_property(p)))
    except Exception as exc:
        log('  %s -> %s' % (p, str(exc)[:110]))

log('MI factory props: %s' % sorted(
    [p for p in dir(unreal.MaterialInstanceConstantFactoryNew)
     if not p.startswith('_')]))
