"""Art pass probe 81: configure collision through the BodySetup directly.

EditorStaticMeshLibrary.add_simple_collisions() returns -1 and changes nothing
in a commandlet, so the BodySetup has to be written by hand. A BodySetup is
created automatically on the mesh, so the question is whether AggGeom and the
trace flag are writable from Python.
"""

import os
import traceback

import unreal

REP = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\art81\report.txt'
os.makedirs(os.path.dirname(REP), exist_ok=True)


def p(m=''):
    line = str(m)
    unreal.log('A81: ' + line)
    with open(REP, 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


def main():
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.make_directory('/Game/KhoangLang/ArtTest')
    p('=== A. BodySetup / AggGeom surface ===')
    for n in ('BodySetup', 'AggGeom', 'KAggregateGeom', 'BoxElem', 'SphereElem',
              'ConvexElem', 'CTShape', 'PhysMaterial', 'BodyInstance'):
        p('  unreal.%-16s %s' % (n, hasattr(unreal, n)))
    BS = unreal.BodySetup
    ms = [m for m in dir(BS) if not m.startswith('_')]
    p('  BodySetup members (%d): %s' % (len(ms), ms))
    for m in ms:
        if 'agg' in m.lower() or 'geom' in m.lower() or 'trace' in m.lower() \
                or 'collision' in m.lower():
            p('    .%s -> %s' % (m, (getattr(BS, m).__doc__ or '')[:220]
                                 .replace('\r\n', ' ')))

    p('')
    p('=== B. make a mesh and reach its BodySetup ===')
    from editor_toolset.toolsets import scene as SCENE
    sm = unreal.load_asset('/Engine/BasicShapes/Cube')
    p('  reference engine cube: %s' % sm)
    bs = sm.get_editor_property('body_setup')
    p('  engine cube body_setup = %s' % bs)
    if bs:
        for prop in ('collision_trace_flag', 'generate_mirrored_collision',
                     'double_sided_geometry', 'generate_mirrored_winding'):
            try:
                p('    %s = %r' % (prop, bs.get_editor_property(prop)))
            except Exception as exc:
                p('    %s -> %r' % (prop, str(exc)[:100]))
        ag = bs.get_editor_property('agg_geom')
        p('    agg_geom = %r' % (ag,))
        if ag:
            p('    agg_geom members = %s' % [m for m in dir(ag)
                                             if not m.startswith('_')][:40])
            for prop in ('box_elems', 'sphere_elems', 'convex_elems',
                         'sphyl_elems', 'tapered_capsule_elems'):
                try:
                    v = ag.get_editor_property(prop)
                    p('      %-22s %d entries' % (prop, len(v) if v else 0))
                except Exception as exc:
                    p('      %s -> %r' % (prop, str(exc)[:90]))
            if hasattr(unreal, 'BoxElem'):
                p('    BoxElem members = %s' % [m for m in dir(unreal.BoxElem)
                                                 if not m.startswith('_')][:30])
    p('')
    p('=== C. can a BodySetup be written? (make a throwaway mesh) ===')
    t = unreal.Transform()
    t.set_editor_property('translation', unreal.Vector(0, 0, 0))
    t.set_editor_property('scale3d', unreal.Vector(1, 1, 1))
    a = SCENE.SceneTools.add_to_scene_from_class(
        unreal.StaticMeshActor.static_class(), 'A81_Act', t)
    from editor_toolset.toolsets import actor as ACT
    for c in ACT.ActorTools.get_components(a):
        if 'StaticMesh' in c.get_class().get_name():
            c.set_editor_property('static_mesh', sm)
    path = '/Game/KhoangLang/ArtTest/A81_Mesh'
    if unreal.load_asset(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    dupe = unreal.load_asset('/Engine/BasicShapes/Cube')
    unreal.EditorAssetLibrary.duplicate_asset('/Engine/BasicShapes/Cube', path) \
        if False else None
    p('  (duplicating an engine asset to test BodySetup writes)')
    d2 = unreal.EditorAssetLibrary.duplicate_asset('/Engine/BasicShapes/Cube',
                                                  path)
    p('  duplicate -> %s' % (d2.get_name() if d2 else None))
    if d2:
        bs2 = d2.get_editor_property('body_setup')
        p('  body_setup = %s' % bs2)
        if bs2:
            try:
                bs2.set_editor_property('collision_trace_flag',
                                       unreal.CollisionTraceFlag
                                       .CTF_USE_SIMPLE_AND_COMPLEX)
                p('    set collision_trace_flag -> %r' % bs2.get_editor_property(
                    'collision_trace_flag'))
            except Exception as exc:
                p('    set collision_trace_flag -> %r' % str(exc)[:140])
        unreal.EditorAssetLibrary.save_asset(path)
        p('  saved')
        if unreal.load_asset(path):
            unreal.EditorAssetLibrary.delete_asset(path)
    SCENE.SceneTools.remove_from_scene(a)
    p('DONE')


if os.path.exists(REP):
    os.remove(REP)
try:
    main()
except Exception:
    p(traceback.format_exc())
    p('A81_FATAL')
