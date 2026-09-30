"""Inspect the isolated school in real PIE and capture the actual viewport."""
import json
from pathlib import Path
import unreal

world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
if world is None or '/G1Canon/' not in world.get_path_name():
    raise RuntimeError('Canonical school PIE required')
loop=unreal.GameplayStatics.get_actor_of_class(world,unreal.load_class(None,
    '/Game/KhoangLang/Production/G1Canon/BP_KL_SchoolLoop.BP_KL_SchoolLoop_C'))
pawn=unreal.GameplayStatics.get_player_pawn(world,0)
if loop is None or pawn is None:
    raise RuntimeError('Loop or possessed pawn missing')
report={'world':world.get_path_name(),'game_time':unreal.GameplayStatics.get_time_seconds(world),
        'pawn':pawn.get_class().get_path_name(),'state':{},'refs':{},'actors':[]}
for name in ('bInitialised','bEcho','bNotebook','bLamWitness','bLedger','bObserved',
             'bWorkingAvailable','bRawRetained','bSealing','bDossier','bFalseSpace',
             'Attention','Tier','EntityState','LamState','RollTime','LossCount',
             'Caption','Message','Candidate','SealProgress'):
    report['state'][name]=loop.get_editor_property(name)
for name in ('LamActor','NotebookActor','LedgerActor','ListenActor','ExitActor',
             'TeacherActor','ChildActor','FalseGeometryActor','RollAudioRef','AmbienceAudioRef'):
    value=loop.get_editor_property(name)
    report['refs'][name]=value.get_path_name() if value else None
for actor in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor):
    tags=actor.get_editor_property('tags')
    if any(str(t).startswith('KL_') for t in tags):
        loc=actor.get_actor_location()
        scale=actor.get_actor_scale3d()
        report['actors'].append({'tags':[str(t) for t in tags],
            'position':[loc.x,loc.y,loc.z],'scale':[scale.x,scale.y,scale.z],
            'hidden':actor.get_editor_property('hidden'),'class':actor.get_class().get_path_name()})
target=Path(unreal.Paths.project_dir())/'docs/agent/EVIDENCE/G1_school_snapshot.json'
target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
unreal.SystemLibrary.execute_console_command(world,'Shot')
print(json.dumps(report,ensure_ascii=False))
