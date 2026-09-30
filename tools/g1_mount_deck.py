"""Give the G1 cassette a source-authored shelf and face it into the hall.

Only new G1 mesh/actor assets are written. PIE must be stopped. Run AFTER
g1_repair_school_meshes.py succeeds: a repaired deck is required, not implied.
No BuildFromDescriptions call is permitted on an existing rendered asset.
"""
import hashlib
import json
from pathlib import Path
import sys
import unreal

ROOT = Path(unreal.Paths.project_dir())
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'Content/Python/KhoangLang'))
import g1_repair_school_meshes as repair
import kl_mesh as M

BASE = '/Game/KhoangLang/Production/G1Canon'
MAP = BASE + '/Lvl_KL_SchoolSlice'
FOLDER = BASE + '/Meshes'
ASSET = FOLDER + '/SM_KL_G1_DeckShelf_V1'
OWNER = 'G1DeckShelfV1'
WOOD = BASE + '/Materials/MI_ART_WoodDark'
METAL = BASE + '/Materials/MI_ART_Metal'
REPORT = ROOT / 'docs/agent/EVIDENCE/G1_deck_mount.json'


def box(builder, slot, x0, y0, z0, x1, y1, z1):
    """Six faces with consistent rectangular UVs; dimensions are cm."""
    builder.quad(slot, (x0,y0,z0), (x1,y0,z0), (x1,y0,z1), (x0,y0,z1))
    builder.quad(slot, (x1,y1,z0), (x0,y1,z0), (x0,y1,z1), (x1,y1,z1))
    builder.quad(slot, (x0,y1,z0), (x0,y0,z0), (x0,y0,z1), (x0,y1,z1))
    builder.quad(slot, (x1,y0,z0), (x1,y1,z0), (x1,y1,z1), (x1,y0,z1))
    builder.quad(slot, (x0,y1,z1), (x0,y0,z1), (x1,y0,z1), (x1,y1,z1))
    builder.quad(slot, (x0,y0,z0), (x0,y1,z0), (x1,y1,z0), (x1,y0,z0))


def create_shelf():
    existing = unreal.load_asset(ASSET)
    if existing is not None:
        if unreal.EditorAssetLibrary.get_metadata_tag(existing, 'G1MountOwner') != OWNER:
            raise RuntimeError('Existing shelf belongs to another author; preserve it')
        result = repair.bounds(existing)
        audit = repair.buffer_audit(existing)  # Read-only; no flag changes.
        body = existing.get_editor_property('body_setup')
        if (not result['finite'] or result['radius'] <= 0 or not audit['qualified']
                or body is None or body.get_editor_property('collision_trace_flag')
                != unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE):
            raise RuntimeError('Existing shelf fails audit; preserve it and author a new version')
        return existing, {'action': 'REUSED_WITHOUT_REBUILD', 'bounds': result,
                          'buffer_audit': audit}
    materials = [unreal.load_asset(path) for path in (WOOD, METAL)]
    if any(material is None for material in materials):
        raise RuntimeError('Required copied wood/metal materials missing')
    unreal.EditorAssetLibrary.make_directory(FOLDER)
    mesh = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        'SM_KL_G1_DeckShelf_V1', FOLDER, unreal.StaticMesh, None)
    if mesh is None:
        raise RuntimeError('Fresh shelf mesh creation failed')
    unreal.EditorAssetLibrary.set_metadata_tag(mesh, 'G1MountOwner', OWNER)
    mesh.set_editor_property('allow_cpu_access', True)
    slots = [str(mesh.add_material(material)) for material in materials]
    builder = M.MeshBuilder(mesh.get_name())
    builder._sm = mesh
    builder._desc = mesh.create_static_mesh_description()
    # Coordinates local to shelf origin (1930,0,0). The top is exactly 122,
    # matching the corrected cassette body's zero-height base at world Z122.
    # Depth supports both the 34cm case and the intact rear cable to X1973.
    box(builder, slots[0], -45, -37, 118, 68, 37, 122)
    for y in (-29, 29):
        # L-bracket: vertical backplate meets the rear wall plane X1998;
        # horizontal arm touches plank underside Z118, without added geometry
        # across the cassette face or player evidence sight line.
        box(builder, slots[1], 64, y-2, 83, 68, y+2, 118)
        box(builder, slots[1], -37, y-2, 114, 64, y+2, 118)
        builder.tube(slots[1], -30, y, 114, 64, y, 87, 1.3, 8, 1)
    authored = repair.vertex_audit(builder._desc)
    triangles = repair.triangle_uv_audit(builder._desc)
    if triangles['degenerate_uv_count'] or triangles['degenerate_geometry_count']:
        raise RuntimeError('Authored shelf geometry or UVs are degenerate')
    description = repair.isolated_corner_description(builder._desc, mesh, slots)
    result = repair.regular_build(mesh, description)  # Fresh assets only.
    body = mesh.get_editor_property('body_setup')
    if body is None:
        raise RuntimeError('Native shelf build did not create a collision body')
    body.modify()
    body.set_editor_property('collision_trace_flag',
                             unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    body.set_editor_property('double_sided_geometry', True)
    audit = repair.buffer_audit(mesh)
    if not audit['qualified']:
        raise RuntimeError('Shelf rendered position/normal/tangent audit failed: '
                           + json.dumps(audit))
    if not unreal.EditorAssetLibrary.save_loaded_asset(mesh, False):
        raise RuntimeError('Shelf mesh save failed')
    return mesh, {'action': 'BUILT_FRESH', 'positions': authored,
                  'triangle_uv_audit': triangles, 'bounds': result,
                  'buffer_audit': audit}


def main():
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if editor.get_game_world():
        raise RuntimeError('Stop PIE before mounting cassette')
    world = editor.get_editor_world()
    if world is None or world.get_path_name().split('.')[0] != MAP:
        raise RuntimeError('Load isolated G1 school')
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    labels = {a.get_actor_label(): a for a in actors.get_all_level_actors()}
    deck = labels.get('G1_ListeningDeck')
    if deck is None:
        raise RuntimeError('Tagged cassette actor missing')
    deck_component = deck.get_component_by_class(unreal.StaticMeshComponent)
    deck_mesh = deck_component.get_editor_property('static_mesh')
    if (deck_mesh is None or not deck_mesh.get_path_name().startswith(FOLDER + '/')
            or '_Regular' not in deck_mesh.get_name()):
        raise RuntimeError('Complete repaired cassette integration before mounting')
    if not repair.bounds(deck_mesh)['finite'] or not repair.buffer_audit(deck_mesh)['qualified']:
        raise RuntimeError('Repaired cassette still fails native geometry audit')
    mesh, audit = create_shelf()
    shelf = labels.get('G1_DeckShelf')
    if shelf is None:
        shelf = actors.spawn_actor_from_class(unreal.StaticMeshActor,
                                               unreal.Vector(1930, 0, 0))
        shelf.set_actor_label('G1_DeckShelf')
        shelf.set_editor_property('tags', [unreal.Name(OWNER)])
    elif unreal.Name(OWNER) not in shelf.get_editor_property('tags'):
        raise RuntimeError('Existing named shelf is not owned; preserve it')
    world.modify()
    shelf.modify()
    shelf.set_actor_location(unreal.Vector(1930,0,0), False, False)
    shelf.set_actor_rotation(unreal.Rotator(pitch=0,yaw=0,roll=0), False)
    shelf.set_actor_scale3d(unreal.Vector(1,1,1))
    component = shelf.get_component_by_class(unreal.StaticMeshComponent)
    component.modify()
    component.set_static_mesh(mesh)
    component.set_mobility(unreal.ComponentMobility.MOVABLE)
    component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    component.set_collision_response_to_channel(unreal.CollisionChannel.ECC_VISIBILITY,
                                                unreal.CollisionResponseType.ECR_BLOCK)
    deck.modify()
    deck.set_actor_location(unreal.Vector(1930,0,122), False, False)
    deck.set_actor_rotation(unreal.Rotator(pitch=0,yaw=-90,roll=0), False)
    # Interaction tags, script reference, mesh materials and deck collision
    # are preserved. This is an owned fixture mount, not a new story fact.
    if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAP):
        raise RuntimeError('Mounted cassette map save failed')
    report = {'map': MAP, 'asset': ASSET, 'actor': shelf.get_actor_label(),
              'deck': deck.get_actor_label(), 'deck_position': [1930,0,122],
              'deck_yaw': -90, 'shelf_top_cm': 122, 'rear_wall_x': 1998,
              'geometry_audit': audit, 'interaction_retest_passed': False,
              'visual_accepted': False,
              'provenance': 'Project-authored shelf geometry and copied wood/metal',
              'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    REPORT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'shelf': ASSET, 'deck_yaw': -90,
                      'interaction_retest_passed': False}))


if __name__ == '__main__':
    main()
