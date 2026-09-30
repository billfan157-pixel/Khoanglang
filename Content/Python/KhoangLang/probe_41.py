import os
import sys
import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from editor_toolset.toolsets import blueprint as BP  # noqa: E402

R = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p41'
os.makedirs(R, exist_ok=True)


def p(m):
    unreal.log('P41: ' + str(m))
    with open(os.path.join(R, 'r.txt'), 'a', encoding='utf-8') as f:
        f.write(str(m) + '\n')


path = '/Game/KhoangLang/Blueprints/Core/BP_KL_InteractComponent'
bp = unreal.load_asset(path)
p('asset=%s status=%s' % (bp, bp.get_editor_property('status')))
try:
    BP.BlueprintTools.compile_blueprint(bp, warnings_as_errors=False)
    p('compile ok, status=%s' % bp.get_editor_property('status'))
except Exception as exc:
    p('compile raised %r' % (exc,))
for g in BP.BlueprintTools.list_graphs(bp):
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    ni_list = []
    for n in ed.list_all_nodes():
        try:
            if n.has_error():
                ni_list.append('%s -> %s' % (n.get_name(), n.error_msg()))
        except Exception as exc:
            ni_list.append('%s -> has_error raised %r' % (n.get_name(), exc))
    if ni_list:
        p('graph %s:' % g.get_name())
        for x in ni_list:
            p('   %s' % x)
p('--- decompiled ---')
for g in BP.BlueprintTools.list_graphs(bp):
    p('### %s' % g.get_name())
    try:
        for ln in str(BP.BlueprintTools.read_graph_dsl(g)).splitlines():
            p('  | %s' % ln)
    except Exception as exc:
        p('  dsl err %r' % (exc,))
p('DONE')
