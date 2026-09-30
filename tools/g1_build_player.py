"""Copy the baseline character, restore input, and build a production HUD."""

import importlib
import json
from pathlib import Path
import sys
import unreal

root = Path(unreal.Paths.project_dir())
sys.path.insert(0, str(root / 'tools'))
import g1_build_runtime as production
importlib.reload(production)
K, build = production.K, production.build
from editor_toolset.toolsets.actor import ActorTools

if not unreal.EditorAssetLibrary.does_asset_exist(build.CHAR):
    character = unreal.EditorAssetLibrary.duplicate_asset(K.BP_TPL_CHAR, build.CHAR)
    if character is None:
        raise RuntimeError('Could not copy baseline character')
    for component in list(K.cdo_components(character)):
        if component.get_class().get_name() in (
                'BP_KL_InvestigationComponent_C', 'BP_KL_ListeningComponent_C'):
            ActorTools.remove_component(component)
    for name in ('FocusCand', 'FocusPrev'):
        build.BPT.remove_variable(character, name)
else:
    character = unreal.load_asset(build.CHAR)

build.build_character()

# Replace the zero-length sphere search with a view-directed, guarded trace.
g, b, e = build.newfn(character, 'UpdateFocus')

def valid(ref):
    node = b.c(K.F_ISVALID)
    b.link(ref[0], ref[1], node, 'Object')
    return (node, 'ReturnValue')

def variable(name):
    node = b.g(name)
    return (node, b.out_any(node).name)

def component(path):
    return build.self_comp(b, path)

def invoke(path, name, ref):
    node = build.callbp(b, path, name)
    b.link(ref[0], ref[1], node, 'self')
    return node

previous = variable('FocusCand')

def clear_previous(en):
    node = invoke(build.INT, 'SetFocused', previous)
    for pin in ('bFocused', 'bFilter', 'bHasDoc', 'bHasTape', 'bTapeHeard'):
        b.setv(node, pin, 'false')
    return build.cont(b, en, node)

e = build.iff(b, e, lambda: valid(previous), then_fn=clear_previous)
clear = b.s('FocusCand')
b.setv(clear, 'FocusCand', 'None')
e = build.cont(b, e, clear)
inv = component(build.INV)
e = build.cont(b, e, invoke(build.INV, 'ClearPrompt', inv))
camera = b.c('/Script/Engine.GameplayStatics:GetPlayerCameraManager')
b.setv(camera, 'PlayerIndex', '0')
location = b.c('/Script/Engine.PlayerCameraManager:GetCameraLocation')
rotation = b.c('/Script/Engine.PlayerCameraManager:GetCameraRotation')
for node in (location, rotation):
    b.link(camera, 'ReturnValue', node, 'self')
forward = b.c('/Script/Engine.KismetMathLibrary:GetForwardVector')
b.link(rotation, 'ReturnValue', forward, 'InRot')
offset = b.c('/Script/Engine.KismetMathLibrary:Multiply_VectorFloat')
# A connected scalar keeps Unreal's promoted operator from changing B to Vector.
distance = b.c('/Script/Engine.KismetSystemLibrary:MakeLiteralDouble')
b.setv(distance, 'Value', '260.0')
b.link(distance, 'ReturnValue', offset, 'B')
b.link(forward, 'ReturnValue', offset, 'A')
if 'Vector' in str(b.inp(offset, 'B').type_id):
    raise RuntimeError('View trace multiplier lost its scalar input')
end = b.c('/Script/Engine.KismetMathLibrary:Add_VectorVector')
b.link(location, 'ReturnValue', end, 'A')
b.link(offset, 'ReturnValue', end, 'B')
trace = b.c('/Script/Engine.KismetSystemLibrary:LineTraceSingle')
b.link(location, 'ReturnValue', trace, 'Start')
b.link(end, 'ReturnValue', trace, 'End')
b.setv(trace, 'TraceChannel', 'TraceTypeQuery1')
b.setv(trace, 'DrawDebugType', 'EDrawDebugTrace::None')
b.setv(trace, 'bIgnoreSelf', 'true')
e = build.cont(b, e, trace)
hit = b.n(K.F_BREAK_HIT)
b.link(trace, 'OutHit', hit, 'Hit')
actor = (hit, 'HitActor')
interaction = build.comp_of_ref(b, actor, build.INT)

def focus(en):
    store = b.s('FocusCand')
    b.link(interaction[0], interaction[1], store, 'FocusCand')
    en = build.cont(b, en, store)
    node = invoke(build.INT, 'SetFocused', interaction)
    b.setv(node, 'bFocused', 'true')
    for pin, path, getter in (
        ('bFilter', build.LIS, 'IsFilterOn'),
        ('bHasDoc', build.INV, 'GetHasDoc'),
        ('bHasTape', build.INV, 'GetHasTape'),
        ('bTapeHeard', build.INV, 'GetTapeHeard'),
    ):
        query = invoke(path, getter, component(path))
        b.link(query, 'ReturnValue', node, pin)
    en = build.cont(b, en, node)
    prompt = invoke(build.INT, 'GetPromptStr', interaction)
    setter = invoke(build.INV, 'SetPromptFromString', inv)
    b.link(prompt, 'ReturnValue', setter, 'InS')
    return build.cont(b, en, setter)

build.iff(b, e, lambda: valid(actor), then_fn=lambda en:
          build.iff(b, en, lambda: valid(interaction), then_fn=focus))
b.ret()
b.compile(character, 'view-directed UpdateFocus')
if not K.save(build.CHAR):
    raise RuntimeError('Character save failed; check file locks')
# Preserve already qualified UI/game mode when updating character routing.
# Rebuilding their live graphs is unnecessary and has triggered an editor
# access violation; dedicated UI repair scripts remain available.
if not unreal.EditorAssetLibrary.does_asset_exist(build.HUD):
    build.build_hud()
if not unreal.EditorAssetLibrary.does_asset_exist(build.GM):
    build.build_gamemode()
report = {}
for path in (build.CHAR, build.HUD, build.GM):
    bp = unreal.load_asset(path)
    status = bp.get_editor_property('status')
    report[path] = str(status)
    if status == unreal.BlueprintStatus.BS_ERROR:
        raise RuntimeError('Final compile error: ' + path)
target = root / 'docs/agent/EVIDENCE/G1_player_build.json'
target.write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report))
