"""Khoang Lang 02:17 - Milestone 1 runtime smoke test.

Executed inside a real game session (`py <this file>`) a few seconds after the
map has loaded.  It inspects the live world and then quits, so the editor log
carries the evidence.  Run with run_playtest.ps1.
"""

import os
import traceback

import unreal

OUT = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\playtest.txt'
LINES = []
RESULT = {'fail': 0}


def p(m):
    line = str(m)
    LINES.append(line)
    unreal.log('KLRT: ' + line)
    try:
        with open(OUT, 'w', encoding='utf-8') as f:
            f.write('\n'.join(LINES))
    except Exception:
        pass


def check(cond, label, extra=''):
    if cond:
        p('  OK   %s %s' % (label, extra))
    else:
        RESULT['fail'] += 1
        p('  FAIL %s %s' % (label, extra))


def finish():
    p('')
    p('PLAYTEST_FAILURES=%d' % RESULT['fail'])
    p('PLAYTEST_DONE')
    try:
        w = unreal.GameplayStatics.get_player_controller(0)
        w = w.get_world() if w else None
        if w is not None:
            unreal.SystemLibrary.execute_console_command(w, 'quit')
    except Exception:
        pass


def run():
    try:
        pc = unreal.GameplayStatics.get_player_controller(0)
        check(pc is not None, 'player controller exists')
        if pc is None:
            return finish()
        world = pc.get_world()
        p('  world  = %s' % world.get_name())
        check(world.get_name() == 'Lvl_KL_School3', 'prototype level loaded')

        pawn = unreal.GameplayStatics.get_player_pawn(0)
        check(pawn is not None, 'player pawn spawned',
              '(%s)' % (pawn.get_class().get_name() if pawn else 'None'))
        if pawn is not None:
            loc = pawn.get_actor_location()
            p('  pawn   = %.0f %.0f %.0f  health=%.0f' % (
                loc.x, loc.y, loc.z, pawn.get_health()))
            check(abs(loc.x - (-1000.0)) < 250.0, 'pawn near PlayerStart',
                  '(%.0f, %.0f, %.0f)' % (loc.x, loc.y, loc.z))
            check(pawn.get_health() > 0.0, 'pawn alive (no fall damage at spawn)')
            comps = [c.get_class().get_name() for c in pawn.get_components_by_class(
                unreal.ActorComponent)]
            p('  pawn components: %s' % ', '.join(sorted(comps)))
            check(any('Investigation' in c for c in comps),
                  'BP_KL_InvestigationComponent attached')
            check(any('Listening' in c for c in comps),
                  'BP_KL_ListeningComponent attached')
            check(any('SpotLight' in c for c in comps), 'flashlight attached')

        gm = world.get_world_settings().get_editor_property('default_game_mode')
        check(gm is not None and gm.get_name() == 'BP_KL_GameMode_C',
              'game mode is BP_KL_GameMode', '(%s)' % (gm.get_name() if gm else 'None'))
        hud = pc.get_hud()
        check(hud is not None and hud.get_class().get_name() == 'BP_KL_HUD_C',
              'HUD is BP_KL_HUD', '(%s)' % (hud.get_class().get_name() if hud else 'None'))

        actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
        p('  actors = %d' % len(actors))
        for w in ('BP_KL_Prop_AttBook_C', 'BP_KL_Prop_TapeDeck_C',
                  'BP_KL_Prop_Roster_C', 'BP_KL_Prop_Corner_C'):
            hits = [a for a in actors if a.get_class().get_name() == w]
            check(len(hits) == 1, '%s placed once' % w, '(%d)' % len(hits))
        lights = [a for a in actors if 'Light' in a.get_class().get_name()]
        check(len(lights) >= 8, 'level lights present', '(%d)' % len(lights))

        # the audio beds StartBeds spawns at runtime
        audio = [a for a in actors if a.get_class().get_name() == 'AudioComponent']
        p('  runtime AudioComponents in world: %d' % len(audio))
        check(len(audio) >= 4, 'four ambient beds spawned by StartBeds',
              '(%d)' % len(audio))
    except Exception:
        p(traceback.format_exc())
        RESULT['fail'] += 1
    finish()


_state = {'n': 0}


def _tick(delta):
    _state['n'] += 1
    if _state['n'] < 150:
        return True
    try:
        unreal.unregister_slate_post_tick_callback(_tick)
    except Exception:
        pass
    run()
    return False


def main():
    if os.path.exists(OUT):
        try:
            os.remove(OUT)
        except Exception:
            pass
    p('registered runtime check, waiting for world load')
    unreal.register_slate_post_tick_callback(_tick)


main()
