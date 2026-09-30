"""Khoang Lang 02:17 - art pass step 2b: art-pass interactable props.

New child Blueprints under Blueprints/Core/PropsArt.  The Milestone 1 props
(BP_KL_Prop_*) are untouched so Lvl_KL_School3 keeps working.

Each art prop keeps exactly ONE StaticMeshComponent, because
BP_KL_InteractComponent reveals/hides its owner's single mesh; extra shape
comes from the level dressing placed around it.
"""

import os
import sys

import unreal

HERE = r'C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang'
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import kl_core as K  # noqa: E402
from kl_core import BP, BPT  # noqa: E402
from kl_core import step, ok, warn, fail  # noqa: E402
from editor_toolset.toolsets import actor as ACT  # noqa: E402
from art_geo import quat  # noqa: E402

INT = K.F_CORE + '/BP_KL_InteractComponent'
F_ART = K.F_CORE + '/PropsArt'
MAT = K.ROOT + '/MaterialsArt'

MESH = {'Cube': '/Engine/BasicShapes/Cube',
        'Cylinder': '/Engine/BasicShapes/Cylinder',
        'Cone': '/Engine/BasicShapes/Cone',
        'Sphere': '/Engine/BasicShapes/Sphere'}

# Real prop meshes, authored by art_74_props.py and modelled at true scale in
# centimetres, so these props run at scale 1.0 with no material override: the
# mesh carries its own material slots.
KPROP = K.ROOT + '/Meshes/Props'

PROPS = [
    dict(name='BP_KL_Prop_ART_AttBook', prompt='Đọc sổ điểm danh',
         mesh_path=KPROP + '/SM_KL_Prop_AttBook', scale=(1.0, 1.0, 1.0),
         flags={}, rot_z=18.0),
    dict(name='BP_KL_Prop_ART_TapeDeck', prompt='Nghe băng nối loa',
         mesh_path=KPROP + '/SM_KL_Prop_TapeDeck', scale=(1.0, 1.0, 1.0),
         flags={'bTapeMode': True}, rot_z=0.0, audio=True,
         light=None, light_color=None),
    dict(name='BP_KL_Prop_ART_Roster', prompt='Đọc bảng danh sách lớp 3',
         mesh_path=KPROP + '/SM_KL_Prop_Roster', scale=(1.0, 1.0, 1.0),
         flags={'bNoteMode': True}, rot_z=0.0),
    dict(name='BP_KL_Prop_ART_Corner', prompt='Có ai ngồi ở đây',
         mesh_path=KPROP + '/SM_KL_Prop_Figure', scale=(1.0, 1.0, 1.0),
         flags={'bCornerMode': True, 'bHiddenAtStart': True}, rot_z=0.0,
         light='ART_CornerGlow', light_color=(0.60, 0.72, 0.98)),
]


def build(name, spec):
    bp, path = K.new_bp(F_ART, name, 'Actor')
    for c in list(K.cdo_components(bp)):
        try:
            ACT.ActorTools.remove_component(c)
        except Exception as exc:
            warn('remove %s: %r' % (c.get_name(), exc))
    mesh = K.add_comp(bp, 'StaticMeshComponent', 'PropMesh')
    ic = K.add_comp(bp, INT, 'KL_Interact')
    if spec.get('audio'):
        K.add_comp(bp, 'AudioComponent', 'TapeOut')
    if spec.get('light'):
        K.add_comp(bp, 'PointLightComponent', spec['light'])
    BPT.compile_blueprint(bp)

    cdo = K.cdo(bp)
    comps = ACT.ActorTools.get_components(cdo)
    m = [c for c in comps if c.get_class().get_name() == 'StaticMeshComponent']
    if not m:
        fail('%s: no mesh component' % name)
        return path
    sx, sy, sz = spec['scale']
    mesh = (unreal.load_asset(spec['mesh_path']) if spec.get('mesh_path')
            else unreal.load_asset(MESH[spec['mesh']]))
    if mesh is None:
        fail('%s: mesh not found' % name)
        return path
    m[0].set_editor_property('static_mesh', mesh)
    m[0].set_editor_property('relative_scale3d', unreal.Vector(sx, sy, sz))
    if spec.get('rot_z'):
        m[0].set_editor_property(
            'relative_rotation',
            unreal.Rotator(0.0, 0.0, spec['rot_z']))
    if spec.get('mat'):
        try:
            m[0].set_editor_property('override_materials',
                                    [unreal.load_asset('%s/%s' % (MAT, spec['mat']))])
        except Exception as exc:
            warn('%s material: %r' % (name, exc))
    if spec.get('audio'):
        for c in comps:
            if c.get_class().get_name() == 'AudioComponent':
                for prop in ('auto_activate', 'b_auto_activate'):
                    try:
                        c.set_editor_property(prop, False)
                        break
                    except Exception:
                        continue
    if spec.get('light'):
        lc = spec.get('light_color') or (0.7, 0.85, 1.0)
        for c in comps:
            if c.get_class().get_name() == 'PointLightComponent':
                for prop, val in (('light_color', unreal.Color(*lc)),
                                  ('intensity', 0.0),
                                  ('attenuation_radius', 240.0),
                                  ('cast_shadows', False),
                                  ('visible', True)):
                    try:
                        c.set_editor_property(prop, val)
                    except Exception:
                        pass
    icdo = None
    for c in comps:
        if 'Interact' in c.get_class().get_name():
            icdo = c
            break
    if icdo is not None:
        icdo.set_editor_property('PromptText', unreal.Text(spec['prompt']))
        for k, v in spec['flags'].items():
            icdo.set_editor_property(k, v)
    BPT.compile_blueprint(bp)
    ok('%-30s mesh=%-24s scale=%s flags=%s' % (
        path, spec.get('mesh_path', spec.get('mesh')), spec['scale'],
        spec['flags'] or '{}'))
    return path


def main():
    K.make_folders()
    K.eas().make_directory(F_ART)
    step('art interactable props')
    made = []
    for spec in PROPS:
        made.append(build(spec['name'], spec))
    K.save(F_ART)
    ok('%d art props' % len([x for x in made if x]))


K.run(main)
