"""Art pass probe 63: prove the full StaticMeshDescription authoring pipeline.

Must answer, headlessly:
  1. create StaticMesh asset with factory=None, fill a description, build it
  2. UVs survive (query vertex instance UVs back out of the description)
  3. polygon groups -> named material slots
  4. how to set collision (set_editor_property('collision_enabled') failed)
  5. the real AutoExposureMethod enum members
  6. verification surface that works in a commandlet (get_num_triangles etc.)
"""

import os
import traceback

import unreal

OUT = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\art63'
os.makedirs(OUT, exist_ok=True)
L = []


def p(m=''):
    L.append(str(m))
    unreal.log('A63: ' + str(m))


# --------------------------------------------------------------------------- #
# tiny mesh helper: an L-shaped bracket with named UVs and 2 material slots
# --------------------------------------------------------------------------- #

def build_description(md, boxes):
    """boxes: [(x0,y0,z0,x1,y1,z1, mat_slot_name, uv_scale)]"""
    verts = {}
    groups = {}

    def vid(x, y, z):
        k = (round(x, 4), round(y, 4), round(z, 4))
        if k not in verts:
            v = md.create_vertex()
            md.set_vertex_position(v, unreal.Vector(*k))
            verts[k] = v
        return verts[k]

    for (x0, y0, z0, x1, y1, z1, slot, uvs) in boxes:
        if slot not in groups:
            g = md.create_polygon_group()
            md.set_polygon_group_material_slot_name(g, slot)
            groups[slot] = g
        g = groups[slot]
        s = max(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)) / 100.0 * uvs
        c = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                 (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        for f in faces:
            vis = []
            for i in f:
                px, py, pz = c[i]
                v = vid(px, py, pz)
                vi = md.create_vertex_instance(v)
                # planar UV on the dominant axis of the face
                nx, ny, nz = ((0, 0, 1) if f[0] < 4 and max(f) - min(f) == 3 else
                              (0, 0, -1) if False else (0, 0, 0))
                if f in ((0, 3, 2, 1), (4, 5, 6, 7)):
                    u, vv = px / 100.0, py / 100.0
                elif f in ((0, 1, 5, 4), (2, 3, 7, 6)):
                    u, vv = px / 100.0, pz / 100.0
                else:
                    u, vv = py / 100.0, pz / 100.0
                md.set_vertex_instance_uv(vi, unreal.Vector2D(u * uvs, vv * uvs))
                vis.append(vi)
            md.create_polygon(g)
            md.set_polygon_vertex_instances(
                md.get_polygon_group_polygons(g)[-1], vis)
    return len(verts), len(groups)


def main():
    at = unreal.AssetToolsHelpers.get_asset_tools()
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.make_directory('/Game/KhoangLang/ArtTest')

    p('=== A. StaticMesh build functions ===')
    for n in ('build_from_static_mesh_descriptions', 'get_static_mesh_description',
              'create_static_mesh_description'):
        d = (getattr(unreal.StaticMesh, n).__doc__ or '').strip().replace('\r\n', ' ')
        p('  .%s -> %s' % (n, d[:240]))

    p('')
    p('=== B. author + build a real mesh ===')
    mpath = '/Game/KhoangLang/ArtTest/A63_Bracket'
    if unreal.load_asset(mpath):
        unreal.EditorAssetLibrary.delete_asset(mpath)
    sm = at.create_asset('A63_Bracket', '/Game/KhoangLang/ArtTest',
                         unreal.StaticMesh, None)
    p('  asset: %s' % (sm.get_name() if sm else None))
    md = sm.create_static_mesh_description()
    p('  description: %s empty=%s' % (md.get_class().get_name(), md.is_empty()))
    nv, ng = build_description(md, [
        (0, 0, 0, 120, 40, 40, 'Wood', 1.0),
        (0, 0, 0, 40, 40, 120, 'Metal', 2.0),
    ])
    p('  authored verts=%d groups=%d  desc: v=%d p=%d t=%d g=%d vi=%d' % (
        nv, ng, md.get_vertex_count(), md.get_polygon_count(),
        md.get_triangle_count(), md.get_polygon_group_count(),
        md.get_vertex_instance_count()))
    try:
        sm.build_from_static_mesh_descriptions([md])
        p('  build_from_static_mesh_descriptions ok')
    except Exception as exc:
        p('  build -> %r' % str(exc)[:250])
    p('  StaticMesh: verts=%s tris=%s sections=%s uvchannels=%s lods=%s' % (
        sm.get_num_vertices(0) if hasattr(sm, 'get_num_vertices') else '?',
        sm.get_num_triangles(0) if hasattr(sm, 'get_num_triangles') else '?',
        sm.get_num_sections(0) if hasattr(sm, 'get_num_sections') else '?',
        sm.get_num_tex_coords(0) if hasattr(sm, 'get_num_tex_coords') else '?',
        sm.get_num_lods()))
    bb = sm.get_bounds()
    p('  bounds origin=%s extent=%s' % (bb.origin, bb.box_extent))
    try:
        p('  material slot 0 = %s' % sm.get_material(0))
    except Exception as exc:
        p('  get_material(0) -> %r' % str(exc)[:150])

    p('')
    p('=== C. assign real materials to the named slots ===')
    mi = unreal.load_asset('/Game/KhoangLang/MaterialsArt/MI_ART_Wood')
    mr = unreal.load_asset('/Game/KhoangLang/MaterialsArt/MI_ART_MetalRust')
    p('  MI_Wood=%s MI_MetalRust=%s' % (mi is not None, mr is not None))
    if mi:
        try:
            sm.set_material(0, mi)
            sm.set_material(1, mr)
            p('  set_material ok: 0=%s 1=%s' % (sm.get_material(0), sm.get_material(1)))
        except Exception as exc:
            p('  set_material -> %r' % str(exc)[:200])
    for prop, val in (('light_map_resolution_scale', 1.0),
                      ('lightmap_coord_index', 0),
                      ('light_map_coordinate_index', 0),
                      ('light_map_scale', 1.0)):
        try:
            sm.set_editor_property(prop, val)
            p('    %s = %s ok' % (prop, val))
        except Exception as exc:
            p('    %s -> %r' % (prop, str(exc)[:110]))

    p('')
    p('=== D. UV readback (does the build keep UVs?) ===')
    try:
        md2 = sm.get_static_mesh_description(0)
        p('  reloaded desc: v=%d p=%d t=%d vi=%d' % (
            md2.get_vertex_count(), md2.get_polygon_count(),
            md2.get_triangle_count(), md2.get_vertex_instance_count()))
        uvs = []
        for poly in md2.get_polygon_group_polygons(md2.get_polygon_group_count() and
                                                  (md2.get_polygon_count() and 0 or 0)) or []:
            pass
        pg = md2.get_polygon_group_count()
        p('  polygon groups: %d' % pg)
        sample = []
        for vi in range(min(6, md2.get_vertex_instance_count())):
            try:
                sample.append(md2.get_vertex_instance_uv(vi))
            except Exception as exc:
                sample.append(str(exc)[:60])
        p('  first UVs: %s' % sample)
    except Exception as exc:
        p('  readback -> %r' % str(exc)[:200])

    p('')
    p('=== E. collision API on a component ===')
    comp = unreal.StaticMeshComponent()
    p('  has set_collision_enabled: %s' % hasattr(comp, 'set_collision_enabled'))
    p('  has collision_enabled prop: %s' % hasattr(comp, 'collision_enabled'))
    for n in ('set_collision_enabled', 'set_collision_profile_name',
              'set_generate_lightmap_uvs', 'set_cast_shadow'):
        p('    %s: %s' % (n, hasattr(comp, n)))
    try:
        comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        p('  set_collision_enabled ok -> %s' % comp.get_collision_enabled())
    except Exception as exc:
        p('  set_collision_enabled -> %r' % str(exc)[:150])
    try:
        comp.set_editor_property('collision_enabled',
                                 unreal.CollisionEnabled.NO_COLLISION)
        p('  set_editor_property collision_enabled ok')
    except Exception as exc:
        p('  set_editor_property collision_enabled -> %r' % str(exc)[:150])
    for n in ('generate_lightmap_uvs', 'cast_shadow', 'b_cast_dynamic_shadow',
              'can_ever_affect_navigation', 'visible_in_ray_tracing',
              'b_allow_distance_field_shadows'):
        try:
            comp.set_editor_property(n, True)
            p('    %s settable' % n)
        except Exception as exc:
            p('    %s -> %r' % (n, str(exc)[:90]))

    p('')
    p('=== F. AutoExposureMethod enum members (crash cause) ===')
    p('  %s' % [a for a in dir(unreal.AutoExposureMethod) if not a.startswith('_')])
    p('  AEM_Historical: %s' % hasattr(unreal.AutoExposureMethod, 'AEM_Historical'))
    p('  AEM_Manual: %s' % hasattr(unreal.AutoExposureMethod, 'AEM_Manual'))
    try:
        p('  dir(): %s' % [a for a in dir(unreal.AutoExposureMethod)])
    except Exception as exc:
        p('  dir -> %r' % exc)
    p('  eye_adaptation_method on settings: %s' % (
        'eye_adaptation_method' in dir(unreal.PostProcessSettings())))

    p('')
    p('=== G. save + reload round trip ===')
    try:
        unreal.EditorAssetLibrary.save_asset(mpath)
        del sm
        again = unreal.load_asset(mpath)
        p('  reloaded: %s verts=%s' % (again.get_name() if again else None,
                                       again.get_num_lods() if again else None))
        if again:
            bb = again.get_bounds()
            p('  bounds extent=%s' % bb.box_extent)
    except Exception as exc:
        p('  save/reload -> %r' % str(exc)[:200])

    p('')
    p('=== H. cleanup ===')
    if unreal.load_asset(mpath):
        unreal.EditorAssetLibrary.delete_asset(mpath)
    p('DONE')


try:
    main()
except Exception:
    p(traceback.format_exc())
    p('A63_FATAL')
finally:
    with open(os.path.join(OUT, 'report.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
