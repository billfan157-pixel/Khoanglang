"""Copy Art architecture, adopt staged Blender furniture and production gameplay.

Only writes the production namespace. Source worlds and shared meshes remain
unchanged. Run with PIE stopped after extracting placement intents.
"""
import gc
import importlib
import json
from pathlib import Path
import sys
import unreal

ROOT = Path(unreal.Paths.project_dir())
sys.path.insert(0, str(ROOT / 'tools'))
import g1_build_runtime as production
importlib.reload(production)
K, build = production.K, production.build
from editor_toolset.toolsets.actor import ActorTools

MAP = '/Game/KhoangLang/Production/Maps/Lvl_KL_School3_Merged'
SOURCE = '/Game/KhoangLang/Maps/Lvl_KL_School3_Art'
SETS = [('A',780,555,-2.5,503,-2.5), ('B',1010,555,1.5,503,1.5),
        ('C',1240,555,-1,503,-1), ('D',786,695,3.5,643,9),
        ('E',1007,695,-2,647,-6), ('F',1248,692,5,None,None),
        ('G',770,330,-6,278,2)]

def main():
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if editor.get_game_world():
        raise RuntimeError('Stop PIE before merging')
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    gc.collect()
    unreal.EditorAssetLibrary.make_directory('/Game/KhoangLang/Production/Maps')
    if unreal.EditorAssetLibrary.does_asset_exist(MAP):
        raise RuntimeError('Merged map already exists; use a targeted repair')

    classes = {}
    for suffix in ('AttBook', 'Roster', 'TapeDeck', 'Corner'):
        name = 'BP_KL_Prop_ART_' + suffix
        old_path = '/Game/KhoangLang/Blueprints/Core/PropsArt/' + name
        path = K.F_CORE + '/PropsArt/' + name
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            raise RuntimeError('Production art prop already exists: ' + path)
        source = unreal.load_asset(old_path)
        old = [c for c in K.cdo_components(source)
               if c.get_class().get_name() == 'BP_KL_InteractComponent_C'][0]
        values = {p: old.get_editor_property(p) for p in
                  (*build.INT_BOOL, *build.INT_TEXT, *build.INT_SOUNDS, *build.INT_FLOAT, 'PromptText')}
        bp = unreal.EditorAssetLibrary.duplicate_asset(old_path, path)
        if bp is None:
            raise RuntimeError('Prop copy failed: ' + path)
        for c in list(K.cdo_components(bp)):
            if c.get_class().get_name() == 'BP_KL_InteractComponent_C':
                ActorTools.remove_component(c)
        comp = K.add_comp(bp, build.INT, 'KL_ProductionInteraction')
        for p, v in values.items():
            comp.set_editor_property(p, v)
        if suffix == 'Corner':
            for c in K.cdo_components(bp):
                if isinstance(c, unreal.StaticMeshComponent):
                    c.set_editor_property('visible', True)
                    c.set_editor_property('hidden_in_game', True)
        build.BPT.compile_blueprint(bp)
        if bp.get_editor_property('status') == unreal.BlueprintStatus.BS_ERROR or not K.save(path):
            raise RuntimeError('Prop compile/save failed: ' + path)
        classes[old_path + '.' + name + '_C'] = K.bp_class(path)

    # World duplication through EditorAssetLibrary previously crashed this UE
    # version. The native template-level path was verified on the G1 copy.
    source = old = bp = comp = c = None
    gc.collect()
    if not level.new_level_from_template(MAP, SOURCE):
        raise RuntimeError('Could not create merged level')
    labels = {a.get_actor_label(): a for a in actors.get_all_level_actors()}
    intents = json.loads((ROOT / 'docs/agent/EVIDENCE/G1_school_placement_intents.json').read_text())
    report = dict(map=MAP, architecture=SOURCE, rotation_repairs=[], removed=[], furniture=[], props=[], lights=[])
    for placement in intents['placements'] + intents['lights']:
        a = labels[placement['label']]
        p, y, r = placement['rotation']
        prior = a.get_actor_rotation()
        if max(abs(prior.pitch-p), abs(prior.yaw-y), abs(prior.roll-r)) > .01:
            report['rotation_repairs'].append(placement['label'])
        a.set_actor_rotation(unreal.Rotator(pitch=p, yaw=y, roll=r), False)
    for setting in intents['lights']:
        a = labels[setting['label']]
        c = a.get_component_by_class(unreal.LightComponent)
        r, g, b = [round(v * 255) for v in setting['rgb']]
        c.set_editor_property('light_color', unreal.Color(r=r, g=g, b=b, a=255))
        c.set_editor_property('intensity', setting['intensity'])
        c.set_editor_property('cast_shadows', setting['shadows'])
        report['lights'].append(dict(label=setting['label'], color=str(c.get_editor_property('light_color'))))

    # Remove only the old pupil rows and unsupported loose chairs in this copy.
    # Teacher furniture, stacked furniture and all architecture are retained.
    for name, a in list(labels.items()):
        if (name.startswith(('ART_Desk', 'ART_Bench')) and '_' in name[9:]) or name in (
                'ART_Chair_700', 'ART_Chair_1060', 'ART_Chair_1240', 'ART_Chair_Fallen'):
            if not actors.destroy_actor(a):
                raise RuntimeError('Could not remove copied placeholder: ' + name)
            report['removed'].append(name)
    for tag, x, y, yaw, by, byaw in SETS:
        for kind, fy, angle in [('Desk', y, yaw), ('Bench', by, byaw)]:
            if fy is None:
                continue
            mesh_path = '/Game/KhoangLang/Meshes/SchoolFurniture/SM_KL_School%s_A' % kind
            mesh = unreal.load_asset(mesh_path)
            if mesh is None:
                raise RuntimeError('Missing adopted furniture: ' + mesh_path)
            a = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x,fy,0),
                unreal.Rotator(pitch=0,yaw=angle,roll=0))
            name = 'SF_' + kind + '_' + tag
            a.set_actor_label(name)
            c = a.get_component_by_class(unreal.StaticMeshComponent)
            c.set_static_mesh(mesh)
            c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
            c.set_editor_property('cast_shadow', kind == 'Desk')
            c.set_editor_property('can_ever_affect_navigation', False)
            report['furniture'].append(name)
    for old in list(actors.get_all_level_actors()):
        cls = classes.get(old.get_class().get_path_name())
        if cls is None:
            continue
        name = old.get_actor_label()
        a = actors.spawn_actor_from_class(cls, old.get_actor_location(), unreal.Rotator())
        a.set_actor_label(name)
        if name == 'ART_AttBook':
            # Teacher desktop top is 89 cm (14 cm platform + 75 cm desk).
            a.set_actor_location(unreal.Vector(1050,810,90), False, False)
        actors.destroy_actor(old)
        report['props'].append(name)
    labels['ART_PlayerStart'].set_actor_location(unreal.Vector(-880,0,110), False, False)
    world = editor.get_editor_world()
    world.get_world_settings().set_editor_property('default_game_mode', K.bp_class(build.GM))
    if not level.save_current_level():
        raise RuntimeError('Merged map save failed')
    report['actor_count'] = len(actors.get_all_level_actors())
    (ROOT / 'docs/agent/EVIDENCE/G1_school_merge.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))

main()
