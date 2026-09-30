"""Compile and inspect current production assets without saving user assets."""
import datetime
import json
from pathlib import Path
import sys
import unreal

root = Path(unreal.Paths.project_dir())
sys.path.insert(0, str(root / 'Content/Python/KhoangLang'))
from kl_core import BPT

sub = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
if sub.get_game_world():
    raise RuntimeError('Stop PIE before compilation')
world = sub.get_editor_world()
report = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'source_revision': '76fe591d59afc21d7838bf35cd9d17ad493f9899',
          'world': world.get_path_name(), 'blueprints': [], 'actors': [],
          'scope': 'Editor Blueprint compilation and inventory; not packaged build'}
base = '/Game/KhoangLang/Production/Blueprints/'
paths = [base + p for p in ('Core/BP_KL_InvestigationComponent',
    'Core/BP_KL_ListeningComponent', 'Core/BP_KL_InteractComponent',
    'Player/BP_KL_Character', 'Player/BP_KL_GameMode', 'UI/BP_KL_HUD')]
paths += unreal.EditorAssetLibrary.list_assets(base + 'Core/PropsArt', recursive=True)
for path in paths:
    bp = unreal.load_asset(path)
    if not isinstance(bp, unreal.Blueprint):
        continue
    BPT.compile_blueprint(bp, warnings_as_errors=False)
    errors = []
    for graph in BPT.list_graphs(bp):
        ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        for node in ed.list_all_nodes():
            if hasattr(node, 'has_error') and node.has_error():
                errors.append({'graph': graph.get_name(), 'error': node.error_msg()})
    report['blueprints'].append({'path': path, 'status': str(bp.get_editor_property('status')),
                                'errors': errors,
                                'node_diagnostics': 'Optional has_error API unavailable on some node classes; compile status checked'})
for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
    loc = actor.get_actor_location()
    report['actors'].append({'label': actor.get_actor_label(),
                            'class': actor.get_class().get_path_name(),
                            'location': [loc.x, loc.y, loc.z]})
gm = world.get_world_settings().get_editor_property('default_game_mode')
report['game_mode'] = gm.get_path_name() if gm else None
report['failed'] = [b['path'] for b in report['blueprints'] if b['errors'] or 'BS_ERROR' in b['status']]
target = root / 'docs/agent/EVIDENCE/G0_current_audit.json'
target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'world': report['world'], 'compiled': len(report['blueprints']),
                  'actors': len(report['actors']), 'failed': report['failed']}))
if report['failed']:
    raise RuntimeError('Production compile failed')
