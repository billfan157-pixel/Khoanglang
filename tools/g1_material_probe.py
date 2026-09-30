"""Inspect failed source shader and mesh metadata without modifying assets."""
import json
from pathlib import Path
import unreal
mat = unreal.load_asset('/Game/KhoangLang/MaterialsArt/M_KL_ART_Surface')
mel = unreal.MaterialEditingLibrary
report = dict(material_api=[n for n in dir(mel) if any(k in n for k in ('expression', 'input', 'statistic'))],
    mesh_api=[n for n in dir(unreal.StaticMesh) if any(k in n for k in ('build', 'bound', 'mesh_description'))],
    globals_api=[n for n in dir(unreal) if any(k in n for k in ('objects_with', 'find_object'))])
if hasattr(unreal, 'get_objects_with_outer'):
    report['expressions'] = [dict(path=o.get_path_name(), cls=o.get_class().get_name())
        for o in unreal.get_objects_with_outer(mat, True) if 'MaterialExpression' in o.get_class().get_name()]
for name in ('SM_KL_Wall_700', 'SM_KL_Notice_Board', 'SM_KL_WallDoor_140'):
    asset = unreal.load_asset('/Game/KhoangLang/Meshes/Arch/' + name)
    if asset:
        report[name] = str(asset.get_bounds())
target = Path(unreal.Paths.project_dir()) / 'docs/agent/EVIDENCE/G1_material_probe.json'
target.write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
