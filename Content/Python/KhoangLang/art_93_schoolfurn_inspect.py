"""Khoang Lang 02:17 - inspect the classroom before furniture is placed.

Nothing is modified. This dumps the real actor census of
/Game/KhoangLang/Maps/Lvl_KL_School3 so the furniture layout is designed against
what is actually in the level rather than against the numbers in
build_30_level.py, which may have drifted.

Reports
-------
  * every actor: label, class, location, mesh name, world-space bounds
  * the four gameplay interactables and where their components live
  * the floor height actually used inside the classroom
  * PlayerStart, lights, game mode

Run:  run_ue_script.ps1 -Script art_93_schoolfurn_inspect.py
"""

import os
import sys
import traceback

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import kl_core as K  # noqa: E402
from editor_toolset.toolsets import actor as ACT  # noqa: E402

MAP = K.ROOT + '/Maps/Lvl_KL_School3'
OUT = os.path.join(HERE, 'art_93_schoolfurn_inspect.report.txt')
LINES = []


def log(m):
    line = str(m)
    LINES.append(line)
    unreal.log('INS: ' + line)


def world_bounds(actor):
    try:
        for c in ACT.ActorTools.get_components(actor):
            if 'StaticMesh' in c.get_class().get_name():
                sm = c.get_editor_property('static_mesh')
                if sm is None:
                    return None
                b = sm.get_bounds()
                sc = actor.get_actor_scale3d()
                return dict(
                    mesh=sm.get_name(),
                    half=[round(b.box_extent.x * sc.x, 1),
                          round(b.box_extent.y * sc.y, 1),
                          round(b.box_extent.z * sc.z, 1)],
                    local_min=[round(b.origin.x - b.box_extent.x, 1),
                               round(b.origin.y - b.box_extent.y, 1),
                               round(b.origin.z - b.box_extent.z, 1)])
    except Exception as exc:
        return dict(error=str(exc)[:80])
    return None


def main():
    log('=== art_93_schoolfurn_inspect ===')
    if not unreal.EditorLevelLibrary.load_level(MAP):
        log('could not load %s' % MAP)
        return
    world = unreal.EditorLevelLibrary.get_editor_world()
    actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    log('total actors: %d' % len(actors))

    rows = []
    interactables = []
    floors = []
    for a in actors:
        label = str(ACT.ActorTools.get_label(a))
        cls = a.get_class().get_name()
        loc = a.get_actor_location()
        comps = [c.get_class().get_name() for c in ACT.ActorTools.get_components(a)]
        b = world_bounds(a)
        row = dict(label=label, cls=cls,
                   loc=[round(loc.x, 1), round(loc.y, 1), round(loc.z, 1)],
                   comps=comps, bounds=b)
        rows.append(row)
        if 'Interact' in ' '.join(comps) or 'KL_Interact' in label:
            flags = {}
            for c in ACT.ActorTools.get_components(a):
                if 'Interact' in c.get_class().get_name():
                    for prop in ('PromptText', 'bTapeMode', 'bCornerMode',
                                 'bNoteMode'):
                        try:
                            flags[prop] = str(c.get_editor_property(prop))
                        except Exception:
                            pass
            interactables.append((label, row, flags))
        if label.startswith('KL_') and b and 'Floor' in label:
            floors.append((label, row))
        if label.startswith('KL_') and b and 'Ground' in label:
            floors.append((label, row))

    log('--- actors with labels, sorted by label ---')
    for r in sorted(rows, key=lambda r: r['label']):
        b = r['bounds'] or {}
        extra = ''
        if 'mesh' in b:
            extra = ' mesh=%s half=%s min=%s' % (b['mesh'], b['half'],
                                                 b['local_min'])
        elif 'error' in b:
            extra = ' bounds_err=%s' % b['error']
        log('%-28s %-34s loc=%s%s' % (r['label'], r['cls'], r['loc'], extra))

    log('--- floor candidates ---')
    for label, r in floors:
        log('%-28s loc=%s bounds=%s' % (label, r['loc'], r['bounds']))

    log('--- gameplay interactables ---')
    for label, r, flags in interactables:
        log('%-28s loc=%s flags=%s' % (label, r['loc'], flags))

    ps = [r for r in rows if r['cls'] == 'PlayerStart']
    log('--- PlayerStart --- %s' % ([p['loc'] for p in ps],))

    lights = [r for r in rows if 'Light' in r['cls']]
    log('--- lights: %d --- %s' % (len(lights), [l['label'] for l in lights]))

    try:
        ws = world.get_world_settings()
        log('default_game_mode=%s kill_z=%s'
            % (ws.get_editor_property('default_game_mode'),
               ws.get_editor_property('kill_z')))
    except Exception as exc:
        log('world settings: %r' % (exc,))

    # blueprint compile status for the props that carry the gameplay
    eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    for bp_path in (K.F_PROPS + '/BP_KL_Prop_AttBook',
                    K.F_PROPS + '/BP_KL_Prop_Roster',
                    K.F_PROPS + '/BP_KL_Prop_TapeDeck',
                    K.F_PROPS + '/BP_KL_Prop_Corner'):
        bp = eas.load_asset(bp_path)
        if bp is None:
            log('BP MISSING %s' % bp_path)
            continue
        try:
            log('BP %-46s status=%s' % (bp_path,
                                        bp.get_editor_property('status')))
        except Exception as exc:
            log('BP %s status: %r' % (bp_path, str(exc)[:80]))

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(LINES) + '\n')
    log('report written to %s' % OUT)
    log('=== done ===')


try:
    main()
except Exception:
    log(traceback.format_exc())
