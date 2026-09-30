"""Repair the reversed consumed-state prompt in production assets only."""
import importlib
from pathlib import Path
import sys
import unreal
sys.path.insert(0, str(Path(unreal.Paths.project_dir()) / 'tools'))
import g1_build_runtime as production
importlib.reload(production)
K, build = production.K, production.build
bp = unreal.load_asset(build.INT)
g, b, e = build.newfn(bp, 'GetPromptStr', out=('ReturnValue', 'string'))
consumed = b.g('MsgConsumed')
prompt = b.g('PromptText')
a = b.text2str(consumed, b.out_any(consumed).name)
pn = b.text2str(prompt, b.out_any(prompt).name)
s = build.selb(b, (pn, 'ReturnValue'), (a, 'ReturnValue'), build.bv(b, 'bConsumed'))
b.ret(s[0], s[1])
b.compile(bp, 'correct consumed prompt')
if K.FAILS or not K.save(build.INT):
    raise RuntimeError('Production prompt repair failed')
print('G1_PROMPT_REPAIRED')
