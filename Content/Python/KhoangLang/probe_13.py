"""Discovery probe 13: the three remaining risks.

  1. Cross-Blueprint call type ids (needed by every system).
  2. Key struct authoring so IMC mappings can be created from Python.
  3. The real id of the Delay node + HUD/player-controller accessors.
"""

import os
import sys
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
sys.path.insert(0, HERE)

OUT_DIR = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p13'
os.makedirs(OUT_DIR, exist_ok=True)
REPORT = []


def p(msg):
    line = str(msg)
    REPORT.append(line)
    unreal.log('KL13: ' + line)
    with open(os.path.join(OUT_DIR, 'report.txt'), 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


def keys_of():
    from editor_toolset.toolsets import blueprint as BP
    return BP


def main():
    BP = keys_of()
    at = unreal.AssetToolsHelpers.get_asset_tools()
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.make_directory('/Game/KhoangLang/Data')
    eas.make_directory('/Game/KhoangLang/Input')

    # ---------------------------------------------------------------- target bp
    target = BP.BlueprintTools.create('/Game/KhoangLang/Data', 'TMP13_Target',
                                      unreal.Actor.static_class())
    BP.BlueprintTools.add_variable(target, 'Label', 'string')
    fg = BP.BlueprintTools.add_function_graph(target, 'Ping')
    BP.BlueprintTools.add_function_param(fg, 'Result', 'string', False)
    BP.BlueprintTools.write_graph_dsl(
        fg, '(fn Ping ()\n  (return "pong"))')
    compile_ok = BP.BlueprintTools.compile_blueprint(target)
    p('target compile: %s' % compile_ok)

    # ---------------------------------------------------------------- caller bp
    caller = BP.BlueprintTools.create('/Game/KhoangLang/Data', 'TMP13_Caller',
                                      unreal.Actor.static_class())
    BP.BlueprintTools.add_object_variable(caller, 'TargetRef', unreal.Actor.static_class())
    g = BP.BlueprintTools.list_graphs(caller)[0]
    BP.BlueprintTools.compile_blueprint(caller)
    BP._BlueprintCache.invalidate(caller) if hasattr(BP, '_BlueprintCache') else None
    BP.BlueprintTools.list_graphs(caller)

    p('')
    p('=== 1. cross-BP ids seen from the CALLER graph ===')
    for probe in ('|Ping', 'Ping', 'TMP13', 'CastToTMP13', 'Label'):
        hits = BP.BlueprintTools.find_node_types(g, probe)
        p('  %-14s -> %s' % (probe, [h for h in hits if 'TMP13' in h or probe == 'Ping'][:8]
                             or hits[:4]))

    p('')
    p('=== 1b. transpile a cross-BP call for real ===')
    call_ids = [h for h in BP.BlueprintTools.find_node_types(g, 'Ping')
                if h.endswith('|Ping') or h == '|Ping']
    p('  candidates: %s' % call_ids)
    for cid in call_ids:
        try:
            ni = BP.BlueprintTools.get_node_type_pins(g, cid)
            p('  pins %s\n     IN [%s]\n     OUT [%s]' % (
                cid,
                ', '.join('%s:%s' % (x.name, x.type_id) for x in ni.input_pins),
                ', '.join('%s:%s' % (x.name, x.type_id) for x in ni.output_pins)))
        except Exception as exc:
            p('  pins %s FAILED %r' % (cid, exc))

    # real end-to-end write using the discovered id
    ok = False
    for cid in call_ids:
        try:
            BP.BlueprintTools.write_graph_dsl(g, (
                '(event EventBeginPlay\n'
                '  (Development|PrintString :InString %s))' % cid))
            ok = True
            p('  WRITE OK with id "%s"' % cid)
            break
        except Exception as exc:
            p('  WRITE FAILED with id "%s": %r' % (cid, exc))
    p('  cross-BP call usable: %s' % ok)

    p('')
    p('=== 1c. cast to the other blueprint ===')
    p('  CastToTMP13Target -> %s'
      % [h for h in BP.BlueprintTools.find_node_types(g, 'CastToTMP13')][:6])

    p('')
    p('=== 1d. own-BP function call id (sanity) ===')
    fgc = BP.BlueprintTools.add_function_graph(caller, 'Local')
    BP.BlueprintTools.write_graph_dsl(fgc, '(fn Local ()\n  (return 1))')
    BP.BlueprintTools.compile_blueprint(caller)
    p('  |Local -> %s' % [h for h in BP.BlueprintTools.find_node_types(g, 'Local')][:6])

    p('')
    p('=== 2. Key authoring ===')
    variants = {}
    try:
        k = unreal.Key()
        variants['bare'] = k.export_text()
    except Exception as exc:
        variants['bare'] = 'ERR %r' % (exc,)
    for name, fn in (
        ('set_editor_property', lambda: _key_setprop('E')),
        ('set_editor_properties', lambda: _key_setprops('E')),
        ('import_text', lambda: _key_import('E')),
    ):
        try:
            variants[name] = fn()
        except Exception as exc:
            variants[name] = 'ERR %r' % (exc,)
    for name, txt in variants.items():
        p('  %-22s %s' % (name, txt))

    p('')
    p('=== 2b. IMC mapping end to end ===')
    ia = at.create_asset('TMP13_IA', '/Game/KhoangLang/Input', unreal.InputAction,
                         unreal.InputAction_Factory())
    imc = at.create_asset('TMP13_IMC', '/Game/KhoangLang/Input',
                          unreal.InputMappingContext, unreal.InputMappingContext_Factory())
    k = _key_setprop('E')
    p('  key used: %s' % k.export_text())
    try:
        res = imc.map_key(ia, k)
        p('  map_key returned: %r' % (res,))
    except Exception as exc:
        p('  map_key raised: %r' % (exc,))
    for prop in ('mappings', 'default_key_mappings'):
        try:
            v = imc.get_editor_property(prop)
            p('  %s = %s' % (prop, v))
            for m in (v or []):
                p('     entry: %s' % m)
        except Exception as exc:
            p('  %s ERR %r' % (prop, exc))
    eas.save_directory('/Game/KhoangLang/Input', only_if_is_dirty=False, recursive=True)
    imc2 = unreal.load_asset('/Game/KhoangLang/Input/TMP13_IMC')
    try:
        p('  after reload mappings = %s' % imc2.get_editor_property('mappings'))
    except Exception as exc:
        p('  after reload ERR %r' % (exc,))
    p('  IMC pins: %s' % sorted(x for x in dir(imc) if not x.startswith('_')))

    p('')
    p('=== 3. remaining node ids ===')
    allids = BP.BlueprintTools.find_node_types(g, '')
    for pat in ('delay', 'gethud', 'owningplayer', 'setwindowtitle', 'quit', 'openlevel',
                'isvalid', 'tostring(text)'):
        hits = sorted(set(h for h in allids if pat in h.lower()))
        p('  %-18s %s' % (pat, hits[:10]))

    p('')
    p('=== 4. cleanup ===')
    for n in ('TMP13_Target', 'TMP13_Caller'):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/' + n)
    for n in ('TMP13_IA', 'TMP13_IMC'):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Input/' + n)
    p('PROBE13_DONE')


def _key_setprop(name):
    k = unreal.Key()
    k.set_editor_property('key_name', name)
    return k


def _key_setprops(name):
    k = unreal.Key()
    k.set_editor_properties({'key_name': name})
    return k


def _key_import(name):
    k = unreal.Key()
    k.import_text('(KeyName="%s")' % name)
    return k


try:
    rep = os.path.join(OUT_DIR, 'report.txt')
    if os.path.exists(rep):
        os.remove(rep)
    main()
except Exception:
    p(traceback.format_exc())
    p('PROBE13_FAILED')
