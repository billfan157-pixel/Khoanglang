"""Art pass probe 78: UE 5.8 post-process override property names.

29 of the 44 grade settings were rejected on Lvl_KL_School3_Art, all of them
the b_override_* family: UE 5.8 moved the override flags off
FPostProcessSettings. Fixed exposure and disabled motion blur / DOF matter
for both the look and the frame budget, so the real names are needed.
"""

import os
import traceback

import unreal

OUT = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\art78'
os.makedirs(OUT, exist_ok=True)
REP = os.path.join(OUT, 'report.txt')


def p(m=''):
    line = str(m)
    unreal.log('A78: ' + line)
    with open(REP, 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()


def main():
    s = unreal.PostProcessSettings()
    props = [m for m in dir(s) if not m.startswith('_')]
    p('=== A. does FPostProcessSettings have any b_override_* left? ===')
    p('  override props: %s' % [x for x in props if 'override' in x.lower()])
    p('')
    p('=== B. exposure / eye adaptation ===')
    p('  %s' % [x for x in props if 'exposure' in x.lower()
                or 'eye_adapt' in x.lower()])
    p('  AutoExposureMethod: %s' % [a for a in dir(unreal.AutoExposureMethod)
                                    if not a.startswith('_')])
    p('')
    p('=== C. motion blur / DOF / lens flare ===')
    for key in ('motion_blur', 'depth_of_field', 'lens_flare', 'bloom',
                'vignette', 'ambient_occlusion', 'chromatic'):
        p('  %-20s %s' % (key, [x for x in props if key in x.lower()]))
    p('')
    p('=== D. what can actually be SET on the struct? ===')
    SET = [
        ('auto_exposure_method', unreal.AutoExposureMethod.AEM_MANUAL),
        ('auto_exposure_min_brightness', 0.55),
        ('auto_exposure_max_brightness', 1.30),
        ('auto_exposure_apply_physical_camera_exposure', False),
        ('auto_exposure_bias', 0.0),
        ('motion_blur_amount', 0.0),
        ('camera_motion_blur_amount', 0.0),
        ('depth_of_field_enabled', False),
        ('lens_flare_bloom_intensity', 0.0),
        ('chromatic_aberration_intensity', 0.0),
        ('color_contrast', 1.14),
        ('color_saturation', 0.80),
        ('color_gamma', 1.06),
        ('color_offset', (0.006, 0.010, 0.020, 0.0)),
        ('color_gain', (0.97, 0.99, 1.04, 1.0)),
        ('vignette_intensity', 0.38),
        ('bloom_intensity', 0.45),
        ('bloom_threshold', 1.15),
        ('ambient_occlusion_intensity', 0.90),
        ('ambient_occlusion_radius', 60.0),
        ('ambient_occlusion_power', 1.5),
        ('ambient_occlusion_static_fraction', 0.40),
        ('screen_space_reflections_intensity', 12.0),
    ]
    ok_list, bad_list = [], []
    for prop, val in SET:
        try:
            s.set_editor_property(prop, val)
            ok_list.append(prop)
        except Exception as exc:
            bad_list.append((prop, str(exc)[:110]))
    p('  settable (%d): %s' % (len(ok_list), ok_list))
    for prop, err in bad_list:
        p('  REJECTED %-46s %s' % (prop, err))

    p('')
    p('=== E. PostProcessVolume actor: where do the overrides live now? ===')
    cls = unreal.PostProcessVolume
    cdo = unreal.get_default_object(cls)
    aprops = [m for m in dir(cdo) if not m.startswith('_')]
    p('  override props on the volume: %s' % [x for x in aprops
                                              if 'override' in x.lower()])
    p('  blend/priority props: %s' % [x for x in aprops
                                      if any(k in x.lower() for k in
                                             ('blend', 'priority', 'unbound',
                                              'enabled', 'setting'))])

    p('')
    p('=== F. spawn a volume and try the override flags on it ===')
    from editor_toolset.toolsets import scene as SCENE
    t = unreal.Transform()
    t.set_editor_property('translation', unreal.Vector(0, 0, 150))
    t.set_editor_property('scale3d', unreal.Vector(1, 1, 1))
    a = SCENE.SceneTools.add_to_scene_from_class(cls, 'A78_PP', t)
    if a is None:
        p('  spawn failed')
    else:
        for prop, val in (('blend_weight', 1.0), ('blend_radius', 0.0),
                          ('unbound', True), ('priority', 0.0),
                          ('settings', s)):
            try:
                a.set_editor_property(prop, val)
                p('    %s ok' % prop)
            except Exception as exc:
                p('    %s -> %r' % (prop, str(exc)[:110]))
        p('  final settings sanity: contrast=%s saturation=%s' % (
            a.get_editor_property('settings').color_contrast if True else 0,
            a.get_editor_property('settings').color_saturation))
        p('  motion_blur_amount=%s' % a.get_editor_property('settings').motion_blur_amount)
        p('  exposure_method=%s' % a.get_editor_property('settings').auto_exposure_method)
        SCENE.SceneTools.remove_from_scene(a)
    p('DONE')


if os.path.exists(REP):
    os.remove(REP)
try:
    main()
except Exception:
    p(traceback.format_exc())
    p('A78_FATAL')
