"""Rebuild bounded mesh copies in G1; never alter the source mesh packages.

Execution is serialized by the shared-editor owner, with PIE stopped and
G1Canon/Lvl_KL_SchoolSlice loaded. Finite source positions are a prerequisite:
non-finite authored coordinates abort instead of being invented or zeroed.
The editor's regular static-mesh builder recomputes normals/tangents and bounds.
The cassette's malformed Y-cylinder caps are corrected in an owned mesh copy.
The wall's welded smoothing is replaced by isolated native triangle corners,
with exact triangle positions, winding, UVs and material groups preserved.
"""
import ast
import hashlib
import json
import math
from pathlib import Path
import sys
import unreal

ROOT = Path(unreal.Paths.project_dir())
sys.path.insert(0, str(ROOT / 'Content/Python/KhoangLang'))
import kl_mesh as M

BASE = '/Game/KhoangLang/Production/G1Canon'
MAP = BASE + '/Lvl_KL_SchoolSlice'
FOLDER = BASE + '/Meshes'
SCHOOL = '/Game/KhoangLang/Production/Meshes/School'
SOURCES = [SCHOOL + '/' + name for name in
           ('SM_KL_Notice_Board', 'SM_KL_Wall_700', 'SM_KL_Door_Frame')]
DECK = FOLDER + '/SM_KL_Prop_TapeDeck'
ISOLATED_ARCHITECTURE = {'SM_KL_Wall_700', 'SM_KL_Door_Frame'}
REPORT = ROOT / 'docs/agent/EVIDENCE/G1_school_mesh_repair.json'


def package_hash(path):
    filename = ROOT / 'Content' / (path.removeprefix('/Game/') + '.uasset')
    if not filename.is_file():
        raise RuntimeError('Source package file not found: ' + path)
    return hashlib.sha256(filename.read_bytes()).hexdigest()


def xyz(value):
    return [float(value.x), float(value.y), float(value.z)]


def finite(values):
    return all(math.isfinite(v) for v in values)


def bounds(mesh):
    value = mesh.get_bounds()
    origin, extent = xyz(value.origin), xyz(value.box_extent)
    radius = float(value.sphere_radius)
    return {'origin': origin, 'extent': extent, 'radius': radius,
            'finite': finite(origin + extent + [radius])}


def vertex_audit(description):
    if description is None or description.is_empty():
        raise RuntimeError('Mesh description absent or empty')
    count = description.get_vertex_count()
    points = []
    # ID validity is checked before native position access. Existing procedural
    # descriptions are dense, but tolerate bounded sparse IDs without guessing.
    for index in range(count * 4 + 256):
        vertex_id = unreal.VertexID(id_value=index)
        if not description.is_vertex_valid(vertex_id):
            continue
        point = xyz(description.get_vertex_position(vertex_id))
        if not finite(point):
            raise RuntimeError('Non-finite authored position at vertex ' + str(index))
        points.append(point)
        if len(points) == count:
            break
    if len(points) != count or count == 0:
        raise RuntimeError('Could not enumerate all finite source positions')
    return {'vertices': count, 'triangles': description.get_triangle_count(),
            'minimum': [min(p[i] for p in points) for i in range(3)],
            'maximum': [max(p[i] for p in points) for i in range(3)],
            'positions_sha256': hashlib.sha256(
                json.dumps(points, separators=(',', ':')).encode()).hexdigest()}


def triangle_uv_audit(description):
    count = description.get_triangle_count()
    checked = 0
    bad_uv, bad_geometry = [], []
    for index in range(count * 4 + 256):
        triangle = unreal.TriangleID(id_value=index)
        if not description.is_triangle_valid(triangle):
            continue
        instances = description.get_triangle_vertex_instances(triangle)
        points = [xyz(description.get_vertex_position(
            description.get_vertex_instance_vertex(vi))) for vi in instances]
        coordinates = [description.get_vertex_instance_uv(vi, 0) for vi in instances]
        uv = [[float(value.x), float(value.y)] for value in coordinates]
        if len(points) != 3 or not all(finite(value) for value in points + uv):
            raise RuntimeError('Invalid native triangle positions/UVs: ' + str(index))
        du, dv = [uv[1][i]-uv[0][i] for i in range(2)]
        eu, ev = [uv[2][i]-uv[0][i] for i in range(2)]
        determinant = du*ev - dv*eu
        a = [points[1][i]-points[0][i] for i in range(3)]
        b = [points[2][i]-points[0][i] for i in range(3)]
        cross = [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2],
                 a[0]*b[1]-a[1]*b[0]]
        if abs(determinant) <= 1e-10:
            bad_uv.append({'triangle': index, 'positions': points, 'uv': uv})
        if sum(value*value for value in cross) <= 1e-10:
            bad_geometry.append(index)
        checked += 1
        if checked == count:
            break
    if checked != count:
        raise RuntimeError('Could not audit every native triangle UV')
    return {'triangles': checked, 'degenerate_uv_count': len(bad_uv),
            'degenerate_geometry_count': len(bad_geometry),
            'degenerate_uv_examples': bad_uv[:12],
            'degenerate_geometry_examples': bad_geometry[:12]}


def triangle_records(description):
    """Read exact oriented corner data; never edit the source description."""
    count = description.get_triangle_count()
    records = []
    for index in range(count * 4 + 256):
        triangle = unreal.TriangleID(id_value=index)
        if not description.is_triangle_valid(triangle):
            continue
        corners = []
        for instance in description.get_triangle_vertex_instances(triangle):
            point = xyz(description.get_vertex_position(
                description.get_vertex_instance_vertex(instance)))
            uv = description.get_vertex_instance_uv(instance, 0)
            coordinate = [float(uv.x), float(uv.y)]
            if not finite(point + coordinate):
                raise RuntimeError('Non-finite native triangle corner')
            corners.append({'position': point, 'uv': coordinate})
        if len(corners) != 3:
            raise RuntimeError('Native triangle does not have three corners')
        group = description.get_triangle_polygon_group(triangle)
        records.append({'group': int(group.id_value), 'corners': corners})
        if len(records) == count:
            break
    if len(records) != count:
        raise RuntimeError('Could not enumerate all native triangles')
    return records


def triangle_signature(description):
    # Compare authored order and winding, not just bounds or vertex count.
    return hashlib.sha256(json.dumps(triangle_records(description),
                                    separators=(',', ':')).encode()).hexdigest()


def isolated_corner_description(original, target, material_slot_names):
    """Clone exact native corner data with independent triangle topology."""
    records = triangle_records(original)
    if sorted({r['group'] for r in records}) != list(range(len(material_slot_names))):
        raise RuntimeError('Isolation requires dense ordered material groups')
    description = target.create_static_mesh_description()
    groups = []
    for name in material_slot_names:
        group = description.create_polygon_group()
        description.set_polygon_group_material_slot_name(group, name)
        groups.append(group)
    for record in records:
        instances = []
        for corner in record['corners']:
            vertex = description.create_vertex()
            description.set_vertex_position(vertex, unreal.Vector(*corner['position']))
            instance = description.create_vertex_instance(vertex)
            description.set_vertex_instance_uv(instance, unreal.Vector2D(*corner['uv']), 0)
            instances.append(instance)
        description.create_triangle(groups[record['group']], instances)
    if (description.get_vertex_count() != 3 * len(records)
            or triangle_signature(description) != triangle_signature(original)):
        raise RuntimeError('Isolation changed native triangle coordinates/UVs/winding/groups')
    return description


def isolated_wall_description(source, target):
    """Make a fresh description with three independent vertices per triangle.

    StaticMeshOperations computes normals per connected VertexID and soft-edge
    group. The original builder welds box boundaries without declaring hard
    edges. Isolating native triangles avoids cancellation at those boundaries;
    coordinates, UVs, winding and material assignments remain unchanged.
    """
    original = source.get_static_mesh_description(0)
    audit = triangle_uv_audit(original)
    if audit['degenerate_uv_count'] or audit['degenerate_geometry_count']:
        raise RuntimeError('Architecture isolation requires nondegenerate source triangles/UVs')
    subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    if subsystem.get_num_uv_channels(source, 0) != 1:
        raise RuntimeError('Architecture has additional UV channels requiring explicit cloning')
    materials = source.get_editor_property('static_materials')
    group_count = original.get_polygon_group_count()
    records = triangle_records(original)
    # The native probe verified this author's groups are dense and ordered
    # identically to LOD sections. Refuse any other layout instead of guessing.
    expected_groups = 3 if source.get_name() == 'SM_KL_Wall_700' else 2
    if (source.get_name() not in ISOLATED_ARCHITECTURE or group_count != expected_groups
            or source.get_num_sections(0) != group_count
            or sorted({r['group'] for r in records}) != list(range(group_count))):
        raise RuntimeError('Architecture material-group topology differs from verified layout')
    slot_indices = [subsystem.get_lod_material_slot(source, 0, i)
                    for i in range(group_count)]
    if (any(i < 0 or i >= len(materials) for i in slot_indices)
            or source.get_name() == 'SM_KL_Wall_700' and slot_indices != [0, 1, 2]):
        raise RuntimeError('Architecture section-to-material binding differs')
    return isolated_corner_description(original, target,
        [str(materials[i].material_slot_name) for i in slot_indices])


def regular_build(mesh, description):
    # The fast path reads normals/tangents verbatim and, in the installed cook
    # cache path, does not assign Bounds like the regular MeshBuilder does.
    # This flag is persisted; passing fast_build=False alone does not clear it
    # on a duplicate. Our fresh StaticMesh constructor defaults it to false.
    # The flag is not exposed by this engine's Python reflection.
    mesh.modify()
    if mesh.get_num_sections(0) > 0:
        raise RuntimeError('Never BuildFromDescriptions on an already built mesh')
    subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    # A fresh mesh has no LOD models until its first native description build.
    # That first build uses the engine constructor's recompute defaults; apply
    # explicit options and rebuild immediately afterward.
    mesh.build_from_static_mesh_descriptions([description],
                                             build_simple_collision=False,
                                             fast_build=False)
    options = subsystem.get_lod_build_settings(mesh, 0)
    settings = {'recompute_normals': True, 'recompute_tangents': True,
                'use_mikk_t_space': True, 'remove_degenerates': True,
                'use_full_precision_u_vs': True,
                'use_high_precision_tangent_basis': True,
                'generate_lightmap_u_vs': False}
    # PythonizeName can spell UVs differently between reflected versions.
    for key, value in settings.items():
        candidates = [key]
        if key == 'generate_lightmap_u_vs':
            candidates = ['generate_lightmap_u_vs', 'generate_lightmap_uvs']
        resolved = None
        for candidate in candidates:
            try:
                options.get_editor_property(candidate)
            except Exception:
                continue
            resolved = candidate
            break
        if resolved is None:
            raise RuntimeError('Build setting unavailable: ' + key)
        options.set_editor_property(resolved, value)
    subsystem.set_lod_build_settings(mesh, 0, options)
    # SetLodBuildSettings -> PostEditChange -> Build is the verified native path.
    # Native build is synchronous for this explicit description path; require
    # actual returned geometry bounds before saving or remapping any actor.
    result = bounds(mesh)
    if not result['finite'] or result['radius'] <= 0:
        raise RuntimeError('Regular build did not produce finite nonempty bounds')
    return result


class CorrectedDeckBuilder(M.MeshBuilder):
    def cylinder(self, slot, cx, cy, z0, z1, r, seg=12, uv_scale=1.0,
                 caps=True, axis='z', r_top=None):
        if axis != 'y':
            return super().cylinder(slot, cx, cy, z0, z1, r, seg,
                                    uv_scale, caps, axis, r_top)
        # Keep existing body points/UVs. In the original Y-cylinder helper the
        # body uses z0 as its Z centre, but cap centres erroneously use cy.
        super().cylinder(slot, cx, cy, z0, z1, r, seg,
                         uv_scale, False, axis, r_top)
        if not caps:
            return
        top_radius = r if r_top is None else r_top
        for index in range(seg):
            a0 = 2 * math.pi * index / seg
            a1 = 2 * math.pi * (index + 1) / seg
            def point(angle, radius, y):
                return (cx + radius * math.cos(angle), y,
                        z0 + radius * math.sin(angle))
            self.tri(slot, (cx, z1, z0), (.5, .5),
                     point(a0, top_radius, z1), (0, 0),
                     point(a1, top_radius, z1), (1, 0))
            self.tri(slot, (cx, z0, z0), (.5, .5),
                     point(a1, r, z0), (1, 0),
                     point(a0, r, z0), (0, 0))


def deck_description(mesh):
    # Compile only the authoring function, never import the original script:
    # importing it invokes its asset-writing main function.
    path = ROOT / 'Content/Python/KhoangLang/art_74_props.py'
    tree = ast.parse(path.read_text(encoding='utf-8'))
    function = next(n for n in tree.body
                    if isinstance(n, ast.FunctionDef) and n.name == 'prop_tapedeck')
    materials = mesh.get_editor_property('static_materials')
    if len(materials) != 3:
        raise RuntimeError('Unexpected cassette material slot layout')
    namespace = {'METAL': 'source_metal', 'RUST': 'source_rust',
                 'WOOD_DK': 'source_wood_dark'}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), 'exec'),
         namespace)
    builder = CorrectedDeckBuilder(mesh.get_name())
    builder._sm = mesh
    builder._desc = mesh.create_static_mesh_description()
    slots = {namespace[key]: str(materials[i].material_slot_name)
             for i, key in enumerate(('METAL', 'RUST', 'WOOD_DK'))}
    namespace['prop_tapedeck']()(builder, slots)
    return builder._desc


def buffer_audit(mesh):
    library = getattr(unreal, 'ProceduralMeshLibrary', None)
    if library is None or not hasattr(library, 'get_section_from_static_mesh'):
        return {'qualified': False,
                'reason': 'No exposed render-buffer reader; normals/tangents '
                          'recomputed by native builder but not read back'}
    # No plugin is installed/enabled by this script. Read buffers only if the
    # engine already exposes its native reader in this editor session.
    if not mesh.get_editor_property('allow_cpu_access'):
        return {'qualified': False, 'reason': 'Existing copy lacks CPU buffer access; '
                                              'will not rebuild it for inspection'}
    sections = []
    bad_positions, bad_normals, bad_tangents = [], [], []
    for index in range(mesh.get_num_sections(0)):
        vertices, triangles, normals, uvs, tangents = \
            library.get_section_from_static_mesh(mesh, 0, index)
        if not vertices:
            raise RuntimeError('Empty rendered mesh section: ' + str(index))
        if len(normals) != len(vertices) or len(tangents) != len(vertices):
            raise RuntimeError('Rendered section has incomplete normal/tangent buffers')
        for vertex_index, vertex in enumerate(vertices):
            if not finite(xyz(vertex)):
                bad_positions.append({'section': index, 'vertex': vertex_index,
                                      'position': xyz(vertex)})
        for vertex_index, normal in enumerate(normals):
            if not finite(xyz(normal)) or sum(c*c for c in xyz(normal)) < .5:
                bad_normals.append({'section': index, 'vertex': vertex_index,
                                    'normal': xyz(normal)})
        for vertex_index, tangent in enumerate(tangents):
            direction = xyz(tangent.tangent_x)
            if not finite(direction) or sum(c*c for c in direction) < .5:
                example = {'section': index, 'vertex': vertex_index,
                           'tangent': direction,
                           'length_squared': sum(c*c for c in direction)}
                if vertex_index < len(vertices):
                    example['position'] = xyz(vertices[vertex_index])
                if vertex_index < len(normals):
                    example['normal'] = xyz(normals[vertex_index])
                if vertex_index < len(uvs):
                    example['uv'] = [float(uvs[vertex_index].x),
                                     float(uvs[vertex_index].y)]
                bad_tangents.append(example)
        sections.append({'section': index, 'vertices': len(vertices),
                         'triangles': len(triangles)//3,
                         'normals': len(normals), 'tangents': len(tangents)})
    return {'qualified': not (bad_positions or bad_normals or bad_tangents),
            'sections': sections, 'invalid_position_count': len(bad_positions),
            'invalid_normal_count': len(bad_normals),
            'invalid_tangent_count': len(bad_tangents),
            'invalid_position_examples': bad_positions[:12],
            'invalid_normal_examples': bad_normals[:12],
            'invalid_tangent_examples': bad_tangents[:16]}


def existing_copy_audit(mesh, source, expected_positions, collision, double_sided,
                        expected_corner_signature=None):
    """Read-only reuse audit. A failure keeps the old asset intact."""
    description = mesh.get_static_mesh_description(0)
    actual_positions = vertex_audit(description)
    if expected_corner_signature is not None:
        if (actual_positions['vertices'] != 3 * expected_positions['triangles']
                or triangle_signature(description) != expected_corner_signature):
            raise RuntimeError('Existing copy lacks isolated, exactly preserved triangles')
    elif actual_positions != expected_positions:
        raise RuntimeError('Existing copy has unexpected positions/topology')
    if not bounds(mesh)['finite'] or bounds(mesh)['radius'] <= 0:
        raise RuntimeError('Existing copy bounds are invalid')
    source_slots = source.get_editor_property('static_materials')
    actual_slots = mesh.get_editor_property('static_materials')
    if len(source_slots) != len(actual_slots):
        raise RuntimeError('Existing copy material slot count differs')
    for original, actual in zip(source_slots, actual_slots):
        if str(original.material_slot_name) != str(actual.material_slot_name):
            raise RuntimeError('Existing copy material slot names differ')
        if original.material_interface == actual.material_interface:
            continue
        # Main's separate material-binding step can replace only the known
        # corresponding G1 copy. That is not a reason to rebuild geometry.
        if (original.material_interface is None or actual.material_interface is None
                or actual.material_interface.get_path_name().split('.')[0] !=
                BASE + '/Materials/' + original.material_interface.get_name()):
            raise RuntimeError('Existing copy has an unexpected material interface')
    body = mesh.get_editor_property('body_setup')
    if collision is not None:
        if (body is None or body.get_editor_property('collision_trace_flag') != collision
                or body.get_editor_property('double_sided_geometry') != double_sided):
            raise RuntimeError('Existing copy collision differs')
    buffers = buffer_audit(mesh)
    if not buffers['qualified']:
        raise RuntimeError('Existing copy strict buffer audit failed: ' + json.dumps(buffers))
    if source.get_name() == 'SM_KL_Prop_TapeDeck':
        sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        expected = {0: 192, 2: 200, 1: 36}
        actual = {sub.get_lod_material_slot(mesh, 0, s['section']): s['triangles']
                  for s in buffers['sections']}
        if actual != expected:
            raise RuntimeError('Existing cassette section materials differ from authored case/front/casing')
    return buffers


def main():
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if editor.get_game_world():
        raise RuntimeError('Stop PIE before mesh repair')
    world = editor.get_editor_world()
    if world is None or world.get_path_name().split('.')[0] != MAP:
        raise RuntimeError('Load isolated G1 school map')
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    report = {'status': 'started', 'map': MAP, 'meshes': [], 'actors': [],
              'clean_cook_verified': False, 'visual_accepted': False,
              'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    REPORT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    try:
        unreal.EditorAssetLibrary.make_directory(FOLDER)
        replacements = {}
        for source_path in SOURCES + [DECK]:
            source_hash = package_hash(source_path)
            source = unreal.load_asset(source_path)
            if not isinstance(source, unreal.StaticMesh):
                raise RuntimeError('Missing source mesh: ' + source_path)
            source_description = source.get_static_mesh_description(0)
            before_positions = vertex_audit(source_description)
            source_uv = triangle_uv_audit(source_description)
            source_body = source.get_editor_property('body_setup')
            collision_flag = (source_body.get_editor_property('collision_trace_flag')
                              if source_body else None)
            double_sided = (source_body.get_editor_property('double_sided_geometry')
                            if source_body else None)
            if collision_flag not in (None, unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE):
                raise RuntimeError('Source requires aggregate simple-collision cloning: ' + source_path)
            expected_description = (deck_description(source) if source_path == DECK
                                    else source_description)
            expected_positions = vertex_audit(expected_description)
            triangle_isolated = source.get_name() in ISOLATED_ARCHITECTURE or source_path == DECK
            expected_corner_signature = (triangle_signature(expected_description)
                                         if triangle_isolated else None)
            mesh = None
            reused = False
            preserved_candidates = []
            candidate_names = [source.get_name() + '_Regular'] + [
                source.get_name() + '_Regular_v%02d' % i for i in range(2, 17)]
            for name in candidate_names:
                destination = FOLDER + '/' + name
                candidate = unreal.load_asset(destination)
                if candidate is None:
                    mesh = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
                        name, FOLDER, unreal.StaticMesh, None)
                    break
                if unreal.EditorAssetLibrary.get_metadata_tag(candidate, 'G1MeshRepairOrigin') != source_path:
                    preserved_candidates.append({'copy': destination,
                                                 'reason': 'Not owned by this repair'})
                    continue
                try:
                    buffers = existing_copy_audit(candidate, source, expected_positions,
                                                  collision_flag, double_sided,
                                                  expected_corner_signature)
                except Exception as exc:
                    preserved_candidates.append({'copy': destination, 'reason': str(exc)})
                    continue
                mesh = candidate
                reused = True
                break
            if mesh is None:
                raise RuntimeError('No safe fresh or qualified copy destination available')
            if reused:
                # A previous failed run may leave a qualified but unsaved
                # UObject. Persist it before allowing the map to reference it.
                if not unreal.EditorAssetLibrary.save_loaded_asset(mesh, False):
                    raise RuntimeError('Qualified mesh persistence failed')
                replacements[source_path] = mesh
                replacements[destination] = mesh
                for candidate in preserved_candidates:
                    if candidate['reason'] != 'Not owned by this repair':
                        replacements[candidate['copy']] = mesh
                report['meshes'].append({'source': source_path, 'copy': destination,
                                         'action': 'REUSED_QUALIFIED_COPY_NO_REBUILD',
                                         'source_positions': before_positions,
                                         'rebuilt_positions': vertex_audit(
                                             mesh.get_static_mesh_description(0)),
                                         'source_triangle_uv_audit': source_uv,
                                         'bounds': bounds(mesh), 'buffer_audit': buffers,
                                         'source_package_sha256': source_hash,
                                         'collision': str(collision_flag),
                                         'preserved_candidates': preserved_candidates})
                continue
            mesh.modify()
            mesh.set_editor_property('static_materials',
                                      list(source.get_editor_property('static_materials')))
            unreal.EditorAssetLibrary.set_metadata_tag(mesh, 'G1MeshRepairOrigin', source_path)
            mesh.set_editor_property('allow_cpu_access', True)
            if source_path == DECK:
                corrected_description = deck_description(mesh)
                deck_slots = mesh.get_editor_property('static_materials')
                # The isolated authoring function creates groups in this exact
                # order: metal case, dark wood casing, rusty front panel.
                description = isolated_corner_description(corrected_description, mesh,
                    [str(deck_slots[i].material_slot_name) for i in (0, 2, 1)])
            elif source.get_name() in ISOLATED_ARCHITECTURE:
                description = isolated_wall_description(source, mesh)
            else:
                description = source_description
            after_positions = vertex_audit(description)
            if source_path != DECK and not triangle_isolated and before_positions != after_positions:
                raise RuntimeError('Architecture positions/topology changed during copy')
            triangle_preservation = ({'source': expected_corner_signature,
                                      'copy': triangle_signature(description)}
                                     if triangle_isolated else None)
            rebuilt_bounds = regular_build(mesh, description)
            if triangle_isolated and triangle_signature(mesh.get_static_mesh_description(0)) != \
                    triangle_preservation['source']:
                raise RuntimeError('Native build changed exact authored triangle data')
            body = mesh.get_editor_property('body_setup')
            if collision_flag is not None:
                if body is None:
                    raise RuntimeError('Copied collision body disappeared')
                body.modify()
                body.set_editor_property('collision_trace_flag', collision_flag)
                body.set_editor_property('double_sided_geometry', double_sided)
            if [m.material_slot_name for m in mesh.get_editor_property('static_materials')] != \
                    [m.material_slot_name for m in source.get_editor_property('static_materials')]:
                raise RuntimeError('Material slot names changed during rebuild')
            buffers = buffer_audit(mesh)
            entry = {'source': source_path, 'copy': destination,
                     'source_positions': before_positions,
                     'rebuilt_positions': after_positions,
                     'source_triangle_uv_audit': source_uv,
                     'bounds': rebuilt_bounds, 'buffer_audit': buffers,
                     'build_mode': 'Fresh constructor + native fast_build=False',
                     'source_package_sha256': source_hash,
                     'collision': str(collision_flag),
                     'action': 'BUILT_NEW_COPY',
                     'preserved_candidates': preserved_candidates,
                     'triangle_corner_signature': triangle_preservation,
                     'tangent_repair': 'Isolated triangle topology; native TBN recompute'
                         if triangle_isolated else None,
                     'geometry_change': 'Corrected Y-cylinder cap centres'
                         if source_path == DECK else 'None'}
            report['meshes'].append(entry)
            if buffers.get('invalid_tangent_count', 0):
                # A bounded native alternative, not a relaxed verification:
                # source UVs/geometry and normals must be valid first. Keep
                # the same strict finite/nonzero tangent audit afterward.
                if (source.get_name() != 'SM_KL_Wall_700'
                        or buffers.get('invalid_position_count', 0)
                        or buffers.get('invalid_normal_count', 0)
                        or source_uv['degenerate_uv_count']
                        or source_uv['degenerate_geometry_count']):
                    raise RuntimeError('Invalid tangents require a separate geometry/UV repair')
                entry['mikk_buffer_audit'] = buffers
                subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
                options = subsystem.get_lod_build_settings(mesh, 0)
                options.set_editor_property('use_mikk_t_space', False)
                subsystem.set_lod_build_settings(mesh, 0, options)
                native_options = subsystem.get_lod_build_settings(mesh, 0)
                if native_options.get_editor_property('use_mikk_t_space'):
                    raise RuntimeError('Native non-Mikk option did not take effect')
                if not all(native_options.get_editor_property(key) for key in
                           ('recompute_normals', 'recompute_tangents')):
                    raise RuntimeError('Native tangent/normal recompute became disabled')
                buffers = buffer_audit(mesh)
                entry['buffer_audit'] = buffers
                entry['tangent_repair'] = ('Isolated native triangle topology + '
                                         'non-Mikk recompute; geometry/UV unchanged')
                entry['bounds'] = bounds(mesh)
                if not entry['bounds']['finite']:
                    raise RuntimeError('Non-Mikk rebuild produced non-finite bounds')
            if (buffers.get('invalid_position_count', 0)
                    or buffers.get('invalid_normal_count', 0)
                    or buffers.get('invalid_tangent_count', 0)):
                raise RuntimeError('Native rendered position/normal/tangent audit failed')
            if not buffers.get('qualified'):
                raise RuntimeError('Native rendered buffer audit is unqualified')
            if sum(section['triangles'] for section in buffers['sections']) != \
                    after_positions['triangles']:
                raise RuntimeError('Native rendered build changed triangle count')
            if triangle_isolated:
                subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
                expected_slots = ([0, 2, 1] if source_path == DECK else
                    [subsystem.get_lod_material_slot(source, 0, i)
                     for i in range(source.get_num_sections(0))])
                # MeshBuilder orders render sections by material slot, while
                # the description retains authoring group order. Verify the
                # actual triangle population per bound material, not ordering.
                expected_counts = {}
                for section_index, slot in enumerate(expected_slots):
                    subsystem.set_lod_material_slot(mesh, material_slot_index=slot,
                        lod_index=0, section_index=section_index)
                for record in triangle_records(description):
                    slot = expected_slots[record['group']]
                    expected_counts[slot] = expected_counts.get(slot, 0) + 1
                actual_counts = {}
                for section in buffers['sections']:
                    slot = subsystem.get_lod_material_slot(mesh, 0, section['section'])
                    actual_counts[slot] = actual_counts.get(slot, 0) + section['triangles']
                entry['triangles_by_material_slot'] = actual_counts
                if actual_counts != expected_counts:
                    raise RuntimeError('Triangle material binding changed during build')
            if not unreal.EditorAssetLibrary.save_loaded_asset(mesh, False):
                raise RuntimeError('Copied mesh save failed')
            if package_hash(source_path) != source_hash:
                raise RuntimeError('Source package changed unexpectedly: ' + source_path)
            replacements[source_path] = mesh
            replacements[destination] = mesh
            for candidate in preserved_candidates:
                if candidate['reason'] != 'Not owned by this repair':
                    replacements[candidate['copy']] = mesh
        world.modify()
        for actor in actor_subsystem.get_all_level_actors():
            for component in actor.get_components_by_class(unreal.StaticMeshComponent):
                old = component.get_editor_property('static_mesh')
                if old is None:
                    if actor.get_actor_label() == 'G1_ListeningDeck':
                        replacement = replacements[DECK]
                        actor.modify()
                        component.modify()
                        component.set_static_mesh(replacement)
                        report['actors'].append({'actor': actor.get_actor_label(),
                            'mesh': replacement.get_path_name(), 'restored_missing_owned_copy': True})
                    continue
                replacement = replacements.get(old.get_path_name().split('.')[0])
                if replacement is None:
                    continue
                overrides = list(component.get_editor_property('override_materials'))
                collision = component.get_collision_enabled()
                actor.modify()
                component.modify()
                if old != replacement and not component.set_static_mesh(replacement):
                    raise RuntimeError('Actor mesh remap failed: ' + actor.get_actor_label())
                component.set_editor_property('override_materials', overrides)
                if component.get_collision_enabled() != collision:
                    raise RuntimeError('Actor collision mode changed during remap')
                report['actors'].append({'actor': actor.get_actor_label(),
                                         'mesh': replacement.get_path_name(),
                                         'collision': str(collision)})
        if not report['actors']:
            raise RuntimeError('No affected G1 actors were remapped')
        if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAP):
            raise RuntimeError('G1 repaired map save failed')
        report['status'] = 'COPIES_REBUILT_MAP_SAVED_COOK_UNVERIFIED'
    except Exception as exc:
        report['status'] = 'FAILED'
        report['error'] = str(exc)
        raise
    finally:
        REPORT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'status': report['status'], 'meshes': len(report['meshes']),
                      'actors': len(report['actors']), 'clean_cook_verified': False}))


if __name__ == '__main__':
    main()
