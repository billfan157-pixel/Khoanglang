"""Load the primary classroom without saving any original levels."""
import gc
import unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    raise RuntimeError('Stop PIE first')
gc.collect()
if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(
        '/Game/KhoangLang/Production/Maps/Lvl_KL_School3_Primary'):
    raise RuntimeError('Primary level load failed')
print('PRIMARY_SCHOOL_OPEN')
