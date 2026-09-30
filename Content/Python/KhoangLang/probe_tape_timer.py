"""Read-only node/pin discovery for the tape completion timer."""

import os

import unreal
from editor_toolset.toolsets.blueprint import BlueprintTools as BPT

bp = unreal.load_asset('/Game/KhoangLang/Blueprints/Core/BP_KL_InteractComponent')
graph = next(g for g in BPT.list_graphs(bp) if g.get_name() == 'DoTape')
queries = ('SetTimerbyFunctionName', 'ClearTimerbyFunctionName',
           'IsTimerActivebyFunctionName', 'IsPlaying', 'GetDuration',
           'Variables|Getareferencetoself', 'Actor|GetActorOfClass')
lines = []
for q in queries:
    hits = BPT.find_node_types(graph, q)
    lines.append('%s: %s' % (q, hits[:12]))
    for hit in hits[:3]:
        try:
            info = BPT.get_node_type_pins(graph, hit)
            lines.append('  %s IN=%s OUT=%s' % (
                hit,
                [(p.name, p.type_id) for p in info.input_pins],
                [(p.name, p.type_id) for p in info.output_pins]))
        except Exception as exc:
            lines.append('  %s ERROR=%r' % (hit, exc))

out = os.path.join(os.path.dirname(__file__), 'probe_tape_timer.report.txt')
with open(out, 'w', encoding='utf-8') as stream:
    stream.write('\n'.join(lines) + '\n')
for line in lines:
    unreal.log('KLTIMER: ' + line)
