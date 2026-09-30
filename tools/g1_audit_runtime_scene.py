"""Read back saved lighting/player settings in actual PIE before fixtures."""
import json
from pathlib import Path
import unreal

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
if world is None:
    raise RuntimeError('Fresh G1 PIE required')
pawn = unreal.GameplayStatics.get_player_pawn(world,0)
lamp = pawn.get_component_by_class(unreal.SpotLightComponent)
lights = []
failures = []
for actor in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Light):
    component = actor.get_component_by_class(unreal.LightComponent)
    lights.append({'actor':actor.get_actor_label(),'mobility':str(component.get_editor_property('mobility'))})
    if component.get_editor_property('mobility')!=unreal.ComponentMobility.MOVABLE:
        failures.append('Static light: '+actor.get_actor_label())
post = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.PostProcessVolume)
            if a.get_editor_property('priority')==100)
settings = post.get_editor_property('settings')
ev = float(settings.get_editor_property('auto_exposure_bias'))
intensity = float(lamp.get_editor_property('intensity'))
force = world.get_world_settings().get_editor_property('force_no_precomputed_lighting')
if intensity!=90 or ev!=-1.5 or not force:
    failures.append('Saved lighting/torch values differ')
report={'status':'passed' if not failures else 'failed','world':world.get_path_name(),
        'torch_lumens':intensity,'exposure_ev':ev,'force_no_precomputed_lighting':force,
        'lights':lights,'failures':failures,'visual_accepted':False}
(Path(unreal.Paths.project_dir())/'docs/agent/EVIDENCE/G1_runtime_scene_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
