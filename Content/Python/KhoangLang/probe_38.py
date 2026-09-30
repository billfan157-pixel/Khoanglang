import os
import unreal
from editor_toolset.toolsets import blueprint as BP

R = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p38'
os.makedirs(R, exist_ok=True)


def p(m):
    unreal.log('P38: ' + str(m))
    with open(os.path.join(R, 'r.txt'), 'a', encoding='utf-8') as f:
        f.write(str(m) + '\n')


eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
eas.make_directory('/Game/KhoangLang/Data')

CANDS = ['DataAsset', 'PrimaryDataAsset', 'Object', 'SaveGame', 'DataTable',
         'CurveBase', 'Blueprint', 'AnimSequence', 'SoundWave', 'Texture2D',
         'UserWidget', 'Widget', 'LevelBlueprint', 'DataTableRowBase', 'JsonObject']
for n in CANDS:
    try:
        cls = unreal.load_class(None, '/Script/Engine.' + n)
    except Exception as exc:
        p('%-18s load err %r' % (n, exc))
        continue
    if cls is None:
        p('%-18s load -> None' % n)
        continue
    try:
        b = BP.BlueprintTools.create('/Game/KhoangLang/Data', 'TMP38_%s' % n, cls)
        p('%-18s -> %s' % (n, ('OK ' + b.get_name()) if b is not None else 'None'))
        if b is not None:
            try:
                BP.BlueprintTools.add_variable(b, 'ProbeText', 'text')
                BP.BlueprintTools.compile_blueprint(b)
                p('       +variable ok, status=%s' % b.get_editor_property('status'))
            except Exception as exc:
                p('       variable failed %r' % (exc,))
            try:
                unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP38_%s' % n)
            except Exception:
                pass
    except Exception as exc:
        p('%-18s create raised %r' % (n, exc))

p('--- also try engine module paths ---')
for path in ('/Script/Engine.DataAsset', '/Script/Engine.Blueprint',
             '/Script/CoreUObject.Object', '/Script/Engine.BlueprintBaseLibrary'):
    p('%-44s -> %r' % (path, unreal.load_class(None, path)))
p('DONE')
