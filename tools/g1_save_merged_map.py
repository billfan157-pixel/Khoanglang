"""Save the merged world explicitly, bypassing the level UI checkout path."""
import unreal
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
path = '/Game/KhoangLang/Production/Maps/Lvl_KL_School3_Merged'
if path not in world.get_path_name():
    raise RuntimeError('Merged world required')
if not unreal.EditorLoadingAndSavingUtils.save_map(world,path):
    raise RuntimeError('Explicit map save failed')
print('MERGED_MAP_SAVED')
