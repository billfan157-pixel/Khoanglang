"""Art pass probe 79: the four struct-typed grade properties.

color_contrast, color_saturation, color_gamma and vignette_size became structs
in UE 5.8. Desaturation is central to the horror look, so this needs resolving
rather than being dropped.
"""

import os
import traceback

import unreal

OUT = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\art79'
os.makedirs(OUT, exist_ok=True)
REP = os.path.join(OUT, 'report.txt')


def p(m=''):
    line = str(m)
    unreal.log('A79: ' + line)
    with open(REP, 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


TARGETS = ('color_contrast', 'color_saturation', 'color_gamma', 'vignette_size',
           'color_offset', 'color_gain', 'vignette_color')


def main():
    s = unreal.PostProcessSettings()
    p('=== A. what type is each property, and what does it hold? ===')
    vals = {}
    for prop in TARGETS:
        try:
            v = s.get_editor_property(prop)
            vals[prop] = v
            p('  %-20s %r' % (prop, v))
            p('       py type = %s' % type(v).__name__)
            p('       members = %s' % [m for m in dir(v)
                                       if not m.startswith('_')][:30])
        except Exception as exc:
            p('  %-20s EXC %r' % (prop, str(exc)[:150]))

    p('')
    p('=== B. are the struct classes exposed on unreal? ===')
    for n in ('ColorContrast', 'ColorSaturation', 'ColorGamma', 'VignetteSize',
              'ColorGradingLUT'):
        p('  unreal.%-22s %s' % (n, hasattr(unreal, n)))
        if hasattr(unreal, n):
            try:
                p('     members: %s' % [m for m in dir(getattr(unreal, n))
                                        if not m.startswith('_')][:25])
            except Exception as exc:
                p('     dir -> %r' % str(exc)[:90])

    p('')
    p('=== C. mutate the returned struct copy and write it back ===')
    for prop, member, val in (('color_saturation', 'saturation', 0.80),
                              ('color_contrast', 'contrast', 1.14),
                              ('color_gamma', 'gamma', 1.06),
                              ('vignette_size', 'size', 1.4)):
        try:
            cur = s.get_editor_property(prop)
            cur.set_editor_property(member, val)
            s.set_editor_property(prop, cur)
            p('  %s.%s = %s -> OK, now %r' % (prop, member, val,
                                              s.get_editor_property(prop)))
        except Exception as exc:
            p('  %s.%s -> %r' % (prop, member, str(exc)[:150]))

    p('')
    p('=== D. alternative: drive the look through offset/gain only ===')
    for prop, val in (('color_offset', (0.006, 0.010, 0.020, 0.0)),
                      ('color_gain', (0.97, 0.99, 1.04, 1.0))):
        try:
            s.set_editor_property(prop, val)
            p('  %s = %s OK' % (prop, val))
        except Exception as exc:
            p('  %s -> %r' % (prop, str(exc)[:120]))
    p('  color_offset now = %r' % (s.get_editor_property('color_offset'),))
    p('DONE')


if os.path.exists(REP):
    os.remove(REP)
try:
    main()
except Exception:
    p(traceback.format_exc())
    p('A79_FATAL')
