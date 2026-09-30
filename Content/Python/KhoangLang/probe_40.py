import unreal

R = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p40'
import os
os.makedirs(R, exist_ok=True)


def p(m):
    unreal.log('P40: ' + str(m))
    with open(os.path.join(R, 'r.txt'), 'a', encoding='utf-8') as f:
        f.write(str(m) + '\n')


for path in ('/Game/KhoangLang/Blueprints/Core/BP_KL_InteractComponent',
             '/Game/KhoangLang/Blueprints/Core/BP_KL_ListeningComponent',
             '/Game/KhoangLang/Blueprints/Core/BP_KL_InvestigationComponent',
             '/Game/KhoangLang/UI/BP_KL_HUD',
             '/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter'):
    a = unreal.load_asset(path)
    p('%s -> asset=%s' % (path, a.get_class().get_name() if a else None))
    if a is None:
        continue
    try:
        gc = a.generated_class()
        p('   generated_class -> %r' % (gc,))
    except Exception as exc:
        p('   generated_class raised %r' % (exc,))
    name = path.rsplit('/', 1)[-1]
    p('   load_class plain -> %r' % (unreal.load_class(None, path),))
    p('   load_class _C    -> %r' % (unreal.load_class(None, '%s.%s_C' % (path, name)),))
    p('   all classes     -> %s' % ([c.get_name() for c in unreal.get_objects_with_outer(
        a, include_nested_objects=True) if c.get_class().get_name() == 'Class'][:8],))
p('DONE')
