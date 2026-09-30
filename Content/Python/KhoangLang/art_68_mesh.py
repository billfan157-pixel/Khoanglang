"""Art pass probe 68: can material slots be created on a built StaticMesh?

Probe 67: set_polygon_group_material_slot_name() does NOT create a real
material slot (get_number_materials -> 0) even though get_num_sections() -> 2.
Need a route that actually assigns materials, either on the asset (so a
multi-material kit piece works) or per-actor via override_materials.
"""

import os
import traceback

import unreal

OUT = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\art68'
os.makedirs(OUT, exist_ok=True)
REP = os.path.join(OUT, 'report.txt')


def p(m=''):
    line = str(m)
    unreal.log('A68: ' + line)
    with open(REP, 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


def guard(label, fn, *a, **kw):
    try:
        r = fn(*a, **kw)
        p('  %s -> %r' % (label, r))
        return r
    except Exception as exc:
        p('  ! %s -> %r' % (label, str(exc)[:200]))
        return None


def main():
    at = unreal.AssetToolsHelpers.get_asset_tools()
    ESM = unreal.EditorStaticMeshLibrary
    p('=== A. StaticMesh material API signatures ===')
    for n in ('add_material', 'set_material', 'get_material', 'get_material_index',
              'get_num_sections', 'get_static_materials'):
        d = (getattr(unreal.StaticMesh, n).__doc__ or '')[:260].replace('\r\n', ' ') \
            if hasattr(unreal.StaticMesh, n) else 'MISSING'
        p('  .%s -> %s' % (n, d))

    p('')
    p('=== B. build a 2-section mesh ===')
    path = '/Game/KhoangLang/ArtTest/A68_Two'
    if unreal.load_asset(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    sm = at.create_asset('A68_Two', '/Game/KhoangLang/ArtTest', unreal.StaticMesh, None)
    md = sm.create_static_mesh_description()
    for slot, cx in (('KL_Wood', 0.0), ('KL_Metal', 200.0)):
        g = md.create_polygon_group()
        md.set_polygon_group_material_slot_name(g, slot)
        md.create_cube(unreal.Vector(cx, 0, 50), unreal.Vector(50, 20, 50), g)
    guard('build', sm.build_from_static_mesh_descriptions, [md])
    guard('save', unreal.EditorAssetLibrary.save_asset, path)
    p('  sections=%s  materials=%s' % (
        sm.get_num_sections(0), ESM.get_number_materials(sm)))

    p('')
    p('=== C. add_material ===')
    miw = unreal.load_asset('/Game/KhoangLang/MaterialsArt/MI_ART_Wood')
    mim = unreal.load_asset('/Game/KhoangLang/MaterialsArt/MI_ART_MetalRust')
    p('  assets: wood=%s metal=%s' % (miw is not None, mim is not None))
    guard('add_material(0, wood)', sm.add_material, 0, miw)
    p('  materials now = %s' % ESM.get_number_materials(sm))
    p('  get_material(0) = %s' % sm.get_material(0))
    guard('add_material(1, metal)', sm.add_material, 1, mim)
    p('  materials now = %s' % ESM.get_number_materials(sm))
    p('  get_material(0) = %s' % sm.get_material(0))
    p('  get_material(1) = %s' % sm.get_material(1))
    guard('save', unreal.EditorAssetLibrary.save_asset, path)

    p('')
    p('=== D. survives reload? ===')
    del sm
    again = unreal.load_asset(path)
    p('  reloaded sections=%s materials=%s' % (
        again.get_num_sections(0), ESM.get_number_materials(again)))
    p('  slot0=%s' % again.get_material(0))
    p('  slot1=%s' % again.get_material(1))

    p('')
    p('=== E. section -> slot mapping (does section N use material N?) ===')
    for n in range(2):
        p('  enable_section_collision(%d) -> %r' % (n, guard(
            'esc', ESM.enable_section_collision, again, n, True)))
    p('  is_section_collision_enabled(0)=%s (1)=%s' % (
        guard('i0', ESM.is_section_collision_enabled, again, 0),
        guard('i1', ESM.is_section_collision_enabled, again, 1)))
    guard('save', unreal.EditorAssetLibrary.save_asset, path)

    p('')
    p('=== F. collision for the asset ===')
    p('  ESM.get_collision_complexity = %s' % guard('cc',
                                                    ESM.get_collision_complexity, again))
    p('  add_simple_collisions -> %s' % guard('asc', ESM.add_simple_collisions,
                                              again))
    p('  simple collision count = %s' % guard('scc',
                                              ESM.get_simple_collision_count, again))
    guard('save', unreal.EditorAssetLibrary.save_asset, path)

    p('')
    p('=== G. generate_lightmap_uvs via the library ===')
    p('  ESM.set_generate_lightmap_uv(again, True) -> %r' % guard('glu',
                                                                 ESM.set_generate_lightmap_uv,
                                                                 again, True))
    p('  light_map_coordinate_index = %s' % guard('lmci', again.get_editor_property,
                                                 'light_map_coordinate_index'))

    p('')
    p('=== H. place in a level and check the COMPONENT sees the materials ===')
    mpath = '/Game/KhoangLang/Maps/A68_TestMap'
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.make_directory('/Game/KhoangLang/Maps')
    if unreal.load_asset(mpath):
        unreal.EditorAssetLibrary.delete_asset(mpath)
    guard('new_level', unreal.EditorLevelLibrary.new_level, mpath)
    from editor_toolset.toolsets import scene as SCENE
    tr = unreal.Transform()
    tr.set_editor_property('translation', unreal.Vector(0, 0, 50))
    tr.set_editor_property('scale3d', unreal.Vector(1, 1, 1))
    a = guard('spawn', SCENE.SceneTools.add_to_scene_from_class,
              unreal.StaticMeshActor.static_class(), 'A68_Act', tr)
    if a:
        from editor_toolset.toolsets import actor as ACT
        for c in ACT.ActorTools.get_components(a):
            if 'StaticMesh' in c.get_class().get_name():
                p('  component static_mesh = %s' % c.get_editor_property('static_mesh'))
                p('  component override = %s' % c.get_editor_property('override_materials'))
                p('  component num materials = %s' % c.get_num_materials())
                guard('set_static_mesh', c.set_editor_property, 'static_mesh', again)
                p('  after set: num materials = %s' % c.get_num_materials())
                guard('set_override', c.set_editor_property, 'override_materials',
                      [miw, mim])
                p('  after override: %s' % c.get_editor_property('override_materials'))
    guard('save level', unreal.EditorAssetLibrary.save_asset, mpath)

    p('')
    p('=== I. cleanup ===')
    for pp in (path, mpath):
        if unreal.load_asset(pp):
            unreal.EditorAssetLibrary.delete_asset(pp)
    p('DONE')


if os.path.exists(REP):
    os.remove(REP)
try:
    main()
except Exception:
    p(traceback.format_exc())
    p('A68_FATAL')
