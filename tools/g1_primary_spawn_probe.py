"""Inspect default pawn routing and spawn capsule overlaps."""
import json
from pathlib import Path
import unreal
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
gm=world.get_world_settings().get_editor_property('default_game_mode')
cdo=unreal.get_default_object(gm)
cls=cdo.get_editor_property('default_pawn_class')
report=dict(game_mode=gm.get_path_name(),pawn_class=cls.get_path_name() if cls else None,
    spectator=cdo.get_editor_property('start_players_as_spectators'),overlaps=[])
if cls:
    pawn=unreal.get_default_object(cls)
    capsule=pawn.get_component_by_class(unreal.CapsuleComponent)
    report['capsule']=dict(radius=capsule.get_scaled_capsule_radius(),height=capsule.get_scaled_capsule_half_height())
    object_types=[unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1,unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY2]
    result=unreal.SystemLibrary.capsule_overlap_actors(world,unreal.Vector(-880,0,110),
        capsule.get_scaled_capsule_radius(),capsule.get_scaled_capsule_half_height(),object_types,unreal.Actor,[])
    report['overlaps']=[dict(label=a.get_actor_label(),actor_class=a.get_class().get_path_name()) for a in (result or [])]
(Path(unreal.Paths.project_dir())/'docs/agent/EVIDENCE/G1_primary_spawn_probe.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
