"""Save measured torch intensity on our native player template; no graph rebuild."""
import hashlib
import json
from pathlib import Path
import sys
import unreal
ROOT = Path(unreal.Paths.project_dir())
sys.path.insert(0, str(ROOT / 'Content/Python/KhoangLang'))
import kl_core as K
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    raise RuntimeError('Stop PIE before saving template calibration')
bp = unreal.load_asset('/Game/KhoangLang/Production/G1Canon/BP_KL_SchoolPlayer')
lamp = K.find_comp_of(bp, 'SpotLightComponent')
if lamp is None:
    raise RuntimeError('Native player lamp template missing')
bp.modify()
lamp.modify()
lamp.set_editor_property('intensity', 90.)
if abs(lamp.get_editor_property('intensity') - 90.) > .001:
    raise RuntimeError('Torch intensity readback differs')
if not unreal.EditorAssetLibrary.save_loaded_asset(bp, False):
    raise RuntimeError('Player template save failed')
asset = ROOT / 'Content/KhoangLang/Production/G1Canon/BP_KL_SchoolPlayer.uasset'
report = {'lumens': 90, 'asset_sha256': hashlib.sha256(asset.read_bytes()).hexdigest(),
          'method': 'Native SCS light template property save; fresh PIE/package must verify propagation',
          'runtime_qualified': False}
(ROOT / 'docs/agent/EVIDENCE/G1_torch_calibration.json').write_text(
    json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report))
