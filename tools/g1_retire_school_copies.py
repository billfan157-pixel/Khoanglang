"""Retire only the three obsolete classroom copies authorized by the user."""
import json
import shutil
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir()).resolve()
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
if editor.get_game_world():
    raise RuntimeError('Stop PIE first')
if 'Lvl_KL_School3_Primary' not in editor.get_editor_world().get_path_name():
    raise RuntimeError('Keep primary map loaded')
packages = ['/Game/KhoangLang/Maps/Lvl_KL_School3_ArtTest',
    '/Game/KhoangLang/Production/Maps/Lvl_KL_School3_G1',
    '/Game/KhoangLang/Production/Maps/Lvl_KL_School3_Merged']
registry = unreal.AssetRegistryHelpers.get_asset_registry()
report = []
for package in packages:
    refs = [str(p) for p in registry.get_referencers(package, unreal.AssetRegistryDependencyOptions())
            if str(p) not in packages and str(p) != package]
    if refs:
        raise RuntimeError('Referenced obsolete map: ' + package + ' ' + repr(refs))
backup = root / '_g1_cleanup_20260930'
backup.mkdir(exist_ok=True)
for package in packages:
    source = (root / 'Content' / (package.removeprefix('/Game/') + '.umap')).resolve()
    if not source.is_relative_to(root / 'Content'):
        raise RuntimeError('Path outside project content')
    if not source.exists():
        continue
    shutil.copy2(source, backup / source.name)
    if not unreal.EditorAssetLibrary.delete_asset(package):
        raise RuntimeError('Could not retire ' + package)
    report.append(package)
(root / 'docs/agent/EVIDENCE/G1_retired_school_copies.json').write_text(
    json.dumps({'removed': report, 'backup': '_g1_cleanup_20260930',
                'primary': '/Game/KhoangLang/Production/Maps/Lvl_KL_School3_Primary'}, indent=2), encoding='utf-8')
print(json.dumps(report))
