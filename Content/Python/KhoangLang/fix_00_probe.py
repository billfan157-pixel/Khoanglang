"""fix_00 - diagnose the missing WASD movement in the school prototype.

Read-mostly probe.  Reports:
  A. project maps
  B. BP_FirstPersonCharacter graphs / EventGraph nodes / DSL
  C. a pristine copy of the engine template character (reference wiring)
  D. whether the toolset can recreate an EnhancedInputAction event node
  E. BP_FirstPersonPlayerController (IMC registration)
  F. IMC_Default / IMC_MouseLook mappings + IA_* value types
  G. game mode / pawn class / level + PlayerStart clearance

Writes C:\\Users\\phanb\\AppData\\Local\\Temp\\opencode\\kl\\fix00\\r.txt
"""

import os

import unreal

from editor_toolset.toolsets import blueprint as BP
from editor_toolset.toolsets.blueprint import _get_node_type_id
from editor_toolset.toolsets import actor as ACT

BPT = BP.BlueprintTools
eas = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)

R = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\fix00'
os.makedirs(R, exist_ok=True)
REP = os.path.join(R, 'r.txt')
if os.path.exists(REP):
    os.remove(REP)

CHAR = '/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter'
PC = '/Game/FirstPerson/Blueprints/BP_FirstPersonPlayerController'
GM_TPL = '/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode'
GM_KL = '/Game/KhoangLang/Blueprints/Player/BP_KL_GameMode'
MAP = '/Game/KhoangLang/Maps/Lvl_KL_School3'
REF_FILE = (r'C:\Program Files\Epic Games\UE_5.8\Templates\TP_FirstPersonBP'
            r'\Content\FirstPerson\Blueprints\BP_FirstPersonCharacter.uasset')
REF_DEST = (r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217'
            r'\Content\KhoangLang\Data\TMP_FIX_RefChar.uasset')
REF_ASSET = '/Game/KhoangLang/Data/TMP_FIX_RefChar'


def p(msg):
    line = str(msg)
    unreal.log('FIX00: ' + line)
    with open(REP, 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


def pins(node):
    ni = BPT.get_node_infos([node])[0]
    ins = ', '.join('%s:%s%s' % (x.name, x.type_id,
                                 '[x]' if x.connected_pins else '')
                    for x in ni.input_pins)
    outs = ', '.join('%s:%s%s' % (x.name, x.type_id,
                                  '[x]' if x.connected_pins else '')
                     for x in ni.output_pins)
    return 'IN [%s] OUT [%s]' % (ins, outs)


def section(name):
    p('')
    p('=' * 70)
    p('=== %s' % name)


def dump_graph(bp, label, dsl=True, node_limit=80, skip_pins=False):
    p('--- graphs of %s (%s)' % (label, bp.get_name()))
    for g in BPT.list_graphs(bp):
        ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
        p('    graph %-26s nodes=%d' % (g.get_name(), len(ed.list_all_nodes())))
    for g in BPT.list_graphs(bp):
        ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
        nodes = ed.list_all_nodes()
        p('  == %s :: %s (%d nodes)' % (label, g.get_name(), len(nodes)))
        for n in nodes[:node_limit]:
            try:
                tid = _get_node_type_id(n)
            except Exception as exc:
                tid = 'ERR:%r' % (exc,)
            try:
                tit = n.get_node_title()
            except Exception:
                tit = ''
            p('     %-38s %-50s %s' % (n.get_class().get_name(), tid, tit))
            if skip_pins:
                continue
            try:
                p('         %s' % pins(n))
            except Exception as exc:
                p('         pins failed %r' % (exc,))
        if len(nodes) > node_limit:
            p('     ... %d more nodes' % (len(nodes) - node_limit))
        if dsl:
            try:
                txt = str(BPT.read_graph_dsl(g))
            except Exception as exc:
                txt = 'read_graph_dsl failed: %r' % (exc,)
            p('  -- dsl %s :: %s' % (label, g.get_name()))
            for ln in txt.splitlines():
                p('   | ' + ln)


def main():
    section('A. maps')
    for folder in ('/Game/KhoangLang/Maps', '/Game/KhoangLang/ArtTest'):
        try:
            p('  %-32s %s' % (folder, eas.list_assets(folder, recursive=True)))
        except Exception as exc:
            p('  %-32s list failed %r' % (folder, exc))

    section('B. BP_FirstPersonCharacter')
    ch = unreal.load_asset(CHAR)
    p('  asset=%s status=%s' % (ch, ch.get_editor_property('status')))
    dump_graph(ch, 'Character')
    try:
        p('  list_events -> %s'
          % (unreal.BlueprintEditorLibrary.list_events(ch),))
    except Exception as exc:
        p('  list_events failed %r' % (exc,))
    try:
        gc = unreal.load_class(
            None, CHAR + '.' + CHAR.rsplit('/', 1)[-1] + '_C')
        p('  generated class: %r' % (gc,))
        names = []
        try:
            names = [f for f in dir(gc) if 'nput' in f or 'Move' in f
                     or 'Aim' in f or 'Jump' in f]
        except Exception:
            pass
        p('  python-visible members matching input/move/aim/jump: %s' % (names,))
        p('  list_functions -> %s'
          % (BPT.list_functions(ch) if hasattr(BPT, 'list_functions') else None,))
    except Exception as exc:
        p('  generated class lookup failed %r' % (exc,))

    section('C. pristine engine template character (reference wiring)')
    ref = None
    try:
        if not os.path.exists(REF_FILE):
            p('  reference file missing: %s' % REF_FILE)
        else:
            if os.path.exists(REF_DEST):
                os.remove(REF_DEST)
            with open(REF_FILE, 'rb') as src:
                data = src.read()
            with open(REF_DEST, 'wb') as dst:
                dst.write(data)
            p('  copied %d bytes -> %s' % (len(data), REF_DEST))
            ref = unreal.load_asset(REF_ASSET)
            p('  loaded reference asset: %r' % (ref,))
            if ref is not None:
                dump_graph(ref, 'REF')
    except Exception as exc:
        p('  reference dump failed %r' % (exc,))

    section('D. can the toolset create an EnhancedInputAction node?')
    target = ref if ref is not None else ch
    g = unreal.BlueprintEditorLibrary.find_event_graph(target)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
    p('  target graph = %s (%d nodes)' % (g.get_name(),
                                          len(ed.list_all_nodes())))
    cands = ['Input|EnhancedActionEvents|EnhancedInputActionIA_Move',
             'Input|EnhancedActionEvents|EnhancedInputActionIA_Look',
             'Input|EnhancedActionEvents|EnhancedInputActionIA_MouseLook',
             'Input|EnhancedActionEvents|EnhancedInputActionIA_Jump',
             'EnhancedInputActionIA_Move',
             'Input|EnhancedActionEvents|IA_Move',
             'Input|IA_Move', 'InputActions|IA_Move']
    for cid in cands:
        try:
            n = ed.create_node_from_name(cid, unreal.Vector2D(0, 0), [], None)
        except Exception as exc:
            p('  %-58s raised %r' % (cid, exc))
            continue
        if n is None:
            p('  %-58s -> None' % cid)
            continue
        p('  %-58s -> %s id=%r' % (cid, n.get_class().get_name(),
                                   _get_node_type_id(n)))
        try:
            p('        %s' % pins(n))
        except Exception as exc:
            p('        pins failed %r' % (exc,))
        for prop in ('input_action', 'InputAction'):
            try:
                p('        %s = %r' % (prop, n.get_editor_property(prop)))
            except Exception as exc:
                p('        %s unreadable (%s)' % (prop, str(exc)[:60]))
        try:
            ed.remove_nodes([n])
        except Exception as exc:
            p('        remove failed %r' % (exc,))
    for pat in ('EnhancedInputAction', 'IA_'):
        try:
            p('  find_node_types(%r) -> %s'
              % (pat, BPT.find_node_types(g, pat)[:12]))
        except Exception as exc:
            p('  find_node_types(%r) failed %r' % (pat, exc))

    if ref is not None:
        try:
            eas.delete_asset(REF_ASSET)
            p('  reference asset deleted')
        except Exception as exc:
            p('  reference delete failed %r' % (exc,))

    section('E. BP_FirstPersonPlayerController')
    pc = unreal.load_asset(PC)
    p('  asset=%s status=%s' % (pc, pc.get_editor_property('status')))
    dump_graph(pc, 'PlayerController')

    section('F. input mapping contexts')
    for path in ('/Game/Input/IMC_Default', '/Game/Input/IMC_MouseLook'):
        imc = unreal.load_asset(path)
        p('  %s -> %r' % (path, imc))
        if imc is None:
            continue
        try:
            maps = imc.get_editor_property('mappings')
        except Exception as exc:
            p('    mappings unreadable %r' % (exc,))
            continue
        p('    %d mappings' % len(maps))
        for m in maps:
            act = m.get_editor_property('action') if hasattr(
                m, 'get_editor_property') else None
            key = m.get_editor_property('key') if hasattr(
                m, 'get_editor_property') else None
            kname = '?'
            try:
                kname = key.get_editor_property('key_name')
            except Exception:
                kname = str(key)
            p('      %-16s <- %s' % (act.get_name() if act else '?', kname))
    for path in ('/Game/Input/IA_Move', '/Game/Input/IA_Look',
                 '/Game/Input/IA_MouseLook', '/Game/Input/IA_Jump',
                 '/Game/Input/IA_Shoot'):
        ia = unreal.load_asset(path)
        if ia is None:
            p('  %s MISSING' % path)
            continue
        try:
            p('  %-30s value_type=%s triggers=%s modifiers=%s'
              % (path, ia.get_editor_property('value_type'),
                 ia.get_editor_property('triggers'),
                 ia.get_editor_property('modifiers')))
        except Exception as exc:
            p('  %-30s props failed %r' % (path, exc))

    section('G. game mode / pawn / level')
    for path in (GM_TPL, GM_KL):
        gm = unreal.load_asset(path)
        p('  %s -> %r' % (path, gm))
        if gm is None:
            continue
        try:
            p('     parent = %s' % (unreal.BlueprintEditorLibrary
                                    .get_blueprint_parent_class(gm),))
        except Exception as exc:
            p('     parent failed %r' % (exc,))
        try:
            cdo = BPT.get_default_object(gm)
            for prop in ('default_pawn_class', 'player_controller_class',
                         'hud_class', 'game_state_class'):
                try:
                    val = cdo.get_editor_property(prop)
                    p('     %-24s = %s'
                      % (prop, val.get_name() if val else None))
                except Exception as exc:
                    p('     %-24s unreadable %r' % (prop, exc))
        except Exception as exc:
            p('     cdo failed %r' % (exc,))

    try:
        ok = unreal.EditorLevelLibrary.load_level(MAP)
        p('  load_level(%s) -> %s' % (MAP, ok))
        world = unreal.EditorLevelLibrary.get_editor_world()
        p('  world = %s type=%s' % (world.get_name(), world.get_world_type()))
        ws = world.get_world_settings()
        gm = ws.get_editor_property('default_game_mode')
        p('  world settings default_game_mode = %s'
          % (gm.get_name() if gm else None))
        starts = unreal.GameplayStatics.get_all_actors_of_class(
            world, unreal.PlayerStart)
        p('  PlayerStart count = %d' % len(starts))
        meshes = unreal.GameplayStatics.get_all_actors_of_class(
            world, unreal.StaticMeshActor)
        for s in starts:
            loc = s.get_actor_location()
            rot = s.get_actor_rotation()
            p('    %s at (%.0f, %.0f, %.0f) yaw=%.0f'
              % (s.get_actor_label(), loc.x, loc.y, loc.z, rot.yaw))
            for a in meshes:
                try:
                    origin, extent = a.get_actor_bounds(False)
                except Exception:
                    continue
                d = origin - loc
                if (abs(d.x) < extent.x + 60.0 and
                        abs(d.y) < extent.y + 60.0 and
                        abs(d.z) < extent.z + 190.0):
                    p('      nearby mesh: %-26s extent(%.0f,%.0f,%.0f)'
                      % (a.get_actor_label(), extent.x, extent.y, extent.z))
        p('  total actors = %d' % len(unreal.GameplayStatics
                                      .get_all_actors_of_class(
                                          world, unreal.Actor)))
    except Exception as exc:
        p('  level checks failed %r' % (exc,))

    p('')
    p('FIX00_DONE')


try:
    main()
except Exception:
    import traceback
    p(traceback.format_exc())
    p('FIX00_FAILED')
