"""Check the production school in real PIE with debug calls and world timers.

This is engineering verification, not a player playtest or canonical ending.
Requires a fresh production PIE. The callback never blocks the Unreal thread.
"""

import json
from pathlib import Path
import traceback
import unreal

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
if world is None or '/Production/' not in world.get_path_name():
    raise RuntimeError('A fresh production-school PIE is required')
pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
if pawn is None:
    raise RuntimeError('Production pawn did not spawn')

folder = '/Game/KhoangLang/Production/Blueprints/Core/'

def component(actor, name):
    path = folder + name + '.' + name + '_C'
    return actor.get_component_by_class(unreal.load_class(None, path))

inv = component(pawn, 'BP_KL_InvestigationComponent')
lis = component(pawn, 'BP_KL_ListeningComponent')
actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
props = {a.get_class().get_name(): a for a in actors if 'BP_KL_Prop_' in a.get_class().get_name()}
book = component(props['BP_KL_Prop_AttBook_C'], 'BP_KL_InteractComponent')
tape = component(props['BP_KL_Prop_TapeDeck_C'], 'BP_KL_InteractComponent')
corner = component(props['BP_KL_Prop_Corner_C'], 'BP_KL_InteractComponent')
report = {'world': world.get_path_name(), 'method': 'Blueprint debug calls; real world timers',
          'status': 'running', 'checks': [], 'phases': []}
target = Path(unreal.Paths.project_dir()) / 'docs/agent/EVIDENCE/G1_runtime_trial.json'
state = {'phase': 0, 'at': unreal.GameplayStatics.get_time_seconds(world), 'handle': None}

def save():
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')

def check(condition, name):
    report['checks'].append({'name': name, 'pass': bool(condition)})
    if not condition:
        raise AssertionError(name)

def call(obj, name, *params):
    obj.call_method(name, params)

def flag(name):
    return bool(inv.get_editor_property(name))

def phase(number):
    state['phase'] = number
    state['at'] = unreal.GameplayStatics.get_time_seconds(world)
    report['phases'].append({'phase': number, 'game_time': state['at']})
    save()

def stop(status):
    report['status'] = status
    save()
    unreal.unregister_slate_post_tick_callback(state['handle'])

def tick(delta):
    try:
        now = unreal.GameplayStatics.get_time_seconds(world)
        elapsed = now - state['at']
        if state['phase'] == 0:
            check(all((inv, lis, book, tape, corner)), 'Production components exist')
            check(lis.get_editor_property('bStarted'), 'BeginPlay initialized listening')
            check(not flag('bHasDoc') and not flag('bHasTape'), 'Fresh investigation')
            check(book.call_method('GetPromptStr', ()) == str(book.get_editor_property('PromptText')),
                  'Uncollected book shows its interaction prompt')
            call(book, 'DoDocument')
            call(book, 'DoDocument')
            check(flag('bHasDoc'), 'Document acquired through prop method')
            check(len(inv.get_editor_property('Collected')) == 1, 'Document collection is idempotent')
            check(book.call_method('GetPromptStr', ()) == str(book.get_editor_property('MsgConsumed')),
                  'Collected book shows consumed prompt')
            call(tape, 'DoTape')
            check(flag('bHasTape'), 'Masked tape acquired through prop method')
            call(inv, 'ToggleJournal')
            check(not flag('bCorroborated'), 'Journal does not bypass listening')
            call(inv, 'ToggleJournal')
            call(lis, 'SetFilter', True)
            call(tape, 'SetFilterMode', True)
            check(tape.get_editor_property('bPlayingClear'), 'Clear tape timer armed')
            phase(1)
        elif state['phase'] == 1 and elapsed >= 4:
            check(not flag('bTapeHeard'), 'Four seconds is insufficient')
            call(lis, 'SetFilter', False)
            call(tape, 'SetFilterMode', False)
            check(not tape.get_editor_property('bPlayingClear'), 'Changing mode cancels clear timer')
            phase(2)
        elif state['phase'] == 2 and elapsed >= 17:
            check(not flag('bTapeHeard'), 'Cancelled timer cannot complete evidence')
            call(lis, 'SetFilter', True)
            call(tape, 'SetFilterMode', True)
            phase(3)
        elif state['phase'] == 3 and elapsed >= 17:
            check(flag('bTapeHeard'), 'Full clear playback completes listening')
            call(inv, 'ToggleJournal')
            check(flag('bCorroborated'), 'Complete evidence unlocks corroboration')
            call(inv, 'ToggleJournal')
            call(corner, 'SetFocused', True, True, True, True, True)
            call(corner, 'DoCorner')
            check(flag('bBeatDone'), 'Ready corner starts prototype beat')
            phase(4)
        elif state['phase'] == 4 and elapsed >= 17:
            check(flag('bEnded'), 'World timers finish prototype beat')
            report['scope_limit'] = 'Prototype beat only; no canonical ending, save/load or player-input proof'
            unreal.SystemLibrary.execute_console_command(world, 'Shot showui')
            stop('passed')
        elif elapsed > 60:
            raise TimeoutError('Phase did not advance')
    except Exception:
        report['error'] = traceback.format_exc()
        stop('failed')

save()
state['handle'] = unreal.register_slate_post_tick_callback(tick)
print('Real PIE trial registered; inspect G1_runtime_trial.json for completion')
