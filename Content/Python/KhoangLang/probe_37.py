import unreal
from editor_toolset.toolsets import blueprint as BP

R = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p37'
import os
os.makedirs(R, exist_ok=True)


def p(m):
    unreal.log('P37: ' + str(m))
    with open(os.path.join(R, 'r.txt'), 'a', encoding='utf-8') as f:
        f.write(str(m) + '\n')


p('unreal.DataAsset = %r  type=%s' % (unreal.DataAsset, type(unreal.DataAsset)))
p('isinstance(unreal.DataAsset, unreal.Class) = %s' % isinstance(unreal.DataAsset, unreal.Class))
for spec in ('/Script/Engine.DataAsset', '/Script/Engine.Actor',
             '/Script/Engine.ActorComponent', '/Script/Engine.HUD',
             '/Script/Engine.StaticMeshComponent', '/Script/Engine.SpotLightComponent',
             '/Script/Engine.PointLightComponent', '/Script/Engine.AudioComponent',
             '/Script/Engine.SphereComponent', '/Script/Engine.DirectionalLightComponent'):
    p('load_class %-40s -> %r' % (spec, unreal.load_class(None, spec)))
try:
    p('unreal.DataAsset.static_class() -> %r' % (unreal.DataAsset.static_class(),))
except Exception as exc:
    p('unreal.DataAsset.static_class() raised %r' % (exc,))
try:
    p('unreal.Actor.static_class() -> %r' % (unreal.Actor.static_class(),))
except Exception as exc:
    p('unreal.Actor.static_class() raised %r' % (exc,))

eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
eas.make_directory('/Game/KhoangLang/Data')
p('--- create attempts ---')
for spec, label in ((unreal.DataAsset, 'unreal.DataAsset'),
                    (unreal.DataAsset.static_class(), 'unreal.DataAsset.static_class()'),
                    (unreal.load_class(None, '/Script/Engine.DataAsset'), 'load_class'),
                    (unreal.Actor.static_class(), 'Actor.static_class()')):
    try:
        r = BP.BlueprintTools.create('/Game/KhoangLang/Data', 'TMP37_X', spec)
        p('%-32s -> %r  isinstance(Blueprint)=%s' % (
            label, r, isinstance(r, unreal.Blueprint) if r is not None else 'n/a'))
        if r is not None:
            try:
                unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP37_X')
            except Exception:
                pass
    except Exception as exc:
        p('%-32s raised %r' % (label, exc))
p('DONE')
