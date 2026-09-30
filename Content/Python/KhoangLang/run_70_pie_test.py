"""Milestone 1: run the level as a real game world from a headless commandlet.

The commandlet has a GEditor, so PIE ("Play In Editor" simulation) can create a
game world without a viewport.  This is the closest thing to a real playthrough
that fits this machine's memory budget.
"""

import os
import traceback

import unreal

OUT = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\playtest.txt'
LINES = []
RESULT = {'fail': 0}
MAP = '/Game/KhoangLang/Maps/Lvl_KL_School3'


def p(m):
    line = str(m)
    LINES.append(line)
    unreal.log('KLPT: ' + line)
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


ELL = unreal.EditorLevelLibrary
p('EditorLevelLibrary members: %s' % [m for m in dir(ELL) if not m.startswith('_')])

p('loading %s' % MAP)
check(bool(ELL.load_level(MAP)), 'level loads')

try:
    ELL.editor_play_in_viewport()
    p('editor_play_in_viewport() called')
except Exception as exc:
    p('editor_play_in_viewport raised %r' % (exc,))

_state = {'n': 0}


def _tick(delta):
    _state['n'] += 1
    if _state['n'] < 240:
        return True
    try:
        unreal.unregister_slate_post_tick_callback(_tick)
    except Exception:
        pass
    try:
        world = None
        for getter in ('get_gameplay_world', 'get_editor_world'):
            try:
                world = getattr(ELL, getter)()
                if world is not None and getter == 'get_gameplay_world':
                    break
            except Exception:
                world = None
        p('  world = %s' % (world.get_name() if world else 'None'))
        check(world is not None, 'a PIE game world exists')
        if world is None:
            p('PLAYTEST_FAILURES=%d' % RESULT['fail'])
            p('PLAYTEST_DONE')
            return False
        gw = world
        p('  world type = %s' % gw.get_world_type())
        check(str(gw.get_world_type()) != 'Editor', 'PIE world (not the editor world)',
              '(%s)' % gw.get_world_type())

        pawn = unreal.GameplayStatics.get_player_pawn(gw, 0)
        check(pawn is not None, 'player pawn exists',
              '(%s)' % (pawn.get_class().get_name() if pawn else 'None'))
        if pawn is not None:
            loc = pawn.get_actor_location()
            p('  pawn  = %.0f %.0f %.0f' % (loc.x, loc.y, loc.z))
            comps = sorted(c.get_class().get_name() for c in
                           pawn.get_components_by_class(unreal.ActorComponent))
            p('  pawn components: %s' % ', '.join(comps))
            check(any('Investigation' in c for c in comps), 'investigation component')
            check(any('Listening' in c for c in comps), 'listening component')
            check(any('SpotLight' in c for c in comps), 'flashlight')

        actors = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor)
        p('  actors = %d' % len(actors))
        for w in ('BP_KL_Prop_AttBook_C', 'BP_KL_Prop_TapeDeck_C',
                  'BP_KL_Prop_Roster_C', 'BP_KL_Prop_Corner_C'):
            hits = [a for a in actors if a.get_class().get_name() == w]
            check(len(hits) == 1, '%s present' % w, '(%d)' % len(hits))
        audio = [a for a in actors if a.get_class().get_name() == 'AudioComponent']
        p('  AudioComponents in PIE world = %d' % len(audio))
        check(len(audio) >= 4, 'StartBeds spawned the four ambient beds',
              '(%d)' % len(audio))
        lights = [a for a in actors if 'Light' in a.get_class().get_name()]
        check(len(lights) >= 8, 'level lights live', '(%d)' % len(lights))

        corner = [a for a in actors
                  if a.get_class().get_name() == 'BP_KL_Prop_Corner_C']
        if corner:
            for c in corner[0].get_components_by_class(unreal.StaticMeshComponent):
                p('  corner mesh hidden_in_game=%s visible=%s' % (
                    c.is_hidden_in_game(), c.is_visible()))
                check(c.is_hidden_in_game(),
                      'corner figure starts hidden (BeginPlay of the interact component)')
        ps = [a for a in actors if a.get_class().get_name() == 'PlayerStart']
        check(len(ps) == 1, 'one PlayerStart')
    except Exception:
        p(traceback.format_exc())
        RESULT['fail'] += 1
    p('')
    p('PLAYTEST_FAILURES=%d' % RESULT['fail'])
    p('PLAYTEST_DONE')
    return False


def main():
    if os.path.exists(OUT):
        try:
            os.remove(OUT)
        except Exception:
            pass
    p('registering PIE tick check')
    unreal.register_slate_post_tick_callback(_tick)


main()
