"""Art pass probe 80: make mesh collision actually usable.

The level still logs "GetPhysicsTriMeshData: CPU data not available" for 55
instances, which means the player would fall through the school. add_simple_
collisions() reports success but the BodySetup is evidently not being rebuilt
into the mesh's physics data. This pins down the working order.
"""

import os
import traceback

import unreal

OUT = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Temp'
os.makedirs(OUT, exist_ok=True)
REP = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\art80\report.txt'
os.makedirs(os.path.dirname(REP), exist_ok=True)

import sys
HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import kl_mesh as M  # noqa: E402

ESM = unreal.EditorStaticMeshLibrary


def p(m=''):
    line = str(m)
    unreal.log('A80: ' + line)
    with open(REP, 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


def report(tag, sm):
    n = None
    cplx = None
    cpu = None
    bs = None
    for fn, setter in (('simple_collisions', lambda: ESM.get_simple_collision_count(sm)),
                       ('collision_complexity', lambda: ESM.get_collision_complexity(sm)),
                       ('allow_cpu_access', lambda: sm.get_editor_property(
                           'allow_cpu_access')),
                       ('body_setup', lambda: sm.get_editor_property('body_setup'))):
        try:
            v = setter()
        except Exception as exc:
            v = 'EXC %r' % str(exc)[:80]
        p('  %-22s %s' % (fn, v))
    p('  %-22s %s' % (tag, sm.get_name()))


def build(name, collide):
    def fn(mb, s):
        mat = s['/Engine/BasicShapes/BasicShapeMaterial']
        mb.box(mat, -50, -50, 0, 50, 50, 100, 0.5)
        mb.box(mat, -50, -50, 100, 50, 50, 120, 0.5)
    return M.make_mesh(name, '/Game/KhoangLang/ArtTest',
                       ['/Engine/BasicShapes/BasicShapeMaterial'],
                       fn, collision=False)


def main():
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.make_directory('/Game/KhoangLang/ArtTest')

    p('=== A. shape_type enum ===')
    p('  ScriptCollisionShapeType: %s' % (
        [a for a in dir(unreal.ScriptCollisionShapeType) if not a.startswith('_')]
        if hasattr(unreal, 'ScriptCollisionShapeType') else 'MISSING'))
    p('  CollisionTraceFlag: %s' % [a for a in dir(unreal.CollisionTraceFlag)
                                    if not a.startswith('_')])
    p('  ESM.add_simple_collisions doc: %s' % (
        (ESM.add_simple_collisions.__doc__ or '')[:300].replace('\r\n', ' ')))
    p('  ESM.set_convex_decomposition_collisions doc: %s' % (
        (ESM.set_convex_decomposition_collisions.__doc__ or '')[:300]
        .replace('\r\n', ' ')))
    p('  ESM.set_allow_cpu_access doc: %s' % (
        (ESM.set_allow_cpu_access.__doc__ or '')[:200].replace('\r\n', ' ')))
    p('  StaticMesh.allow_cpu_access settable: %s' %
      ('allow_cpu_access' in [m for m in dir(unreal.StaticMesh)
                              if not m.startswith('_')]))

    p('')
    p('=== B. build then add collision, then inspect ===')
    sm, _ = build('A80_Coll', True)
    report('after build only', sm)

    p('  set_allow_cpu_access -> %r' % (ESM.set_allow_cpu_access(sm, True),))
    r = None
    names = [a for a in dir(unreal.ScriptCollisionShapeType)
             if not a.startswith('_')] if hasattr(unreal,
                                                  'ScriptCollisionShapeType') else []
    for shape in names + ['CTF_USE_SIMPLE_AND_COMPLEX']:
        try:
            r = ESM.add_simple_collisions(sm, getattr(unreal.ScriptCollisionShapeType,
                                                      shape))
            p('  add_simple_collisions(%s) -> %r' % (shape, r))
            break
        except Exception as exc:
            p('  add_simple_collisions(%s) -> %r' % (shape, str(exc)[:110]))
    report('after add_simple_collisions', sm)
    unreal.EditorAssetLibrary.save_asset('/Game/KhoangLang/ArtTest/A80_Coll')
    p('  saved')
    del sm
    sm2 = unreal.load_asset('/Game/KhoangLang/ArtTest/A80_Coll')
    report('after reload', sm2)

    p('')
    p('=== C. does a second render build pick up the body setup? ===')
    md = sm2.get_static_mesh_description(0)
    ESM.set_allow_cpu_access(sm2, True)
    ESM.add_simple_collisions(
        sm2, getattr(unreal.ScriptCollisionShapeType, 'SCS_BOX'))
    sm2.build_from_static_mesh_descriptions([md])
    report('after rebuild', sm2)
    unreal.EditorAssetLibrary.save_asset('/Game/KhoangLang/ArtTest/A80_Coll')

    p('')
    p('=== D. place it in a level and save: does the warning appear? ===')
    from editor_toolset.toolsets import scene as SCENE
    mp = '/Game/KhoangLang/Maps/A80_Map'
    if unreal.load_asset(mp):
        unreal.EditorAssetLibrary.delete_asset(mp)
    unreal.EditorLevelLibrary.new_level(mp)
    t = unreal.Transform()
    t.set_editor_property('translation', unreal.Vector(0, 0, 50))
    t.set_editor_property('scale3d', unreal.Vector(1, 1, 1))
    a = SCENE.SceneTools.add_to_scene_from_class(
        unreal.StaticMeshActor.static_class(), 'A80_Act', t)
    from editor_toolset.toolsets import actor as ACT
    for c in ACT.ActorTools.get_components(a):
        if 'StaticMesh' in c.get_class().get_name():
            c.set_editor_property('static_mesh', sm2)
            c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    unreal.EditorAssetLibrary.save_asset(mp)
    p('  level saved - check the log for GetPhysicsTriMeshData')

    p('')
    p('=== E. cleanup ===')
    for q in ('/Game/KhoangLang/ArtTest/A80_Coll', mp):
        if unreal.load_asset(q):
            unreal.EditorAssetLibrary.delete_asset(q)
    p('DONE')


if os.path.exists(REP):
    os.remove(REP)
try:
    main()
except Exception:
    p(traceback.format_exc())
    p('A80_FATAL')
