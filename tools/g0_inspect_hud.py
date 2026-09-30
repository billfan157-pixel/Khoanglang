"""Read-only Blueprint pin audit for the G0 school HUD failure."""

import unreal

from editor_toolset.toolsets.blueprint import BlueprintTools, _get_node_type_id


PATH = "/Game/KhoangLang/Blueprints/UI/BP_KL_HUD"
asset = unreal.load_asset(PATH)
if asset is None:
    unreal.log_error("G0HUD: HUD asset missing")
else:
    unreal.log("G0HUD: status=%s" % asset.get_editor_property("status"))
    for graph in BlueprintTools.list_graphs(asset):
        unreal.log("G0HUD: graph=%s" % graph.get_name())
        if graph.get_name() == "EventGraph":
            for target in ("CastToBP_KL_InvestigationComponent",
                           "CastToBP_KL_ListeningComponent"):
                unreal.log("G0HUD: cast candidates %s=%s" % (
                    target, BlueprintTools.find_node_types(graph, target)[:8]))
        editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        for node in editor.list_all_nodes():
            info = BlueprintTools.get_node_infos([node])[0]
            inputs = list(info.input_pins)
            outputs = list(info.output_pins)
            pin_names = {pin.name for pin in inputs}
            type_id = _get_node_type_id(node)
            if "self" not in pin_names and "ComponentClass" not in pin_names:
                continue
            unreal.log("G0HUD: node=%s type=%s title=%s" % (
                node.get_name(), type_id, node.get_node_title()))
            for side, pins in (("in", inputs), ("out", outputs)):
                for pin in pins:
                    if pin.name in ("self", "Target", "ComponentClass", "ReturnValue"):
                        unreal.log("G0HUD:   %s %s %s links=%s" % (
                            side, pin.name, pin.type_id, pin.connected_pins))
