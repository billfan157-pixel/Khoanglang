"""Inspect initialization wiring and time advancement without editing assets."""

import json
from pathlib import Path
import unreal
from editor_toolset.toolsets.blueprint import BlueprintTools as BPT

report = {"graphs": []}
for path in (
    "/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter",
    "/Game/KhoangLang/Blueprints/Core/BP_KL_InteractComponent",
):
    bp = unreal.load_asset(path)
    for graph in BPT.list_graphs(bp):
        if graph.get_name() not in ("EventGraph", "InitKL", "DoTape", "Move", "Look"):
            continue
        entry = {"asset": path, "graph": graph.get_name(), "nodes": []}
        for node in unreal.BlueprintGraphEditor.get_graph_editor(graph).list_all_nodes():
            info = BPT.get_node_infos([node])[0]
            entry["nodes"].append({"title": node.get_node_title(),
                "inputs": [{"name": p.name, "type": str(p.type_id),
                            "links": len(p.connected_pins)} for p in info.input_pins],
                "outputs": [{"name": p.name, "type": str(p.type_id),
                             "links": len(p.connected_pins)} for p in info.output_pins]})
        report["graphs"].append(entry)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
report["game_time"] = unreal.GameplayStatics.get_time_seconds(world)
report["paused"] = unreal.GameplayStatics.is_game_paused(world)
target = Path(unreal.Paths.project_dir()) / "docs/agent/EVIDENCE/G0_graph_runtime_audit.json"
target.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"report": target.name, "game_time": report["game_time"],
                  "paused": report["paused"], "graphs": len(report["graphs"])}))
