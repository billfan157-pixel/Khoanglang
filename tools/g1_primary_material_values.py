"""Read effective material parameters and editor mesh triangle slots."""
import json
from pathlib import Path
import unreal
mel=unreal.MaterialEditingLibrary
report=[]
for name in ('MI_ART_Chalk','MI_ART_Wood','MI_ART_WallClassroom','MI_ART_WallOchre','MI_SF_Wood_AgedTop'):
    mi=unreal.load_asset('/Game/KhoangLang/Production/Materials/'+name)
    tex=mel.get_material_instance_texture_parameter_value(mi,'Detail')
    report.append(dict(name=name,detail=tex.get_path_name() if tex else None,
        base=str(mel.get_material_instance_vector_parameter_value(mi,'BaseTint')),
        dirt=str(mel.get_material_instance_vector_parameter_value(mi,'DirtTint')),
        parent=mi.get_editor_property('parent').get_path_name()))
(Path(unreal.Paths.project_dir())/'docs/agent/EVIDENCE/G1_primary_material_values.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
