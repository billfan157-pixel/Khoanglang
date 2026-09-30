"""Read-only probe for Blueprint function purity APIs in the installed UE build."""

import inspect
import os
import sys

import unreal

HERE = os.path.dirname(__file__)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from editor_toolset.toolsets.blueprint import BlueprintTools as BPT  # noqa: E402

REPORT = os.path.join(HERE, 'probe_function_purity.report.txt')
lines = []


def note(value):
    value = str(value)
    lines.append(value)
    unreal.log('KLPURE: ' + value)


for label, obj in (
    ('BPT', BPT),
    ('BlueprintEditorLibrary', unreal.BlueprintEditorLibrary),
    ('BlueprintGraphEditor', unreal.BlueprintGraphEditor),
):
    names = [n for n in dir(obj) if any(k in n.lower() for k in
             ('pure', 'function', 'graph', 'flag'))]
    note(label + ': ' + ', '.join(names))

for owner, name in ((BPT, 'add_function_graph'),
                    (unreal.BlueprintGraphEditor, 'set_is_pure_function'),
                    (unreal.BlueprintGraphEditor, 'set_is_exec_function')):
    f = getattr(owner, name, None)
    if f:
        note('%s.%s doc=%s' % (owner.__name__, name, getattr(f, '__doc__', '')))
        try:
            note('source file=%s' % inspect.getsourcefile(f))
            note(inspect.getsource(f)[:1500])
        except Exception as exc:
            note('source unavailable: %r' % exc)

bp = unreal.load_asset('/Game/KhoangLang/Blueprints/Core/BP_KL_InvestigationComponent')
note('bp=%s' % bp)
for g in BPT.list_graphs(bp):
    if g.get_name() in ('GetHasTape', 'GetTitleStr', 'GetObjectiveStr'):
        note('graph %s class=%s' % (g.get_name(), g.get_class().get_name()))
        note('graph attrs: ' + ', '.join(n for n in dir(g) if any(k in n.lower()
             for k in ('pure', 'function', 'flag', 'meta'))))
        for prop in ('bIsPureFunc', 'FunctionFlags', 'function_flags', 'bIsPure'):
            try:
                note('  %s=%r' % (prop, g.get_editor_property(prop)))
            except Exception:
                pass

with open(REPORT, 'w', encoding='utf-8') as stream:
    stream.write('\n'.join(lines) + '\n')
