"""Discovery probe 14: are cross-Blueprint calls / casts reachable once the
target Blueprints are SAVED to disk?  This decides the whole architecture.
"""

import os
import sys
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
sys.path.insert(0, HERE)

OUT_DIR = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p14'
os.makedirs(OUT_DIR, exist_ok=True)
REPORT = []


def p(msg):
    line = str(msg)
    REPORT.append(line)
    unreal.log('KL14: ' + line)
    with open(os.path.join(OUT_DIR, 'report.txt'), 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


def main():
    from editor_toolset.toolsets import blueprint as BP
    from editor_toolset.toolsets import actor as ACT
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    at = unreal.AssetToolsHelpers.get_asset_tools()
    eas.make_directory('/Game/KhoangLang/Data')

    # ---- target actor blueprint, saved
    for n in ('TMP14_Target', 'TMP14_Caller'):
        if unreal.load_asset('/Game/KhoangLang/Data/' + n):
            unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/' + n)

    tgt = BP.BlueprintTools.create('/Game/KhoangLang/Data', 'TMP14_Target',
                                   unreal.Actor.static_class())
    ACT.ActorTools.add_component(tgt, unreal.SpotLightComponent.static_class(), 'KLFlash')
    BP.BlueprintTools.add_variable(tgt, 'Label', 'string')
    fg = BP.BlueprintTools.add_function_graph(tgt, 'Ping')
    BP.BlueprintTools.add_function_param(fg, 'Result', 'string', False)
    BP.BlueprintTools.write_graph_dsl(fg, '(fn Ping ()\n  (return "pong"))')
    BP.BlueprintTools.compile_blueprint(tgt)
    BP.BlueprintTools.set_variable_instance_editable(tgt, 'Label', True)
    BP.BlueprintTools.get_default_object(tgt).set_editor_property('Label', 'hello')
    eas.save_asset('/Game/KhoangLang/Data/TMP14_Target', only_if_is_dirty=False)
    p('target saved: %s' % unreal.EditorAssetLibrary.does_asset_exist(
        '/Game/KhoangLang/Data/TMP14_Target'))
    tgt_cls = unreal.load_class(None, '/Game/KhoangLang/Data/TMP14_Target.TMP14_Target_C')
    p('target class: %s' % (tgt_cls.get_name() if tgt_cls else None))

    cal = BP.BlueprintTools.create('/Game/KhoangLang/Data', 'TMP14_Caller',
                                   unreal.Actor.static_class())
    g = BP.BlueprintTools.list_graphs(cal)[0]
    BP.BlueprintTools.compile_blueprint(cal)
    eas.save_asset('/Game/KhoangLang/Data/TMP14_Caller', only_if_is_dirty=False)

    p('')
    p('=== node count in caller graph ===')
    allids = BP.BlueprintTools.find_node_types(g, '')
    p('  %d ids' % len(allids))
    p('  has Utilities|IsValid: %s' % ('Utilities|IsValid' in allids))
    p('  has HUD|DrawText    : %s' % ('HUD|DrawText' in allids))
    p('  has Delay candidates: %s' % [h for h in allids if 'Delay' in h and 'Audio' not in h][:8])

    p('')
    p('=== cross-BP ids ===')
    for probe in ('|Ping', 'TMP14', 'CastToTMP14', 'Ping'):
        hits = BP.BlueprintTools.find_node_types(g, probe)
        p('  %-14s %s' % (probe, hits[:10]))

    p('')
    p('=== try writing a cross-BP call by brute-force id shapes ===')
    shapes = ['TMP14_Target_C|Ping', 'TMP14_Target|Ping', '|Ping',
              'Class|TMP14_Target_C|Ping', 'Class|TMP14_Target|Ping']
    worked = None
    for sid in shapes:
        try:
            BP.BlueprintTools.write_graph_dsl(g, (
                '(event EventBeginPlay\n'
                '  (Development|PrintString :InString %s))' % sid))
            worked = sid
            p('  WORKED: %s' % sid)
            break
        except Exception as exc:
            p('  fail %-28s %s' % (sid, str(exc)[:160]))
    p('  cross-BP call id: %s' % worked)

    p('')
    p('=== try casting to the saved blueprint class ===')
    cast_shapes = ['Utilities|Casting|CastToTMP14_Target', 'Utilities|Casting|CastToTMP14Target']
    cast_ok = None
    for cid in cast_shapes:
        try:
            BP.BlueprintTools.write_graph_dsl(g, (
                '(event EventBeginPlay\n'
                '  (bind hit (Collision|SphereTraceByChannel '
                ':Start (Transformation|GetActorLocation) :End (Transformation|GetActorLocation) '
                ':TraceChannel "Visibility")\n'
                '  (bind t %s :Object _hit_result))\n'
                '  (Development|PrintString :InString "cast-ok"))' % cid))
            cast_ok = cid
            p('  WORKED: %s' % cid)
            break
        except Exception as exc:
            p('  fail %-46s %s' % (cid, str(exc)[:200]))
    p('  cast id: %s' % cast_ok)

    p('')
    p('=== class-pin trick: GetActorOfClass with a BP class pin ===')
    try:
        BP.BlueprintTools.write_graph_dsl(g, (
            '(event EventBeginPlay\n'
            '  (bind found (Actor|GetActorOfClass :ActorClass "/Game/KhoangLang/Data/'
            'TMP14_Target.TMP14_Target_C"))\n'
            '  (Development|PrintString :InString (Utilities|String|ToString found)))'))
        p('  GetActorOfClass with BP class pin: OK')
    except Exception as exc:
        p('  GetActorOfClass with BP class pin FAILED: %s' % str(exc)[:300])

    p('')
    p('=== can we call a BP function on that result without a cast? ===')
    for sid in (worked and [worked] or []) + shapes:
        try:
            BP.BlueprintTools.write_graph_dsl(g, (
                '(event EventBeginPlay\n'
                '  (bind found (Actor|GetActorOfClass :ActorClass "/Game/KhoangLang/Data/'
                'TMP14_Target.TMP14_Target_C"))\n'
                '  (Development|PrintString :InString %s))' % sid))
            p('  call on GetActorOfClass result WORKS with id %s' % sid)
            break
        except Exception as exc:
            p('  call on result fails %-26s %s' % (sid, str(exc)[:200]))

    p('')
    p('=== property setter/getter on components of another bp ===')
    try:
        BP.BlueprintTools.write_graph_dsl(g, (
            '(event EventBeginPlay\n'
            '  (bind found (Actor|GetActorOfClass :ActorClass "/Game/KhoangLang/Data/'
            'TMP14_Target.TMP14_Target_C"))\n'
            '  (bind comp (Actor|GetComponentbyClass :self found '
            ':ComponentClass "/Script/Engine.SpotLightComponent"))\n'
            '  (Rendering|SetVisibility :self comp :bNewVisibility false))'))
        p('  component-by-class on BP actor result: OK')
    except Exception as exc:
        p('  component-by-class on BP actor result FAILED: %s' % str(exc)[:300])

    p('')
    p('=== blueprint interface factory test ===')
    try:
        ifact = at.create_asset('TMP14_IKL', '/Game/KhoangLang/Data', unreal.Interface,
                                unreal.BlueprintInterfaceFactory())
        p('  interface asset: %s' % ifact)
        p('  interface class: %s'
          % unreal.load_class(None, '/Game/KhoangLang/Data/TMP14_IKL.TMP14_IKL_C'))
    except Exception as exc:
        p('  interface FAILED: %r' % (exc,))

    p('')
    p('=== cleanup ===')
    for n in ('TMP14_Target', 'TMP14_Caller', 'TMP14_IKL'):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/' + n)
    p('PROBE14_DONE')


try:
    rep = os.path.join(OUT_DIR, 'report.txt')
    if os.path.exists(rep):
        os.remove(rep)
    main()
except Exception:
    p(traceback.format_exc())
    p('PROBE14_FAILED')
