"""Report actual blocking hits at the primary entrance."""
import json
from pathlib import Path
import unreal
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pawn=unreal.GameplayStatics.get_player_pawn(world,0)
report=[]
def describe(hit):
    if not hit: return None
    data=hit.to_tuple()
    return dict(actor=data[9].get_actor_label() if data[9] else None,
        component=data[10].get_name() if data[10] else None,hit=str(hit))
for z in (25,70,110,180,215):
    hit=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(-600,0,z),unreal.Vector(0,0,z),
        unreal.TraceTypeQuery.ECC_VISIBILITY,False,[pawn],unreal.DrawDebugTrace.NONE,True)
    report.append(dict(z=z,result=describe(hit)))
hit=unreal.SystemLibrary.capsule_trace_single(world,unreal.Vector(-600,0,110),unreal.Vector(0,0,110),34,96,
    unreal.TraceTypeQuery.ECC_VISIBILITY,False,[pawn],unreal.DrawDebugTrace.NONE,True)
report.append(dict(capsule=describe(hit)))
for z in (25,70,110,180,215):
    hit=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(870,0,z),unreal.Vector(870,410,z),
        unreal.TraceTypeQuery.ECC_VISIBILITY,False,[pawn],unreal.DrawDebugTrace.NONE,True)
    report.append(dict(room_z=z,result=describe(hit)))
hit=unreal.SystemLibrary.capsule_trace_single(world,unreal.Vector(870,0,110),unreal.Vector(870,410,110),34,96,
    unreal.TraceTypeQuery.ECC_VISIBILITY,False,[pawn],unreal.DrawDebugTrace.NONE,True)
report.append(dict(room_capsule=describe(hit)))
(Path(unreal.Paths.project_dir())/'docs/agent/EVIDENCE/G1_primary_route_probe.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
