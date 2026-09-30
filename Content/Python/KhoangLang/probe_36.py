"""Discovery probe 36: comparison / logic / string nodes + pin literal formats."""

import os
import sys
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
sys.path.insert(0, HERE)

OUT_DIR = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\p36'
os.makedirs(OUT_DIR, exist_ok=True)


def p(msg):
    line = str(msg)
    unreal.log('KL36: ' + line)
    with open(os.path.join(OUT_DIR, 'report.txt'), 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


def pins(node):
    from editor_toolset.toolsets import blueprint as BP
    ni = BP.BlueprintTools.get_node_infos([node])[0]
    ins = ', '.join('%s:%s' % (x.name, x.type_id) for x in ni.input_pins)
    outs = ', '.join('%s:%s' % (x.name, x.type_id) for x in ni.output_pins)
    return 'IN [%s] OUT [%s]' % (ins, outs)


PATHS = [
    '/Script/Engine.KismetMathLibrary:EqualEqual_IntInt',
    '/Script/Engine.KismetMathLibrary:NotEqual_IntInt',
    '/Script/Engine.KismetMathLibrary:NotEqualEqual_IntInt',
    '/Script/Engine.KismetMathLibrary:EqualEqual_BoolBool',
    '/Script/Engine.KismetMathLibrary:Add_IntInt',
    '/Script/Engine.KismetMathLibrary:Subtract_IntInt',
    '/Script/Engine.KismetMathLibrary:Multiply_IntInt',
    '/Script/Engine.KismetMathLibrary:Greater_IntInt',
    '/Script/Engine.KismetMathLibrary:GreaterEqual_IntInt',
    '/Script/Engine.KismetMathLibrary:Less_IntInt',
    '/Script/Engine.KismetMathLibrary:Not_BoolBool',
    '/Script/Engine.KismetMathLibrary:And_BoolBool',
    '/Script/Engine.KismetMathLibrary:Or_BoolBool',
    '/Script/Engine.KismetMathLibrary:Not',
    '/Script/Engine.KismetMathLibrary:SelectInt',
    '/Script/Engine.KismetMathLibrary:Conv_TextToString',
    '/Script/Engine.KismetTextLibrary:Conv_StringToText',
    '/Script/Engine.KismetTextLibrary:Conv_TextToString',
    '/Script/Engine.KismetStringLibrary:Conv_StringToText',
    '/Script/Engine.KismetMathLibrary:Conv_IntToString',
    '/Script/Engine.KismetStringLibrary:Conv_IntToString',
    '/Script/Engine.KismetStringLibrary:PrintString',
    '/Script/Engine.GameplayStatics:SetSubtitleText',
    '/Script/Engine.SoundMix',
    '/Script/Engine.AudioComponent:AudioDevice',
]

NAMES = [
    'Math|Integer|==',
    'Math|Integer|!=',
    'Math|Integer|+',
    'Math|Integer|Increment',
    'Math|Boolean|!',
    'Math|Boolean|AND',
    'Math|Comparison|Equal(Int)',
    'Math|Comparison|Equal(Integer)',
    'Utilities|String|EqualEqual(Str)',
    'Utilities|String|==',
    'Utilities|Array|Get(aref)',
    'Utilities|Array|Get',
    'Utilities|Array|Set',
    'Utilities|Struct|MakeKey',
    'Utilities|Select',
    'Utilities|Text|ToText(String)',
    'Utilities|String|ToString(Text)',
    'Utilities|String|Conv_TextToString',
    'Utilities|String|ToString(Text)',
    'Class|GameplayStatics|SetGamePaused',
    'Audio|PlaySound2D',
    'Audio|PlaySoundAtLocation',
    'Audio|Components|Audio|SetVolumeMultiplier',
    'Rendering|Components|Light|SetIntensity',
    'Components|Activation|Deactivate',
    'Components|Activation|IsActive',
    'Development|SetHiddenInGame',
    'Collision|BreakHitResult',
    'Utilities|FlowControl|Branch',
]


def main():
    from editor_toolset.toolsets import blueprint as BP
    BPT = BP.BlueprintTools
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    eas.make_directory('/Game/KhoangLang/Data')
    if unreal.load_asset('/Game/KhoangLang/Data/TMP36'):
        unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP36')
    bp = BPT.create('/Game/KhoangLang/Data', 'TMP36', unreal.Actor.static_class())
    BPT.add_variable(bp, 'Steps', 'int')
    BPT.add_variable(bp, 'Line', 'text')
    BPT.add_object_variable(bp, 'Items', unreal.DataAsset.static_class(), None,
                            BP.ContainerType.ARRAY)
    BPT.compile_blueprint(bp)
    g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)

    p('=== A. paths ===')
    for path in PATHS:
        try:
            n = ed.add_call_function_node(path)
        except Exception as exc:
            p('  RAISE %-56s %r' % (path, exc))
            continue
        if n is None:
            p('  MISS  %s' % path)
            continue
        p('  OK    %-56s %s' % (path, pins(n)))
        ed.remove_nodes([n])

    p('')
    p('=== B. names ===')
    for nid in NAMES:
        try:
            n = ed.create_node_from_name(nid, unreal.Vector2D(0, 0), [], None)
        except Exception as exc:
            p('  RAISE %-46s %r' % (nid, exc))
            continue
        if n is None:
            p('  MISS  %s' % nid)
            continue
        p('  OK    %-46s %s' % (nid, pins(n)))
        ed.remove_nodes([n])

    p('')
    p('=== C. pin literal formats on real pins ===')
    n = ed.create_node_from_name('Utilities|Text|ToText(String)', unreal.Vector2D(0, 0), [], None)
    ni = BPT.get_node_infos([n])[0]
    sp = ni.input_pins[0]
    for c in ('Xin chào', '"Xin chào"', 'Sổ điểm danh tập kết - 21/9/2002', 'A\nB'):
        try:
            BPT.set_pin_value(sp.pin_id, c)
            p('  string pin set %-42r -> %r' % (c, BPT.get_pin_value(sp.pin_id)))
        except Exception as exc:
            p('  string pin set %-42r raised %r' % (c, exc))
    ed.remove_nodes([n])

    n = ed.create_node_from_name('Utilities|Array|Get(aref)', unreal.Vector2D(0, 0), [], None)
    if n is not None:
        ni = BPT.get_node_infos([n])[0]
        getter = ed.add_get_member_variable_node(unreal.Name('Items'))
        gin = BPT.get_node_infos([getter])[0]
        ai = [x for x in ni.input_pins if 'Array' in x.name]
        if ai:
            BPT.connect_pins(next(x for x in gin.output_pins if x.type_id != 'Exec').pin_id,
                             ai[0].pin_id)
            BPT.compile_blueprint(bp)
            p('  array-get wired; status=%s errors=%s' % (
                bp.get_editor_property('status'),
                [n_.error_msg() for n_ in ed.list_all_nodes() if n_.has_error()]))
        ed.remove_nodes([n])
    if n is None:
        p('  array get (aref) not available')

    p('')
    p('=== D. function graph with params: text/array/object ===')
    try:
        fg = BPT.add_function_graph(bp, 'KL_Probe2')
        BPT.add_function_param(fg, 'InT', 'text', True)
        BPT.add_function_param(fg, 'InB', 'bool', True)
        BPT.add_function_param(fg, 'InI', 'int', True)
        BPT.add_function_param(fg, 'OutS', 'string', False)
        hed = unreal.BlueprintGraphEditor.get_graph_editor(fg)
        conv = hed.create_node_from_name('Utilities|String|ToString(Text)',
                                         unreal.Vector2D(0, 0), [], None)
        ret = hed.add_return_node()
        ri = BPT.get_node_infos([ret])[0]
        ci = BPT.get_node_infos([conv])[0]
        p('  conv %s' % pins(conv))
        p('  ret  %s' % pins(ret))
        p('  return input pins: %s' % [(x.name, x.type_id) for x in ri.input_pins])
        try:
            BPT.connect_pins(next(x for x in ci.output_pins
                                  if x.type_id != 'Exec').pin_id,
                             ri.input_pins[0].pin_id)
            p('  linked')
        except Exception as exc:
            p('  link raised %r' % (exc,))
        BPT.compile_blueprint(bp)
        p('  status %s' % bp.get_editor_property('status'))
        p('  errors: %s' % [n_.error_msg() for n_ in hed.list_all_nodes() if n_.has_error()])
        p('  dsl:')
        for ln in str(BPT.read_graph_dsl(fg)).splitlines():
            p('    | %s' % ln)
    except Exception:
        p(traceback.format_exc())

    p('')
    p('=== E. cleanup ===')
    unreal.EditorAssetLibrary.delete_asset('/Game/KhoangLang/Data/TMP36')
    p('PROBE36_DONE')


try:
    rep = os.path.join(OUT_DIR, 'report.txt')
    if os.path.exists(rep):
        os.remove(rep)
    main()
except Exception:
    p(traceback.format_exc())
    p('PROBE36_DONE_FATAL')
