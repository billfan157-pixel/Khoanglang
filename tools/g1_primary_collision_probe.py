"""Inspect primary spawn geometry and collision metadata, then save live repairs."""
import json
from pathlib import Path
import sys
import unreal
root=Path(unreal.Paths.project_dir())
sys.path.insert(0,str(root/'tools'))
import g1_build_runtime as production
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
if '/Production/Maps/Lvl_KL_School3_Primary' not in world.get_path_name():
    raise RuntimeError('Primary world required')
report=dict(actors=[])
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    c=a.get_component_by_class(unreal.StaticMeshComponent)
    mesh=c.get_editor_property('static_mesh') if c else None
    loc=a.get_actor_location()
    if loc.x<-300 or a.get_actor_label() in ('ART_PlayerStart','ART_Wall_HallN_Door','ART_Door3_Frame','ART_Teacher_Desk','ART_Chalkboard'):
        row=dict(label=a.get_actor_label(),location=str(loc),bounds=str(a.get_actor_bounds(False)),materials=[])
        if mesh:
            row['mesh']=mesh.get_path_name()
            body=mesh.get_editor_property('body_setup')
            row['collision_trace']=str(body.get_editor_property('collision_trace_flag')) if body else None
            row['materials']=[c.get_material(i).get_path_name() if c.get_material(i) else None for i in range(c.get_num_materials())]
        report['actors'].append(row)
bp=unreal.load_asset(production.build.CHAR)
if not production.K.save(production.build.CHAR):
    raise RuntimeError('Could not save repaired character after lock release')
(root/'docs/agent/EVIDENCE/G1_primary_collision_probe.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
