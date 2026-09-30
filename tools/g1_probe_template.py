"""Inspect reusable template functions and graph-edit APIs."""
import unreal
from editor_toolset.toolsets.blueprint import BlueprintTools as BPT
bp = unreal.load_asset('/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter')
for graph in BPT.list_graphs(bp):
    print('GRAPH', graph.get_name())
    if graph.get_name() in ('Aim', 'Move', 'Look'):
        for n in unreal.BlueprintGraphEditor.get_graph_editor(graph).list_all_nodes():
            if n.get_class().get_name() == 'K2Node_FunctionEntry':
                print('ENTRY', [(p.name, str(p.type_id)) for p in BPT.get_node_infos([n])[0].output_pins])
print('BlueprintGraphEditor', [n for n in dir(unreal.BlueprintGraphEditor) if any(s in n for s in ('disconnect','break','remove'))])
g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
print('SEQUENCE', [n for n in BPT.find_node_types(g, 'Sequence') if n.endswith('|Sequence')])
print('ARITHMETIC', BPT.find_node_types(g, 'Multiply')[:12])
print('ADD', BPT.find_node_types(g, 'Add_Vector')[:12])
