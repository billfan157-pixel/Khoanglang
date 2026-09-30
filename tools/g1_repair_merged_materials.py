"""Repair the copied art surface shader and override merged actors only."""
import json
from pathlib import Path
import unreal
from editor_toolset.toolsets.material import MaterialTools

ROOT = Path(unreal.Paths.project_dir())
FOLDER = '/Game/KhoangLang/Production/Materials'
MASTER = FOLDER + '/M_KL_ART_Surface'
mel = unreal.MaterialEditingLibrary

def connect(src, output, dst, pin):
    if not mel.connect_material_expressions(src, output, dst, pin):
        raise RuntimeError('Material connection failed: %s.%s' % (dst.get_name(), pin))

def main():
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not any(n in world.get_path_name() for n in ('/Production/Maps/Lvl_KL_School3_Merged',
            '/Production/Maps/Lvl_KL_School3_Primary')):
        raise RuntimeError('Merged editor map required')
    world.modify()
    unreal.EditorAssetLibrary.make_directory(FOLDER)
    if True:  # Also repair an interrupted, unsaved production copy.
        mat = (unreal.load_asset(MASTER) if unreal.EditorAssetLibrary.does_asset_exist(MASTER)
            else unreal.EditorAssetLibrary.duplicate_asset('/Game/KhoangLang/MaterialsArt/M_KL_ART_Surface', MASTER))
        nodes = mel.get_material_expressions(mat)
        saturate = next(n for n in nodes if isinstance(n, unreal.MaterialExpressionSaturate))
        inverse = next(n for n in nodes if isinstance(n, unreal.MaterialExpressionOneMinus))
        multiply = next(n for n in nodes if isinstance(n, unreal.MaterialExpressionMultiply)
            and inverse in mel.get_inputs_for_material_expression(mat,n))
        connect(multiply, '', saturate, mel.get_material_expression_input_names(saturate)[0])
        defaults = {'Detail':'T_ART_Plaster_A', 'DetailRough':'T_ART_Plaster_R',
            'Grunge':'T_ART_Grunge_A', 'NormalMap':'T_ART_Plaster_N'}
        for n in nodes:
            if isinstance(n, unreal.MaterialExpressionTextureSampleParameter2D):
                texture = unreal.load_asset('/Game/KhoangLang/TexturesArt/' + defaults[str(n.get_editor_property('parameter_name'))])
                if texture is None:
                    raise RuntimeError('Missing default texture')
                n.set_editor_property('texture', texture)
        # Express height in centimetres and keep dirt near the floor.
        mask = next(n for n in nodes if isinstance(n,unreal.MaterialExpressionComponentMask))
        wp = next(n for n in nodes if isinstance(n,unreal.MaterialExpressionWorldPosition))
        connect(wp,'',mask,mel.get_material_expression_input_names(mask)[0])
        divide = next((n for n in nodes if isinstance(n,unreal.MaterialExpressionDivide)), None)
        if divide is None:
            divide = mel.create_material_expression(mat,unreal.MaterialExpressionDivide)
        divide.set_editor_property('const_b', 180.0)
        connect(mask,'',divide,'A')
        connect(divide,'',inverse,mel.get_material_expression_input_names(inverse)[0])
        lerp = next(n for n in nodes if isinstance(n,unreal.MaterialExpressionLinearInterpolate))
        base = next(n for n in nodes if isinstance(n,unreal.MaterialExpressionVectorParameter)
            and str(n.get_editor_property('parameter_name')) == 'BaseTint')
        dirt = next(n for n in nodes if isinstance(n,unreal.MaterialExpressionVectorParameter)
            and str(n.get_editor_property('parameter_name')) == 'DirtTint')
        connect(base,'',lerp,'A')
        connect(dirt,'',lerp,'B')
        MaterialTools.recompile(mat)
        if not unreal.EditorAssetLibrary.save_asset(MASTER):
            raise RuntimeError('Master save failed')
    copied = {}
    def adopt(material):
        if material is None:
            return None
        path = material.get_path_name().split('.')[0]
        if path.startswith(FOLDER + '/'):
            return material
        if not path.startswith('/Game/KhoangLang/MaterialsArt/'):
            return material
        if path in copied:
            return copied[path]
        if not isinstance(material,unreal.MaterialInstanceConstant):
            return material
        parent = material.get_editor_property('parent')
        if parent and parent.get_path_name().split('.')[0] == '/Game/KhoangLang/MaterialsArt/M_KL_ART_Surface':
            target_parent = unreal.load_asset(MASTER)
        elif isinstance(parent,unreal.MaterialInstanceConstant):
            target_parent = adopt(parent)
        else:
            return material  # retain the valid emissive family
        target = FOLDER + '/' + material.get_name()
        instance = unreal.load_asset(target) if unreal.EditorAssetLibrary.does_asset_exist(target) else unreal.EditorAssetLibrary.duplicate_asset(path,target)
        instance.set_editor_property('parent',target_parent)
        mel.update_material_instance(instance)
        mel.set_material_instance_scalar_parameter_value(instance,'NormalStrength',0.3)
        mel.update_material_instance(instance)
        if not unreal.EditorAssetLibrary.save_asset(target):
            raise RuntimeError('Instance save failed')
        copied[path] = instance
        return instance
    overrides = []
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            for index in range(component.get_num_materials()):
                old = component.get_material(index)
                new = adopt(old)
                if new != old:
                    actor.modify()
                    component.modify()
                    component.set_material(index,new)
                    overrides.append(dict(actor=actor.get_actor_label(), slot=index, material=new.get_path_name()))
    if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level():
        raise RuntimeError('Map override save failed')
    report = dict(master=MASTER,instances=len(copied),overrides=overrides,
        validation='Native MaterialTools.recompile raises on shader errors')
    (ROOT / 'docs/agent/EVIDENCE/G1_merged_material_repair.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(master=MASTER,instances=len(copied),overrides=len(overrides))))

main()
