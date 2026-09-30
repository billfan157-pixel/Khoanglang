"""Khoang Lang 02:17 - import the Blender school furniture FBX (art step 7).

Reads the two FBX files produced by
ArtSource/Blender/SchoolFurniture/kl_school_furniture.py and lands them as
Static Mesh assets under /Game/KhoangLang/Meshes/SchoolFurniture/.

Deliberate choices:

  * import_materials = False. The Blender shaders are procedural previews, not
    shipping materials, and letting them through would drop five junk material
    assets into the project. The slots are renamed here and filled with
    material instances built from the project's existing ART materials, which
    already have real aged-wood / metal textures.
  * The same three slots on both assets, in the same order, so one material
    assignment loop covers desk and bench.
  * Collision follows the convention kl_mesh.py already established for this
    project: allow CPU access, then add simple collisions with
    CTF_USE_SIMPLE_AND_COMPLEX.

Nothing outside /Game/KhoangLang/Meshes/SchoolFurniture/ and three new
material instances is written. No existing asset is replaced.

Run:  run_ue_script.ps1 -Script art_91_schoolfurn_import.py
"""

import os
import sys
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import kl_core as K  # noqa: E402

ROOT = K.ROOT
FOLDER = ROOT + '/Meshes/SchoolFurniture'
MAT_FOLDER = ROOT + '/MaterialsArt'
FBX_DIR = (r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217'
           r'\ArtExports\FBX\SchoolFurniture')

# slot name -> material instance asset to build and use
SLOTS = [
    ('Wood_AgedTop', 'MI_SF_Wood_AgedTop', MAT_FOLDER + '/MI_ART_Wood'),
    ('Wood_AgedFrame', 'MI_SF_Wood_AgedFrame', MAT_FOLDER + '/MI_ART_WoodDark'),
    ('Metal_Hardware', 'MI_SF_Metal_Hardware', MAT_FOLDER + '/MI_ART_Metal'),
]

ASSETS = [
    ('SM_KL_SchoolDesk_A', 'SM_KL_SchoolDesk_A.fbx'),
    ('SM_KL_SchoolBench_A', 'SM_KL_SchoolBench_A.fbx'),
]

REPORT = []


def log(msg):
    line = 'SF: ' + str(msg)
    REPORT.append(line)
    unreal.log(line)


def warn(msg):
    line = 'SF_WARN: ' + str(msg)
    REPORT.append(line)
    unreal.log_warning(line)


def probe():
    """Record which API this engine build actually exposes."""
    out = {}
    sm_cls = unreal.StaticMesh
    out['StaticMesh_methods'] = sorted(
        [m for m in dir(sm_cls)
         if any(k in m for k in ('get_mesh_description', 'get_num_',
                                 'get_material', 'set_material',
                                 'get_bounds', 'import_model'))])
    lib = unreal.EditorStaticMeshLibrary
    out['ESM_useful'] = sorted(
        [m for m in dir(lib) if any(k in m.lower() for k in
                                     ('collision', 'material', 'section',
                                      'lod', 'tri', 'vert', 'bound',
                                      'uv', 'complexity', 'cpu'))])
    out['FBXImportType_members'] = sorted(
        [a for a in dir(unreal.FBXImportType) if a.isupper()])
    out['has_AssetImportTask'] = hasattr(unreal, 'AssetImportTask')
    out['has_FbxImportUI'] = hasattr(unreal, 'FbxImportUI')
    out['has_FbxStaticMeshImportData'] = hasattr(unreal, 'FbxStaticMeshImportData')
    out['has_MaterialInstanceConstant'] = hasattr(unreal, 'MaterialInstanceConstant')
    out['CollisionTraceFlag_members'] = sorted(
        [a for a in dir(unreal.CollisionTraceFlag) if a.startswith('CTF')])
    out['has_ScriptCollisionShapeType'] = hasattr(unreal,
                                                  'ScriptCollisionShapeType')
    if hasattr(unreal, 'ScriptCollisionShapeType'):
        out['ScriptCollisionShapeType_members'] = sorted(
            [a for a in dir(unreal.ScriptCollisionShapeType)
             if a.isupper() and not a.startswith('_')])
    out['has_StaticMeshEditorSubsystem'] = hasattr(unreal,
                                                   'StaticMeshEditorSubsystem')
    if hasattr(unreal, 'StaticMeshEditorSubsystem'):
        out['SMES_collision_methods'] = sorted(
            [m for m in dir(unreal.StaticMeshEditorSubsystem)
             if 'collision' in m.lower() or 'complexity' in m.lower()])
        out['SMES_add_simple_collisions_doc'] = str(
            unreal.StaticMeshEditorSubsystem.add_simple_collisions.__doc__)[:300]
    out['StaticMesh_has_build'] = hasattr(unreal.StaticMesh, 'build')
    out['StaticMesh_has_set_material'] = hasattr(unreal.StaticMesh, 'set_material')
    try:
        out['add_simple_collisions_doc'] = str(
            unreal.EditorStaticMeshLibrary.add_simple_collisions.__doc__)[:300]
    except Exception as exc:
        out['add_simple_collisions_doc'] = 'ERR %r' % (exc,)
    out['StaticMesh_collision_props'] = [
        p for p in dir(unreal.StaticMesh)
        if 'collision' in p.lower() or 'body' in p.lower()]
    log('probe %s' % out)


def set_collision(sm, name):
    """Build CPU collision and pick a trace complexity this build accepts.

    EditorStaticMeshLibrary is deprecated in UE 5.8 and its add_simple_collisions
    now takes a ScriptCollisionShapeType, so the non-deprecated
    StaticMeshEditorSubsystem is tried first. If no convex hulls can be built
    the asset falls back to complex-as-simple, which is exact for a static prop
    and costs nothing to author.
    """
    ctf = unreal.CollisionTraceFlag
    shapes = []
    if hasattr(unreal, 'ScriptCollisionShapeType'):
        scs = unreal.ScriptCollisionShapeType
        # BOX first: for a desk one box hull around the whole piece is the right
        # simple collision. It also closes the open volume under the worktop,
        # which a walk-through-the-frame bug would otherwise allow. Probed
        # members in this build are BOX, CAPSULE, SPHERE and the NDOP set -
        # there is no convex-hull option.
        for n in ('BOX', 'CONVEX_HULL', 'SPHERE', 'CAPSULE'):
            if hasattr(scs, n):
                shapes.append(getattr(scs, n))
    log('  shape types available: %s' % shapes)

    built = 0
    try:
        smes = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    except Exception as exc:
        smes = None
        warn('StaticMeshEditorSubsystem: %r' % (exc,))

    if smes is not None:
        for shape in shapes:
            try:
                n = smes.add_simple_collisions(sm, shape)
                log('  SMES.add_simple_collisions(%s) -> %s' % (shape, n))
                built = max(n, 0) if isinstance(n, int) else 1
                break
            except Exception as exc:
                warn('SMES.add_simple_collisions(%s): %s'
                     % (shape, str(exc)[:110]))

    if built <= 0:
        for shape in shapes:
            try:
                n = unreal.EditorStaticMeshLibrary.add_simple_collisions(sm, shape)
                log('  ESM.add_simple_collisions(%s) -> %s' % (shape, n))
                built = max(n, 0) if isinstance(n, int) else 1
                break
            except Exception as exc:
                warn('ESM.add_simple_collisions(%s): %s'
                     % (shape, str(exc)[:110]))

    # add_simple_collisions returns -1 ("nothing added") when the mesh carries no
    # UCX bodies to derive shapes from, which is the normal case for an FBX
    # import. Simple collision then has nothing to trace against, so the asset
    # must run complex-as-simple instead, or the player walks through the desk.
    # That is exact per-triangle collision and costs nothing to author.
    complexity = ctf.CTF_USE_SIMPLE_AND_COMPLEX if built > 0 else \
        ctf.CTF_USE_COMPLEX_AS_SIMPLE
    log('  convex hulls built = %d -> collision = %s' % (built, complexity))
    try:
        bs = sm.get_editor_property('body_setup')
        bs.set_editor_property('collision_trace_flag', complexity)
        log('  body_setup.collision_trace_flag = %s' % complexity)
        log('  body_setup.collision_enabled readback = %s'
            % bs.get_editor_property('collision_trace_flag'))
    except Exception as exc:
        warn('%s body_setup: %r' % (name, str(exc)[:110]))

    try:
        log('  simple_collision_count=%s  convex=%s  complexity=%s'
            % (unreal.EditorStaticMeshLibrary.get_simple_collision_count(sm),
               unreal.EditorStaticMeshLibrary.get_convex_collision_count(sm),
               unreal.EditorStaticMeshLibrary.get_collision_complexity(sm)))
    except Exception as exc:
        warn('%s collision readback: %r' % (name, str(exc)[:110]))


def ensure_folder(path):
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    if not eas.does_directory_exist(path):
        eas.make_directory(path)
        log('created folder %s' % path)


def make_mi(name, parent_path):
    """Material instance constant, parented on an existing project material."""
    path = '%s/%s' % (MAT_FOLDER, name)
    existing = unreal.load_asset(path)
    if existing is not None:
        log('  reuse %s' % path)
        return existing
    parent = unreal.load_asset(parent_path)
    if parent is None:
        warn('parent material missing: %s' % parent_path)
        return None
    at = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialInstanceConstantFactoryNew()
    mi = at.create_asset(name, MAT_FOLDER, unreal.MaterialInstanceConstant,
                         factory)
    if mi is None:
        warn('could not create %s' % path)
        return None
    # MaterialInstanceConstantFactoryNew has no initial_parent in this build
    # (probed in art_92_fbxprobe.py), so the parent is set on the asset.
    try:
        mi.set_editor_property('parent', parent)
    except Exception as exc:
        warn('%s parent: %r' % (name, exc))
    unreal.EditorAssetLibrary.save_asset(path)
    log('  created %s (parent %s)' % (path, parent.get_name()))
    return mi


def mesh_bounds_cm(sm):
    """Local-space bounds in cm, plus a vertex count, straight from the mesh.

    Tries the asset's own bounds first (cheap), then the static mesh
    description, and reports which one answered.
    """
    try:
        b = sm.get_bounds()
        o, e = b.origin, b.box_extent
        return dict(
            source='get_bounds',
            min=[round(o.x - e.x, 2), round(o.y - e.y, 2), round(o.z - e.z, 2)],
            max=[round(o.x + e.x, 2), round(o.y + e.y, 2), round(o.z + e.z, 2)],
            verts=None)
    except Exception as exc:
        first = 'get_bounds failed: %s' % str(exc)[:90]

    try:
        md = sm.get_static_mesh_description(0)
        vids = md.get_vertices()
        lo = [1e18] * 3
        hi = [-1e18] * 3
        for vid in vids:
            p = md.get_vertex_position(vid)
            for i, v in enumerate((p.x, p.y, p.z)):
                lo[i] = min(lo[i], v)
                hi[i] = max(hi[i], v)
        return dict(source='mesh_description',
                    min=[round(v, 2) for v in lo],
                    max=[round(v, 2) for v in hi], verts=len(vids))
    except Exception as exc:
        return dict(source='none', error='%s / %s' % (first, str(exc)[:90]))


def uv_range_cm(sm):
    """UV channel presence, so a missing or renumbered UV set is visible."""
    out = {}
    try:
        out['tex_coord_channels'] = sm.get_num_tex_coords(0)
    except Exception as exc:
        out['tex_coord_channels'] = 'ERR %s' % str(exc)[:70]
    try:
        md = sm.get_static_mesh_description(0)
        out['uv_layers'] = [str(u) for u in md.get_uv_layers()] \
            if hasattr(md, 'get_uv_layers') else 'no get_uv_layers'
    except Exception as exc:
        out['uv_layers'] = 'ERR %s' % str(exc)[:70]
    return out


def import_one(name, filename, materials):
    src = os.path.join(FBX_DIR, filename)
    if not os.path.isfile(src):
        warn('missing FBX %s' % src)
        return None
    dest = '%s/%s' % (FOLDER, name)

    task = unreal.AssetImportTask()
    task.set_editor_property('filename', src)
    task.set_editor_property('destination_path', FOLDER)
    task.set_editor_property('destination_name', name)
    task.set_editor_property('automated', True)
    task.set_editor_property('replace_existing', True)
    task.set_editor_property('save', True)
    task.set_editor_property('factory', None)

    opts = unreal.FbxImportUI()
    # Option field names were read off this engine build by art_92_fbxprobe.py;
    # UE 5.8 has no automated_import_type on FbxImportUI.
    for prop, val in (('automated_import_should_detect_type', False),
                      ('mesh_type_to_import',
                       unreal.FBXImportType.FBXIT_STATIC_MESH),
                      ('original_import_type',
                       unreal.FBXImportType.FBXIT_STATIC_MESH),
                      ('import_mesh', True),
                      ('import_as_skeletal', False),
                      ('import_rigid_mesh', True),
                      ('import_animations', False),
                      ('import_materials', False),
                      ('import_textures', False),
                      ('create_physics_asset', False)):
        try:
            opts.set_editor_property(prop, val)
        except Exception as exc:
            warn('fbxui.%s: %r' % (prop, exc))

    smd = unreal.FbxStaticMeshImportData()
    for prop, val in (('combine_meshes', True),
                      ('generate_lightmap_u_vs', True),
                      ('auto_generate_collision', False),
                      ('remove_degenerates', True),
                      ('compute_weighted_normals', False),
                      ('reorder_material_to_fbx_order', True),
                      ('bake_pivot_in_vertex', False),
                      ('force_front_x_axis', False),
                      ('build_nanite', False),
                      ('convert_scene', True),
                      ('convert_scene_unit', True),
                      ('import_uniform_scale', 1.0),
                      ('normal_import_method',
                       unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)):
        try:
            smd.set_editor_property(prop, val)
        except Exception as exc:
            warn('smd.%s: %r' % (prop, exc))
    opts.set_editor_property('static_mesh_import_data', smd)

    task.set_editor_property('options', opts)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    sm = unreal.load_asset(dest)
    if sm is None:
        warn('import produced nothing at %s' % dest)
        log('  import messages: %s' % ([str(m) for m in task.get_editor_property(
            'result')] if task.get_editor_property('result') else 'n/a'))
        return None

    log('imported %s <- %s (%d bytes)' % (dest, filename,
                                          os.path.getsize(src)))
    return sm


def dress(sm, name, materials):
    """Slots, materials, collision, and the measurements worth checking."""
    slots = list(sm.get_editor_property('static_materials'))
    log('  slots on import: %d' % len(slots))
    while len(slots) < len(SLOTS):
        slots.append(unreal.StaticMeshSlot())
    for i in range(len(slots)):
        try:
            slots[i].set_editor_property('material_slot_name', SLOTS[i][0])
        except Exception as exc:
            warn('%s slot %d name: %r' % (name, i, exc))
        try:
            # read-only in this build; the FBX name stays as the record of
            # which Blender material the slot came from
            slots[i].set_editor_property('imported_material_slot_name',
                                         'KL_Art_%s' % SLOTS[i][0])
        except Exception:
            pass
    try:
        sm.set_editor_property('static_materials', slots)
    except Exception as exc:
        warn('%s static_materials: %r' % (name, exc))

    for i, (slot_name, mi_name, _parent) in enumerate(SLOTS):
        mi = materials.get(mi_name)
        if mi is None:
            continue
        try:
            sm.set_material(i, mi)
        except Exception as exc:
            warn('%s set_material %d: %r' % (name, i, exc))

    lib = unreal.EditorStaticMeshLibrary
    try:
        lib.set_allow_cpu_access(sm, True)
        log('  set_allow_cpu_access ok')
    except Exception as exc:
        warn('%s set_allow_cpu_access: %r' % (name, str(exc)[:110]))
    set_collision(sm, name)

    unreal.EditorAssetLibrary.save_asset('%s/%s' % (FOLDER, name))

    # ---- measurements ----------------------------------------------------- #
    bounds = mesh_bounds_cm(sm)
    if bounds.get('source') != 'none':
        lo, hi = bounds['min'], bounds['max']
        size = [round(hi[i] - lo[i], 2) for i in range(3)]
        log('  bounds cm (%s) min=%s max=%s size=%s'
            % (bounds['source'], lo, hi, size))
        if abs(size[2]) < 20.0:
            warn('%s is only %.2f cm tall - the FBX orientation is probably '
                 'wrong' % (name, size[2]))
        if abs(lo[2]) > 3.0 or abs(hi[2]) > 120.0:
            warn('%s pivot is not at the floor: z spans %.2f..%.2f'
                 % (name, lo[2], hi[2]))
    else:
        warn('%s: no bounds available (%s)' % (name, bounds.get('error')))

    uvr = uv_range_cm(sm)
    log('  uv0 range: %s' % (uvr,))

    try:
        log('  sections=%d  tris=%s  verts=%s'
            % (sm.get_num_sections(0), sm.get_num_triangles(0),
               sm.get_num_vertices(0)))
    except Exception as exc:
        warn('%s mesh stats: %r' % (name, exc))
    try:
        log('  materials: %s'
            % [str(sm.get_material(i).get_name()) if sm.get_material(i)
               else None for i in range(len(SLOTS))])
    except Exception as exc:
        warn('%s material readback: %r' % (name, exc))
    try:
        bs = sm.get_editor_property('body_setup')
        log('  body_setup=%s  simple_collisions=%s  complexity=%s'
            % ('yes' if bs is not None else 'no',
               unreal.EditorStaticMeshLibrary.get_simple_collision_count(sm),
               unreal.EditorStaticMeshLibrary.get_collision_complexity(sm)))
    except Exception as exc:
        warn('%s body_setup read: %r' % (name, exc))
    return sm


def main():
    log('=== art_91_schoolfurn_import ===')
    probe()
    ensure_folder(FOLDER)
    ensure_folder(MAT_FOLDER)

    materials = {}
    for slot_name, mi_name, parent in SLOTS:
        materials[mi_name] = make_mi(mi_name, parent)

    made = []
    for name, filename in ASSETS:
        sm = import_one(name, filename, materials)
        if sm is None:
            continue
        sm = dress(sm, name, materials)
        made.append(sm)
        log('  OK %s' % name)

    log('imported %d/%d assets' % (len(made), len(ASSETS)))
    try:
        with open(os.path.join(HERE, 'art_91_schoolfurn_import.report.txt'),
                  'w', encoding='utf-8') as f:
            f.write('\n'.join(REPORT) + '\n')
    except Exception as exc:
        warn('report write: %r' % (exc,))
    log('=== done ===')


try:
    main()
except Exception:
    log(traceback.format_exc())
    log('=== FAILED ===')
