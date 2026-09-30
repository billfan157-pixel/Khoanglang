"""Persist production prop collision meshes on Blueprint templates."""
import json
import sys
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
sys.path.insert(0, str(root / 'Content/Python/KhoangLang'))
import kl_core as K

editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
if editor.get_game_world():
    raise RuntimeError('Stop PIE before editing prop templates')
report = []
for suffix in ('AttBook', 'Roster', 'TapeDeck', 'Corner'):
    path = '/Game/KhoangLang/Production/Blueprints/Core/PropsArt/BP_KL_Prop_ART_' + suffix
    bp = unreal.load_asset(path)
    for component in K.cdo_components(bp):
        if not isinstance(component, unreal.StaticMeshComponent):
            continue
        old = component.get_editor_property('static_mesh')
        if not old:
            continue
        target = '/Game/KhoangLang/Production/Meshes/School/' + old.get_name()
        mesh = unreal.load_asset(target)
        if not mesh:
            raise RuntimeError('Missing copied collision mesh: ' + target)
        component.modify()
        component.set_static_mesh(mesh)
        report.append({'blueprint': path, 'component': component.get_name(), 'mesh': target})
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    if bp.get_editor_property('status') == unreal.BlueprintStatus.BS_ERROR:
        raise RuntimeError('Blueprint compile failed: ' + path)
    if not unreal.EditorAssetLibrary.save_asset(path):
        raise RuntimeError('Blueprint save failed: ' + path)
(root / 'docs/agent/EVIDENCE/G1_primary_prop_collision.json').write_text(
    json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report))
