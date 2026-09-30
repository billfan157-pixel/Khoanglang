"""Apply the verified visibility trace enum to the production character only."""
from pathlib import Path
import sys
import unreal

root = Path(unreal.Paths.project_dir())
sys.path.insert(0, str(root / 'tools'))
import g1_build_runtime as production
K, build = production.K, production.build
bp = unreal.load_asset(build.CHAR)
patched = 0
for graph in build.BPT.list_graphs(bp):
    if graph.get_name() != 'UpdateFocus':
        continue
    builder = K.B(graph, 'production visibility trace')
    for node in builder.ed.list_all_nodes():
        info = build.BPT.get_node_infos([node])[0]
        if any(p.name == 'TraceChannel' for p in info.input_pins):
            if not builder.setv(node, 'TraceChannel', 'TraceTypeQuery1'):
                raise RuntimeError('Could not set the trace channel')
            patched += 1
if patched != 1:
    raise RuntimeError('Expected exactly one production view trace, found %d' % patched)
build.BPT.compile_blueprint(bp)
if bp.get_editor_property('status') == unreal.BlueprintStatus.BS_ERROR:
    raise RuntimeError('Production character compile failed')
if not K.save(build.CHAR):
    raise RuntimeError('Production character save failed')
print('G1_TRACE_PATCHED=' + str(patched))
