"""Build corrected gameplay in a separate production asset namespace.

Run through ue_live.py with PIE stopped. Original prototype assets are read-only.
"""

import importlib
import json
from pathlib import Path
import sys
import unreal

root = Path(unreal.Paths.project_dir())
sys.path.insert(0, str(root / 'Content/Python/KhoangLang'))
import kl_core as K
import build_20_blueprints as build
importlib.reload(K)
importlib.reload(build)

production = '/Game/KhoangLang/Production'
K.MAP_NAME = 'Lvl_KL_School3_Primary'
K.MAP_PATH = production + '/Maps/' + K.MAP_NAME
K.F_CORE = production + '/Blueprints/Core'
K.F_PLAYER = production + '/Blueprints/Player'
K.F_UI = production + '/Blueprints/UI'
for folder in (K.F_CORE, K.F_PLAYER, K.F_UI):
    unreal.EditorAssetLibrary.make_directory(folder)
build.INV = K.F_CORE + '/BP_KL_InvestigationComponent'
build.LIS = K.F_CORE + '/BP_KL_ListeningComponent'
build.INT = K.F_CORE + '/BP_KL_InteractComponent'
build.HUD = K.F_UI + '/BP_KL_HUD'
build.GM = K.F_PLAYER + '/BP_KL_GameMode'
build.CHAR = K.F_PLAYER + '/BP_KL_Character'

def main():
    build.build_investigation(repair_definition=False)
    build.build_listening()
    build.build_interact()
    if K.FAILS:
        raise RuntimeError('Production core build errors: ' + str(K.FAILS))
    report = {}
    for path in (build.INV, build.LIS, build.INT):
        asset = unreal.load_asset(path)
        status = str(asset.get_editor_property('status'))
        report[path] = status
        if asset.get_editor_property('status') == unreal.BlueprintStatus.BS_ERROR:
            raise RuntimeError('Compile failed: ' + path)
    target = root / 'docs/agent/EVIDENCE/G1_core_build.json'
    target.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
