"""Save the merged working world under the final primary package name."""
import unreal
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
if '/Production/Maps/Lvl_KL_School3_Merged' not in world.get_path_name():
    raise RuntimeError('Merged staging world required')
path = '/Game/KhoangLang/Production/Maps/Lvl_KL_School3_Primary'
if unreal.EditorAssetLibrary.does_asset_exist(path):
    raise RuntimeError('Primary map exists; use a targeted repair')
if not unreal.EditorLoadingAndSavingUtils.save_map(world,path):
    raise RuntimeError('Primary map save failed')
print('PRIMARY_MAP_SAVED')
