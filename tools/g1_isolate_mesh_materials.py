"""Bind school mesh defaults to repaired G1 materials in owned copies.

Actor overrides alone do not remove invalid source masters from cooked mesh
dependencies. Never edit original meshes/materials. Geometry/collision remain
preserved as exact oriented triangles in fresh native builds. Fast-built
source duplicates retain invalid derived data and are never adopted.
"""
import hashlib
import json
from pathlib import Path
import unreal
import sys
sys.path.insert(0, str(Path(unreal.Paths.project_dir()) / 'tools'))
import g1_repair_school_meshes as repair

ROOT = Path(unreal.Paths.project_dir())
BASE = '/Game/KhoangLang/Production/G1Canon'
MAP = BASE + '/Lvl_KL_SchoolSlice'
FOLDER = BASE + '/Meshes/MaterialBound'
MATERIALS = BASE + '/Materials'


def bound_description(source, target, slots, sub):
    original = source.get_static_mesh_description(0)
    repair.vertex_audit(original)
    groups = original.get_polygon_group_count()
    if sub.get_num_uv_channels(source, 0) != 1 or source.get_num_sections(0) != groups:
        raise RuntimeError('Source group/UV layout needs explicit clone: ' + source.get_name())
    description = target.create_static_mesh_description()
    group_ids = []
    for i in range(groups):
        group = description.create_polygon_group()
        description.set_polygon_group_material_slot_name(group,
            str(slots[sub.get_lod_material_slot(source,0,i)].material_slot_name))
        group_ids.append(group)
    removed, reprojected = [], []
    for index, record in enumerate(repair.triangle_records(original)):
        corners = record['corners']
        p = [c['position'] for c in corners]
        a = [p[1][i]-p[0][i] for i in range(3)]
        b = [p[2][i]-p[0][i] for i in range(3)]
        normal = [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
        if sum(v*v for v in normal) <= 1e-10:
            removed.append(index)
            continue  # Zero-area source faces have no surface or collision area.
        uv = [c['uv'] for c in corners]
        determinant = ((uv[1][0]-uv[0][0])*(uv[2][1]-uv[0][1])
                       -(uv[1][1]-uv[0][1])*(uv[2][0]-uv[0][0]))
        if abs(determinant) <= 1e-10:
            axes = [i for i in range(3) if i != max(range(3), key=lambda i: abs(normal[i]))]
            uv = [[point[axes[0]]*.0045, point[axes[1]]*.0045] for point in p]
            reprojected.append(index)
        instances = []
        for point, coordinate in zip(p, uv):
            vertex = description.create_vertex()
            description.set_vertex_position(vertex, unreal.Vector(*point))
            instance = description.create_vertex_instance(vertex)
            description.set_vertex_instance_uv(instance, unreal.Vector2D(*coordinate), 0)
            instances.append(instance)
        description.create_triangle(group_ids[record['group']], instances)
    return description, {'zero_area_faces_removed': removed, 'degenerate_uv_faces_reprojected': reprojected,
                         'source_triangles': original.get_triangle_count(),
                         'retained_triangles': description.get_triangle_count(),
                         'expected_corner_signature': repair.triangle_signature(description)}


def package_hash(path):
    file = ROOT / 'Content' / (path.removeprefix('/Game/') + '.uasset')
    return hashlib.sha256(file.read_bytes()).hexdigest()


def main():
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = editor.get_editor_world()
    if editor.get_game_world() or world.get_path_name().split('.')[0] != MAP:
        raise RuntimeError('Stopped PIE and canonical map required')
    report = {'status': 'started', 'map': MAP, 'meshes': [], 'actors': [],
              'runtime_shader_qualified': False,
              'source_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    out = ROOT / 'docs/agent/EVIDENCE/G1_mesh_material_binding.json'
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    unreal.EditorAssetLibrary.make_directory(FOLDER)
    adopted = {}
    try:
        world.modify()
        for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
            for component in actor.get_components_by_class(unreal.StaticMeshComponent):
                source = component.get_editor_property('static_mesh')
                if source is None:
                    continue
                path = source.get_path_name().split('.')[0]
                if not path.startswith('/Game/KhoangLang/'):
                    continue
                if path in adopted:
                    target = adopted[path]
                else:
                    source_hash = package_hash(path)
                    slots = list(source.get_editor_property('static_materials'))
                    changed = []
                    for index, slot in enumerate(slots):
                        original = slot.material_interface
                        if original is None:
                            continue
                        replacement = unreal.load_asset(MATERIALS + '/' + original.get_name())
                        if replacement is None or original == replacement:
                            continue
                        slot.material_interface = replacement
                        slots[index] = slot
                        changed.append({'slot': index, 'old': original.get_path_name(),
                                        'new': replacement.get_path_name()})
                    needs_geometry_copy = (path.startswith(BASE + '/Meshes/')
                        and (not repair.bounds(source)['finite']
                             or not repair.buffer_audit(source)['qualified']))
                    if not changed and not needs_geometry_copy:
                        adopted[path] = source
                        continue
                    if path.startswith(BASE + '/') and not needs_geometry_copy:
                        target = source
                    else:
                        suffix = hashlib.sha256(path.encode()).hexdigest()[:8]
                        target_path = FOLDER + '/' + source.get_name() + '_' + suffix + '_RegularV3'
                        target = unreal.load_asset(target_path)
                        if target is not None:
                            if unreal.EditorAssetLibrary.get_metadata_tag(target, 'G1MaterialOrigin') != path:
                                raise RuntimeError('Destination ownership differs: ' + target_path)
                        else:
                            target = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
                                target_path.rsplit('/', 1)[1], FOLDER, unreal.StaticMesh, None)
                            if target is None:
                                raise RuntimeError('Mesh copy failed: ' + path)
                            unreal.EditorAssetLibrary.set_metadata_tag(target, 'G1MaterialOrigin', path)
                        if target.get_num_sections(0) == 0:
                            target.set_editor_property('static_materials', slots)
                            target.set_editor_property('allow_cpu_access', True)
                            sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
                            source_body = source.get_editor_property('body_setup')
                            if source_body is None:
                                raise RuntimeError('Source collision body missing: ' + path)
                            description, geometry_change = bound_description(source, target, slots, sub)
                            repair.regular_build(target, description)
                            target_body = target.get_editor_property('body_setup')
                            target_body.set_editor_property('collision_trace_flag', source_body.get_editor_property('collision_trace_flag'))
                            target_body.set_editor_property('agg_geom', source_body.get_editor_property('agg_geom'))
                            target_body.set_editor_property('double_sided_geometry', source_body.get_editor_property('double_sided_geometry'))
                            if repair.triangle_signature(target.get_static_mesh_description(0)) != geometry_change['expected_corner_signature']:
                                raise RuntimeError('Native clone changed triangles: ' + path)
                            report.setdefault('geometry_changes', []).append({'source': path, **geometry_change})
                        sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
                        options = sub.get_lod_build_settings(target, 0)
                        if not options.get_editor_property('use_full_precision_u_vs'):
                            options.set_editor_property('use_full_precision_u_vs', True)
                            options.set_editor_property('use_high_precision_tangent_basis', True)
                            sub.set_lod_build_settings(target, 0, options)
                        audit = repair.buffer_audit(target)
                        if audit['invalid_tangent_count'] and not audit['invalid_position_count'] and not audit['invalid_normal_count']:
                            options = sub.get_lod_build_settings(target, 0)
                            options.set_editor_property('use_mikk_t_space', False)
                            sub.set_lod_build_settings(target, 0, options)
                            report.setdefault('native_tangent_fallbacks', []).append({
                                'target': target_path, 'before': audit,
                                'after': repair.buffer_audit(target), 'mode': 'Native non-Mikk recompute'})
                        if not repair.bounds(target)['finite'] or not repair.buffer_audit(target)['qualified']:
                            raise RuntimeError('Bound mesh strict geometry audit failed: ' + target_path)
                    target.modify()
                    target.set_editor_property('static_materials', slots)
                    native_slots = target.get_editor_property('static_materials')
                    if [s.material_interface for s in native_slots] != [s.material_interface for s in slots]:
                        raise RuntimeError('Default material readback differs: ' + path)
                    if not unreal.EditorAssetLibrary.save_loaded_asset(target, False):
                        raise RuntimeError('Bound mesh save failed')
                    if not path.startswith(BASE + '/') and package_hash(path) != source_hash:
                        raise RuntimeError('Original source package changed: ' + path)
                    adopted[path] = target
                    adopted[target.get_path_name().split('.')[0]] = target
                    report['meshes'].append({'source': path, 'target': target.get_path_name(),
                                             'source_sha256_before': source_hash, 'slots': changed})
                    out.write_text(json.dumps(report, indent=2), encoding='utf-8')
                if target != source:
                    overrides = list(component.get_editor_property('override_materials'))
                    collision = component.get_collision_enabled()
                    actor.modify()
                    component.modify()
                    if not component.set_static_mesh(target):
                        raise RuntimeError('Mesh binding rejected')
                    component.set_editor_property('override_materials', overrides)
                    if component.get_collision_enabled() != collision:
                        raise RuntimeError('Collision mode changed')
                    report['actors'].append({'label': actor.get_actor_label(), 'mesh': target.get_path_name()})
        if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAP):
            raise RuntimeError('Map save failed')
        report['status'] = 'MATERIAL_DEFAULTS_BOUND_COOK_RUNTIME_PENDING'
    except Exception as e:
        report['status'] = 'failed'
        report['error'] = str(e)
        raise
    finally:
        out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'status': report['status'], 'meshes': len(report['meshes']),
                      'actors': len(report['actors'])}))


if __name__ == '__main__':
    main()
