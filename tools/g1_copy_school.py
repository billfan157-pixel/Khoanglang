"""Stage copied graybox props and map with production gameplay components."""

import importlib
import json
from pathlib import Path
import sys
import unreal

root = Path(unreal.Paths.project_dir())
sys.path.insert(0, str(root / 'tools'))
import g1_build_runtime as production
importlib.reload(production)
K, build = production.K, production.build
from editor_toolset.toolsets.actor import ActorTools

source_folder = '/Game/KhoangLang/Blueprints/Core/Props'
target_folder = K.F_CORE + '/Props'
unreal.EditorAssetLibrary.make_directory(target_folder)
classes = {}
for name in ('BP_KL_Prop_AttBook', 'BP_KL_Prop_TapeDeck',
             'BP_KL_Prop_Roster', 'BP_KL_Prop_Corner'):
    target = target_folder + '/' + name
    if not unreal.EditorAssetLibrary.does_asset_exist(target):
        source = unreal.load_asset(source_folder + '/' + name)
        old = [c for c in K.cdo_components(source)
               if c.get_class().get_name() == 'BP_KL_InteractComponent_C'][0]
        values = {prop: old.get_editor_property(prop) for prop in
                  (*build.INT_BOOL, *build.INT_TEXT, *build.INT_SOUNDS,
                   *build.INT_FLOAT, 'PromptText')}
        prop_bp = unreal.EditorAssetLibrary.duplicate_asset(source_folder + '/' + name, target)
        if prop_bp is None:
            raise RuntimeError('Could not copy prop ' + name)
        for comp in list(K.cdo_components(prop_bp)):
            if comp.get_class().get_name() == 'BP_KL_InteractComponent_C':
                ActorTools.remove_component(comp)
        comp = K.add_comp(prop_bp, build.INT, 'KL_ProductionInteraction')
        for prop, value in values.items():
            comp.set_editor_property(prop, value)
        build.BPT.compile_blueprint(prop_bp)
        if not K.save(target):
            raise RuntimeError('Could not save prop ' + name)
    classes[source_folder + '/' + name + '.' + name + '_C'] = K.bp_class(target)

target_map = '/Game/KhoangLang/Production/Maps/Lvl_KL_School3_G1'
unreal.EditorAssetLibrary.make_directory('/Game/KhoangLang/Production/Maps')
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not unreal.EditorAssetLibrary.does_asset_exist(target_map):
    if not level.new_level_from_template(target_map, '/Game/KhoangLang/Maps/Lvl_KL_School3'):
        raise RuntimeError('Could not copy school map')
elif not level.load_level(target_map):
    raise RuntimeError('Could not open copied school')
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
replaced = []
for actor in list(actors.get_all_level_actors()):
    cls = classes.get(actor.get_class().get_path_name())
    if cls is None:
        continue
    new = actors.spawn_actor_from_class(cls, actor.get_actor_location(), actor.get_actor_rotation())
    if new is None:
        raise RuntimeError('Could not stage copied prop')
    new.set_actor_scale3d(actor.get_actor_scale3d())
    new.set_actor_label(actor.get_actor_label())
    replaced.append(actor.get_actor_label())
    if not actors.destroy_actor(actor):
        raise RuntimeError('Could not replace actor in copied map')
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
world.get_world_settings().set_editor_property('default_game_mode', K.bp_class(build.GM))
if not level.save_current_level():
    raise RuntimeError('Could not save copied school')
print(json.dumps({'map': target_map, 'replaced': replaced}))
