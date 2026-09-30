"""Khoang Lang 02:17 - Milestone 1 verification pass.

Loads the prototype level, checks the actor inventory, Blueprint compile
status, references and world settings, and writes a summary.
"""

import os
import sys

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import kl_core as K  # noqa: E402
from kl_core import BPT  # noqa: E402
from kl_core import step, ok, warn, fail  # noqa: E402
from editor_toolset.toolsets import actor as ACT  # noqa: E402

MAP = K.MAP_PATH

BLUEPRINTS = [
    K.F_DATA + '/BP_KL_EvidenceDef',
    K.F_CORE + '/BP_KL_InvestigationComponent',
    K.F_CORE + '/BP_KL_ListeningComponent',
    K.F_CORE + '/BP_KL_InteractComponent',
    K.F_CORE + '/Props/BP_KL_Prop_AttBook',
    K.F_CORE + '/Props/BP_KL_Prop_TapeDeck',
    K.F_CORE + '/Props/BP_KL_Prop_Roster',
    K.F_CORE + '/Props/BP_KL_Prop_Corner',
    K.F_UI + '/BP_KL_HUD',
    K.F_PLAYER + '/BP_KL_GameMode',
    K.BP_TPL_CHAR,
    K.BP_TPL_PC,
]


def check_blueprints():
    step('blueprint integrity')
    bad = 0
    for path in BLUEPRINTS:
        bp = unreal.load_asset(path)
        if bp is None:
            fail('missing blueprint %s' % path)
            bad += 1
            continue
        st = bp.get_editor_property('status')
        errs = []
        for g in BPT.list_graphs(bp):
            ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
            for n in ed.list_all_nodes():
                try:
                    if n.has_error():
                        errs.append('%s: %s' % (g.get_name(), n.error_msg()))
                except Exception:
                    pass
        if errs or 'UP_TO_DATE' not in str(st):
            fail('%s  status=%s  %s' % (path, st, errs[:4]))
            bad += 1
        else:
            ok('%-58s %s  graphs=%d' % (path, str(st).split('.')[-1],
                                         len(BPT.list_graphs(bp))))
    ok('blueprints checked: %d, problems: %d' % (len(BLUEPRINTS), bad))


def check_assets():
    step('asset references')
    doc = K.load(K.F_DATA + '/EVD_SoDiemDanh')
    tape = K.load(K.F_DATA + '/EVD_Bang021634')
    for a, want in ((doc, 'BP_KL_EvidenceDef_C'), (tape, 'BP_KL_EvidenceDef_C')):
        got = a.get_class().get_name()
        (ok if got == want else fail)('%s class=%s' % (a.get_name(), got))
    for name in ('S_KL_T2_Clear', 'S_KL_T2_Masked', 'S_KL_RollCall', 'S_KL_ChildReply',
                 'S_KL_Ambience_Hall', 'S_KL_NoiseMask', 'S_KL_ClarityTone',
                 'S_KL_SpeakerHum', 'S_KL_TapeDeck', 'S_KL_UI_Evidence',
                 'S_KL_UI_ModeShift', 'S_KL_UI_Interact'):
        if unreal.load_asset('%s/%s' % (K.F_AUDIO, name)) is None:
            fail('missing audio %s' % name)
    ok('audio: 12 expected, checked')
    for name in ('M_KL_WallUpper', 'M_KL_Floor', 'M_KL_Ceiling', 'M_KL_Desk',
                 'M_KL_Board', 'M_KL_Metal', 'M_KL_Wood', 'M_KL_Paper',
                 'M_KL_Figure', 'M_KL_Outside', 'M_KL_Wainscot'):
        if unreal.load_asset('%s/%s' % (K.F_MAT, name)) is None:
            fail('missing material %s' % name)
    ok('materials: 11 expected, checked')


def check_level():
    step('level inventory')
    if not unreal.EditorLevelLibrary.load_level(MAP):
        fail('load_level %s' % MAP)
        return
    world = unreal.EditorLevelLibrary.get_editor_world()
    ok('world = %s' % world.get_name())
    actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    ok('actor count = %d' % len(actors))
    by_class = {}
    for a in actors:
        by_class[a.get_class().get_name()] = by_class.get(a.get_class().get_name(), 0) + 1
    for k in sorted(by_class):
        ok('  %-34s %d' % (k, by_class[k]))

    starts = [a for a in actors if a.get_class().get_name() == 'PlayerStart']
    (ok if starts else fail)('PlayerStart: %d' % len(starts))
    if starts:
        loc = starts[0].get_actor_location()
        ok('  PlayerStart at %.0f %.0f %.0f' % (loc.x, loc.y, loc.z))

    wanted = ('BP_KL_Prop_AttBook_C', 'BP_KL_Prop_TapeDeck_C',
              'BP_KL_Prop_Roster_C', 'BP_KL_Prop_Corner_C')
    for w in wanted:
        hits = [a for a in actors if a.get_class().get_name() == w]
        if not hits:
            fail('no %s placed' % w)
        else:
            loc = hits[0].get_actor_location()
            ok('  %-24s at %.0f %.0f %.0f' % (w, loc.x, loc.y, loc.z))

    lights = [a for a in actors if 'Light' in a.get_class().get_name()]
    ok('lights = %d' % len(lights))
    if not lights:
        fail('no lights in the level - it will be black')

    ws = world.get_world_settings()
    gm = ws.get_editor_property('default_game_mode')
    (ok if gm and K.bp_class(K.F_PLAYER + '/BP_KL_GameMode') == gm
     else fail)('default_game_mode = %s' % (gm.get_name() if gm else None))

    # every placed interactable must carry the interact component
    for w in wanted:
        for a in actors:
            if a.get_class().get_name() != w:
                continue
            comps = [c.get_class().get_name() for c in ACT.ActorTools.get_components(a)]
            if not any('Interact' in c for c in comps):
                fail('%s has no interact component (%s)' % (w, comps))
            else:
                ok('  %s components: %s' % (w, ', '.join(comps)))


def check_props():
    step('prop defaults')
    for name in ('BP_KL_Prop_AttBook', 'BP_KL_Prop_TapeDeck',
                 'BP_KL_Prop_Roster', 'BP_KL_Prop_Corner'):
        bp = K.load('%s/Props/%s' % (K.F_CORE, name))
        cdo = BPT.get_default_object(bp)
        comps = [c for c in ACT.ActorTools.get_components(cdo)]
        ic = [c for c in comps if 'Interact' in c.get_class().get_name()]
        mesh = [c for c in comps if c.get_class().get_name() == 'StaticMeshComponent']
        if not ic or not mesh:
            fail('%s missing interact/mesh component' % name)
            continue
        ok('%-26s prompt=%r tape=%s corner=%s note=%s hidden0=%s mesh=%s' % (
            name, str(ic[0].get_editor_property('PromptText')),
            ic[0].get_editor_property('bTapeMode'),
            ic[0].get_editor_property('bCornerMode'),
            ic[0].get_editor_property('bNoteMode'),
            ic[0].get_editor_property('bHiddenAtStart'),
            mesh[0].get_editor_property('static_mesh').get_name()
            if mesh[0].get_editor_property('static_mesh') else None))


def check_validation():
    step('engine asset validation (level + project assets)')
    try:
        vs = unreal.get_editor_subsystem(unreal.EditorValidatorSubsystem)
    except Exception as exc:
        warn('EditorValidatorSubsystem unavailable: %r' % (exc,))
        return
    try:
        res = vs.validate_loaded_assets(True, True)
    except Exception as exc:
        try:
            res = vs.validate_loaded_assets()
        except Exception as exc2:
            warn('validate_loaded_assets raised: %r / %r' % (exc, exc2))
            return
    n = 0
    for r in res:
        asset = r.get_asset() if hasattr(r, 'get_asset') else None
        issues = r.get_issues() if hasattr(r, 'get_issues') else []
        if not issues:
            continue
        n += len(issues)
        for i in issues:
            try:
                p = '%s: %s' % (asset.get_path_name() if asset else '?', i)
            except Exception:
                p = str(i)
            if 'KhoangLang' in p or 'FirstPerson' in p:
                warn('validation: %s' % p)
    ok('validator reported %d issue(s) across the loaded assets' % n)


def check_graphs():
    """A clean compile is not proof that a graph has any wiring in it.

    Count the nodes in every graph this build owns: a hand-built graph that
    silently lost its nodes still reports BS_UP_TO_DATE.
    """
    step('graph wiring census')
    floors = {
        'BP_KL_InvestigationComponent': {
            'InitRun': 8, 'RefreshObjective': 8, 'CollectDoc': 6, 'CollectTape': 6,
            'ToggleJournal': 8, 'BeginBeat': 5, 'SetTapeHeard': 5, 'NoteRevealed': 5,
            'GetObjectiveStr': 3, 'GetDocTitleStr': 3, 'GetCorrob1Str': 3,
            'SetPromptFromString': 3, 'SetSubtitleFromString': 3, 'ClearPrompt': 2},
        'BP_KL_ListeningComponent': {'StartBeds': 22, 'SetFilter': 20,
                                     'GetModeStr': 3},
        'BP_KL_InteractComponent': {
            'SetFocused': 24, 'GetPromptStr': 7, 'IsAvailable': 2, 'IsFocused': 2,
            'DoDocument': 8, 'DoTape': 10, 'DoNote': 5, 'DoCorner': 20,
            'SetFilterMode': 5, 'DoInteract': 7, 'EventGraph': 6},
        'BP_FirstPersonCharacter': {'InitKL': 6, 'UpdateFocus': 25, 'PollKeys': 25,
                                    'CheckHeard': 6, 'TickKL': 3, 'EventGraph': 3},
        'BP_KL_HUD': {'EventGraph': 60},
    }
    for bpname, want in floors.items():
        bp = unreal.load_asset(
            {'BP_KL_InvestigationComponent': K.F_CORE + '/BP_KL_InvestigationComponent',
             'BP_KL_ListeningComponent': K.F_CORE + '/BP_KL_ListeningComponent',
             'BP_KL_InteractComponent': K.F_CORE + '/BP_KL_InteractComponent',
             'BP_FirstPersonCharacter': K.BP_TPL_CHAR,
             'BP_KL_HUD': K.F_UI + '/BP_KL_HUD'}[bpname])
        if bp is None:
            fail('census: %s missing' % bpname)
            continue
        for gname, floor in want.items():
            g = next((x for x in BPT.list_graphs(bp) if x.get_name() == gname), None)
            if g is None:
                fail('census: %s has no graph %s' % (bpname, gname))
                continue
            ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
            n = len(ed.list_all_nodes())
            (ok if n >= floor else fail)('%-32s %-20s nodes=%d (floor %d)' % (
                bpname, gname, n, floor))


def main():
    K.make_folders()
    check_blueprints()
    check_assets()
    check_props()
    check_level()
    check_graphs()
    check_validation()


K.run(main)
