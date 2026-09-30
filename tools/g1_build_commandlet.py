"""Build production copies and stage the school with no viewport dependency."""

import importlib
from pathlib import Path
import runpy
import sys
import unreal

root = Path(unreal.Paths.project_dir())
sys.path.insert(0, str(root / 'tools'))
import g1_build_runtime as production
importlib.reload(production)
production.main()
runpy.run_path(str(root / 'tools/g1_fix_prompt.py'), run_name='__main__')
runpy.run_path(str(root / 'tools/g1_build_player.py'), run_name='__main__')
runpy.run_path(str(root / 'tools/g1_open_primary_school.py'), run_name='__main__')
print('G1_BUILD_PRIMARY_COMPLETE')
