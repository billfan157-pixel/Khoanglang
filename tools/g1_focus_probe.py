"""Inspect the production camera ray and collision of reachable evidence."""
import json
from pathlib import Path
import unreal
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
controller = unreal.GameplayStatics.get_player_controller(world, 0)
camera = unreal.GameplayStatics.get_player_camera_manager(world, 0)
def vec(v):
    return [v.x, v.y, v.z]
start = camera.get_camera_location()
rotation = camera.get_camera_rotation()
end = start + unreal.MathLibrary.get_forward_vector(rotation) * 260
hit = unreal.SystemLibrary.line_trace_single(world, start, end,
    unreal.TraceTypeQuery.ECC_VISIBILITY, False, [pawn], unreal.DrawDebugTrace.NONE, True)
report = {'start': vec(start), 'end': vec(end), 'control_rotation': str(controller.get_control_rotation()),
          'camera_rotation': str(rotation), 'hit': str(hit),
          'focus': str(pawn.get_editor_property('FocusCand')),
          'props': []}
report['hit_fields'] = [str(v) for v in hit.to_tuple()]
hit_actor = hit.to_tuple()[9]
report['hit_actor_components'] = [c.get_class().get_path_name() for c in hit_actor.get_components_by_class(unreal.ActorComponent)] if hit_actor else []
pawn.call_method('UpdateFocus', ())
report['focus_after_direct_update'] = str(pawn.get_editor_property('FocusCand'))
from editor_toolset.toolsets.blueprint import BlueprintTools as BPT
bp = unreal.load_asset('/Game/KhoangLang/Production/Blueprints/Player/BP_KL_Character')
report['graphs'] = []
for graph in BPT.list_graphs(bp):
    if graph.get_name() not in ('UpdateFocus', 'TickKL', 'EventGraph'):
        continue
    for node in unreal.BlueprintGraphEditor.get_graph_editor(graph).list_all_nodes():
        info = BPT.get_node_infos([node])[0]
        report['graphs'].append({'graph': graph.get_name(), 'node': node.get_node_title(),
            'inputs': [{'name': p.name, 'type': str(p.type_id), 'links': len(p.connected_pins),
                        'default': str(p.default_value) if hasattr(p, 'default_value') else ''} for p in info.input_pins],
            'outputs': [{'name': p.name, 'links': len(p.connected_pins)} for p in info.output_pins]})
for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
    if 'Prop_AttBook' in actor.get_class().get_name():
        mesh = actor.get_component_by_class(unreal.StaticMeshComponent)
        report['props'].append({'position': vec(actor.get_actor_location()),
            'mesh_position': vec(mesh.get_world_location()), 'bounds': str(actor.get_actor_bounds(False)),
            'collision': str(mesh.get_collision_enabled()),
            'visibility_response': str(mesh.get_collision_response_to_channel(unreal.CollisionChannel.ECC_VISIBILITY))})
target = Path(unreal.Paths.project_dir()) / 'docs/agent/EVIDENCE/G1_focus_probe.json'
target.write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k != 'graphs'}))
