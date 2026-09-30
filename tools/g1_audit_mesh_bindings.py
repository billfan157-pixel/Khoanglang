"""Audit persisted G1 geometry/material dependencies; no asset mutation."""
import hashlib
import json
from pathlib import Path
import sys
import unreal

ROOT = Path(unreal.Paths.project_dir())
sys.path.insert(0, str(ROOT / 'tools'))
import g1_repair_school_meshes as repair

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
if world.get_path_name().split('.')[0] != repair.MAP:
    raise RuntimeError('Load G1 map')
report = {'map': repair.MAP, 'status': 'running', 'meshes': [], 'failures': [],
          'map_sha256': hashlib.sha256((ROOT/'Content/KhoangLang/Production/G1Canon/Lvl_KL_SchoolSlice.umap').read_bytes()).hexdigest()}
seen = set()
for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh = component.get_editor_property('static_mesh')
        if mesh is None:
            report['failures'].append('Missing mesh: ' + actor.get_actor_label())
            continue
        path = mesh.get_path_name().split('.')[0]
        if path in seen or not path.startswith('/Game/KhoangLang/'):
            continue
        seen.add(path)
        entry = {'path': path, 'bounds': repair.bounds(mesh),
                 'default_materials': [str(s.material_interface) for s in mesh.get_editor_property('static_materials')]}
        origin = (unreal.EditorAssetLibrary.get_metadata_tag(mesh,'G1MaterialOrigin')
                  or unreal.EditorAssetLibrary.get_metadata_tag(mesh,'G1MeshRepairOrigin'))
        if origin:
            source = unreal.load_asset(origin)
            source_description = source.get_static_mesh_description(0)
            entry['source_origin'] = origin
            entry['source_geometry_audit'] = repair.triangle_uv_audit(source_description)
            entry['source_package_sha256'] = repair.package_hash(origin)
        if path.startswith(repair.BASE + '/Meshes/'):
            entry['buffers'] = repair.buffer_audit(mesh)
            entry['rendered_triangles'] = sum(s['triangles'] for s in entry['buffers'].get('sections',[]))
            if not entry['buffers']['qualified']:
                report['failures'].append('Invalid geometry buffers: ' + path)
        if not entry['bounds']['finite'] or entry['bounds']['radius'] <= 0:
            report['failures'].append('Invalid bounds: ' + path)
        for slot in mesh.get_editor_property('static_materials'):
            material = slot.material_interface
            if material and material.get_path_name().startswith('/Game/KhoangLang/MaterialsArt/'):
                report['failures'].append('Original broken material dependency: ' + path)
        report['meshes'].append(entry)
report['status'] = 'passed' if not report['failures'] else 'failed'
(ROOT/'docs/agent/EVIDENCE/G1_mesh_binding_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'status': report['status'], 'meshes': len(seen), 'failures': report['failures']}))
