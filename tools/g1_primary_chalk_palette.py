"""Keep the copied slate readable as a dark classroom chalkboard."""
import unreal
mi=unreal.load_asset('/Game/KhoangLang/Production/Materials/MI_ART_Chalk')
mel=unreal.MaterialEditingLibrary
mel.set_material_instance_vector_parameter_value(mi,'BaseTint',unreal.LinearColor(r=.045,g=.065,b=.050,a=1))
mel.set_material_instance_vector_parameter_value(mi,'DirtTint',unreal.LinearColor(r=.015,g=.030,b=.022,a=1))
mel.set_material_instance_scalar_parameter_value(mi,'NormalStrength',.12)
mel.set_material_instance_scalar_parameter_value(mi,'Roughness',.96)
mel.update_material_instance(mi)
if not unreal.EditorAssetLibrary.save_loaded_asset(mi,False): raise RuntimeError('Slate palette save failed')
print('PRIMARY_SLATE_PALETTE_SAVED')
