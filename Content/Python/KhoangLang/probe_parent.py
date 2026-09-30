import unreal, traceback
import sys
sys.path.insert(0, r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang')
from editor_toolset.toolsets import blueprint as BP
from kl_kit import F_DATA, log

eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
eas.make_directory(F_DATA)

for cls in ('DataAsset', 'PrimaryDataAsset', 'Actor', 'Character', 'Pawn', 'HUD',
            'GameModeBase', 'PlayerController', 'ActorComponent'):
    try:
        c = getattr(unreal, cls)
        bp = BP.BlueprintTools.create(F_DATA, 'TMP_Par_' + cls, c.static_class())
        log('CREATE[%s] -> %s' % (cls, type(bp).__name__ if bp is not None else 'None'))
    except Exception as e:
        log('CREATE[%s] EXC %r' % (cls, e))

# also try DataTable row struct alternatives
for n in ('DataTable', 'StringTable', 'CurveTable', 'PrimaryDataAsset'):
    log('HAS %s = %s' % (n, hasattr(unreal, n)))

# BlueprintFactory direct route
try:
    at = unreal.AssetToolsHelpers.get_asset_tools()
    f = unreal.BlueprintFactory()
    f.set_editor_property('parent_class', unreal.DataAsset.static_class())
    b = at.create_asset('TMP_DirectDA', F_DATA, unreal.Blueprint, f)
    log('DIRECT_FACTORY -> %s' % (b.get_class().get_name() if b else 'None'))
except Exception as e:
    log('DIRECT_FACTORY EXC %r' % (e,))

log('DONE')
