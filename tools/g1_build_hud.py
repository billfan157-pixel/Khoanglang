"""Rebuild only the production HUD after a display repair."""
import importlib
from pathlib import Path
import sys
import unreal
sys.path.insert(0, str(Path(unreal.Paths.project_dir()) / 'tools'))
import g1_build_runtime as production
importlib.reload(production)
production.build.build_hud()
if production.K.FAILS:
    raise RuntimeError(str(production.K.FAILS))
print('G1_HUD_REBUILT')
