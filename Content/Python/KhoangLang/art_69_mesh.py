"""Art pass probe 69: lock down the production mesh recipe.

Established so far:
  * authoring: create_vertex / set_vertex_position / create_vertex_instance /
    set_vertex_instance_uv / create_triangle / create_cube  (create_polygon crashes)
  * build: StaticMesh.build_from_static_mesh_descriptions([desc])
  * add_material(material) takes ONE arg, returns the slot Name

Still to settle: the exact sequence that produces a multi-material asset whose
materials actually render, and whether override_materials reads back.
"""

import os
import traceback

import unreal

OUT = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\art69'
os.makedirs(OUT, exist_ok=True)
REP = os.path.join(OUT, 'report.txt')


def p(m=''):
    line = str(m)
    unreal.log('A69: ' + line)
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
    miw = unreal.load_asset('/Game/KhoangLang/MaterialsArt/MI_ART_Wood')
    mim = unreal.load_asset('/Game/KhoangLang/MaterialsArt/MI_ART_MetalRust')
    mid = unreal.load_asset('/Game/KhoangLang/MaterialsArt/MI_ART_WoodDark')

    p('=== A. add_material BEFORE the build (slots first, then geometry) ===')
    p1 = '/Game/KhoangLang/ArtTest/A69_A'
    if unreal.load_asset(p1):
        unreal.EditorAssetLibrary.delete_asset(p1)
    sm = at.create_asset('A69_A', '/Game/KhoangLang/ArtTest', unreal.StaticMesh, None)
    n0 = guard('add_material(wood)', sm.add_material, miw)
    n1 = guard('add_material(metal)', sm.add_material, mim)
    p('  slot names: %r %r  count=%s' % (n0, n1, ESM.get_number_materials(sm)))
    md = sm.create_static_mesh_description()
    p('  desc groups after add_material: %d' % md.get_polygon_group_count())
    for i, (cx, hy) in enumerate(((0.0, 20.0), (200.0, 10.0))):
        g = md.create_polygon_group()
        md.set_polygon_group_material_slot_name(g, str(n0 if i == 0 else n1))
        md.create_cube(unreal.Vector(cx, 0, 50), unreal.Vector(50, hy, 50), g)
    guard('build', sm.build_from_static_mesh_descriptions, [md])
    guard('save', unreal.EditorAssetLibrary.save_asset, p1)
    p('  after build: materials=%s sections=%s' % (ESM.get_number_materials(sm),
                                                  sm.get_num_sections(0)))
    p('  slot0=%s' % sm.get_material(0))
    p('  slot1=%s' % sm.get_material(1))
    p('  index of %r = %s' % (n0, guard('gmi', sm.get_material_index, n0)))
    p('  index of %r = %s' % (n1, guard('gmi', sm.get_material_index, n1)))

    p('')
    p('=== B. add_material AFTER the build ===')
    p2 = '/Game/KhoangLang/ArtTest/A69_B'
    if unreal.load_asset(p2):
        unreal.EditorAssetLibrary.delete_asset(p2)
    sm2 = at.create_asset('A69_B', '/Game/KhoangLang/ArtTest', unreal.StaticMesh, None)
    md2 = sm2.create_static_mesh_description()
    for i, cx in enumerate((0.0, 200.0)):
        g = md2.create_polygon_group()
        md2.set_polygon_group_material_slot_name(g, 'Slot%d' % i)
        md2.create_cube(unreal.Vector(cx, 0, 50), unreal.Vector(50, 20, 50), g)
    guard('build', sm2.build_from_static_mesh_descriptions, [md2])
    p('  before: materials=%s' % ESM.get_number_materials(sm2))
    b0 = guard('add_material(wood)', sm2.add_material, miw)
    b1 = guard('add_material(metal)', sm2.add_material, mim)
    p('  after: materials=%s names=%r %r' % (ESM.get_number_materials(sm2), b0, b1))
    guard('set_material(0, wood)', sm2.set_material, 0, miw)
    guard('set_material(1, metal)', sm2.set_material, 1, mim)
    guard('save', unreal.EditorAssetLibrary.save_asset, p2)
    p('  slot0=%s slot1=%s' % (sm2.get_material(0), sm2.get_material(1)))

    p('')
    p('=== C. reload both, confirm persistence ===')
    for path, tag in ((p1, 'A'), (p2, 'B')):
        m = unreal.load_asset(path)
        p('  %s: materials=%s sections=%s slot0=%s slot1=%s' % (
            tag, ESM.get_number_materials(m), m.get_num_sections(0),
            m.get_material(0), m.get_material(1)))

    p('')
    p('=== D. component override_materials readback with a real mesh ===')
    p('  (art_30_level.py already relies on this; confirm it lands)')
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.make_directory('/Game/KhoangLang/Maps')
    mp = '/Game/KhoangLang/Maps/A69_Map'
    if unreal.load_asset(mp):
        unreal.EditorAssetLibrary.delete_asset(mp)
    guard('new_level', unreal.EditorLevelLibrary.new_level, mp)
    from editor_toolset.toolsets import scene as SCENE
    from editor_toolset.toolsets import actor as ACT
    tr = unreal.Transform()
    tr.set_editor_property('translation', unreal.Vector(0, 0, 50))
    tr.set_editor_property('scale3d', unreal.Vector(1, 1, 1))
    a = guard('spawn', SCENE.SceneTools.add_to_scene_from_class,
              unreal.StaticMeshActor.static_class(), 'A69_Act', tr)
    m = unreal.load_asset(p1)
    for c in ACT.ActorTools.get_components(a):
        if 'StaticMesh' in c.get_class().get_name():
            guard('set static_mesh', c.set_editor_property, 'static_mesh', m)
            p('  num materials after mesh = %s' % c.get_num_materials())
            guard('set override', c.set_editor_property, 'override_materials', [mid, mim])
            p('  override readback = %s' % c.get_editor_property('override_materials'))
            p('  num materials = %s' % c.get_num_materials())
            for i in range(2):
                p('  comp material %d = %s' % (i, c.get_material(i)))
            guard('collision', c.set_collision_enabled,
                  unreal.CollisionEnabled.QUERY_AND_PHYSICS)
            p('  collision now = %s' % c.get_collision_enabled())
    guard('save level', unreal.EditorAssetLibrary.save_asset, mp)

    p('')
    p('=== E. does a reloaded level keep the material? ===')
    guard('reload level', unreal.EditorLevelLibrary.load_level, mp)
    w = unreal.EditorLevelLibrary.get_editor_world()
    actors = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.StaticMeshActor)
    p('  static mesh actors = %d' % len(actors))
    for act in actors:
        for c in ACT.ActorTools.get_components(act):
            if 'StaticMesh' in c.get_class().get_name():
                p('    mesh=%s materials=%s override=%s' % (
                    c.get_editor_property('static_mesh'),
                    c.get_num_materials(),
                    c.get_editor_property('override_materials')))
    guard('save level', unreal.EditorAssetLibrary.save_asset, mp)

    p('')
    p('=== F. cleanup ===')
    for pp in (p1, p2, mp):
        if unreal.load_asset(pp):
            unreal.EditorAssetLibrary.delete_asset(pp)
    p('DONE')


if os.path.exists(REP):
    os.remove(REP)
try:
    main()
except Exception:
    p(traceback.format_exc())
    p('A69_FATAL')
