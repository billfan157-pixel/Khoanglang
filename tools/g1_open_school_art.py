"""Open the existing school art level for inspection without saving it."""
import unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    raise RuntimeError('Stop PIE before opening an existing school map')
if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level('/Game/KhoangLang/Maps/Lvl_KL_School3_Art'):
    raise RuntimeError('Could not open existing school art')
print('EXISTING_SCHOOL_ART_LOADED_READ_ONLY')
