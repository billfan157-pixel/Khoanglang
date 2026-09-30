"""Read saved input graphs; this does not prove physical keyboard behavior."""
import json
from pathlib import Path
import unreal
from editor_toolset.toolsets import blueprint as BP

base = '/Game/KhoangLang/Production/G1Canon'
records, failures = [], []
expected = {'BP_KL_SchoolPlayer': {'W','A','S','D','F'},
            'BP_KL_SchoolLoop': {'Q','E','R','Enter','X','One','Two','Three','Four','J','V'}}
for asset, graph_name in [('BP_KL_SchoolPlayer','PollNativeInput'),
                          ('BP_KL_SchoolLoop','PollSchoolKeys')]:
    bp = unreal.load_asset(base+'/'+asset)
    graphs = [g for g in BP.BlueprintTools.list_graphs(bp) if g.get_name()==graph_name]
    if len(graphs)!=1:
        failures.append('Missing graph: '+asset+'/'+graph_name)
        continue
    nodes = unreal.BlueprintGraphEditor.get_graph_editor(graphs[0]).list_all_nodes()
    for node, info in zip(nodes,BP.BlueprintTools.get_node_infos(nodes)):
        if 'IsInputKeyDown' not in node.get_node_title() and 'WasInputKeyJustPressed' not in node.get_node_title():
            continue
        for pin in info.input_pins:
            if pin.name=='Key':
                records.append({'asset':asset,'graph':graph_name,'node':node.get_node_title(),'key':str(pin.value)})
                if str(pin.value) not in expected[asset]:
                    failures.append('Unexpected key: '+str(pin.value))
    actual = [r['key'] for r in records if r['asset']==asset]
    if set(actual)!=expected[asset] or len(actual)!=len(expected[asset]):
        failures.append('Missing or duplicate declared key: '+asset)
report={'status':'passed' if records and not failures else 'failed',
        'keys':records,'failures':failures,'physical_input_qualified':False}
(Path(unreal.Paths.project_dir())/'docs/agent/EVIDENCE/G1_input_pin_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
