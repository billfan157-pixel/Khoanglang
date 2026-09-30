"""Khoang Lang 02:17 - Milestone 1 shared build library.

Wraps the Epic EditorToolset Python API (Blueprint DSL, actors, assets) with the
small amount of project-specific knowledge the build scripts need.

Verified against UE 5.8.3 + Epic EditorToolset 1.0:
  * node type ids come from `find_node_types`; Blueprint-dependent ids
    (cross-BP calls, casts to BP classes) are NOT listed but DO create, so
    `probe` builds them explicitly and reports instead of assuming.
  * `find_node_types` is incomplete (e.g. no Utilities|FlowControl|Delay in this
    build), so every id used here is checked at build time and failures are loud.
"""

import os
import traceback

import unreal

from editor_toolset.toolsets import actor as ACT
from editor_toolset.toolsets import asset as ASSET
from editor_toolset.toolsets import blueprint as BP
from editor_toolset.toolsets import scene as SCENE
from editor_toolset.toolsets.blueprint import ContainerType

# --------------------------------------------------------------------------- #
# paths
# --------------------------------------------------------------------------- #

PROJ = unreal.Paths.project_dir()
ROOT = '/Game/KhoangLang'
F_AUDIO = ROOT + '/Audio'
F_CORE = ROOT + '/Blueprints/Core'
F_PROPS = F_CORE + '/Props'
F_PLAYER = ROOT + '/Blueprints/Player'
F_UI = ROOT + '/Blueprints/UI'
F_DATA = ROOT + '/Data'
F_INPUT = ROOT + '/Input'
F_MAPS = ROOT + '/Maps'
F_MAT = ROOT + '/Materials'

F_TPL = '/Game/FirstPerson'
BP_TPL_CHAR = F_TPL + '/Blueprints/BP_FirstPersonCharacter'
BP_TPL_PC = F_TPL + '/Blueprints/BP_FirstPersonPlayerController'
BP_TPL_GM = F_TPL + '/Blueprints/BP_FirstPersonGameMode'

MAP_NAME = 'Lvl_KL_School3'
MAP_PATH = F_MAPS + '/' + MAP_NAME

FONT = '/Engine/EngineFonts/Roboto'
MESH_CUBE = '/Engine/BasicShapes/Cube'
MESH_CYL = '/Engine/BasicShapes/Cylinder'
MESH_CONE = '/Engine/BasicShapes/Cone'
MESH_SPHERE = '/Engine/BasicShapes/Sphere'
MESH_PLANE = '/Engine/BasicShapes/Plane'

# --------------------------------------------------------------------------- #
# reporting
# --------------------------------------------------------------------------- #

_LOG = []
FAILURES = []


def log(msg):
    line = str(msg)
    _LOG.append(line)
    unreal.log('KLB: ' + line)
    try:
        p = os.environ.get('KL_REPORT', '')
        if p:
            with open(p, 'a', encoding='utf-8') as f:
                f.write(line + '\n')
    except Exception:
        pass


def step(label):
    log('')
    log('=== %s' % label)


def ok(msg):
    log('  OK   %s' % msg)


def warn(msg):
    log('  WARN %s' % msg)


def fail(msg):
    FAILURES.append(str(msg))
    log('  FAIL %s' % msg)


def flush_report(path):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(_LOG))
    except Exception:
        pass


# --------------------------------------------------------------------------- #
# assets
# --------------------------------------------------------------------------- #

def eas():
    return unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)


def atools():
    return unreal.AssetToolsHelpers.get_asset_tools()


def make_folders():
    for p in (ROOT, F_AUDIO, F_MAT, F_DATA, F_CORE, F_PROPS, F_PLAYER, F_UI,
              F_INPUT, F_MAPS):
        eas().make_directory(p)
    ok('folders ready under %s' % ROOT)


def load(path, cls=None):
    a = unreal.load_asset(path)
    if a is None:
        raise RuntimeError('asset not found: %s' % path)
    if cls is not None and not isinstance(a, cls):
        raise RuntimeError('%s is a %s, expected %s'
                           % (path, a.get_class().get_name(), cls))
    return a


def exists(path):
    return unreal.load_asset(path) is not None


def bp_class(asset_path, name):
    """Generated class object for a Blueprint asset ('/Game/X/BP_Y' -> BP_Y_C)."""
    c = unreal.load_class(None, '%s.%s_C' % (asset_path, name))
    if c is None:
        raise RuntimeError('no generated class for %s' % asset_path)
    return c


def asset_ref_string(asset_path, name):
    """String a BP object pin accepts for a Blueprint class default."""
    return '%s.%s_C' % (asset_path, name)


def save_dir(path):
    eas().save_directory(path, only_if_is_dirty=False, recursive=True)


def save_all():
    eas().save_directory('/Game', only_if_is_dirty=False, recursive=True)


# --------------------------------------------------------------------------- #
# blueprints
# --------------------------------------------------------------------------- #

def new_bp(folder, name, parent):
    """Create (or load) an Actor/DataAsset style Blueprint.

    `parent` may be a native unreal class (str-like) or a Blueprint asset path.
    """
    path = '%s/%s' % (folder, name)
    existing = unreal.load_asset(path)
    if isinstance(existing, unreal.Blueprint):
        log('  reuse %s' % path)
        return existing
    if existing is not None:
        warn('replacing non-blueprint asset at %s' % path)
        unreal.EditorAssetLibrary.delete_asset(path)
    if isinstance(parent, str) and parent.startswith('/'):
        parent_cls = bp_class(parent, os.path.basename(parent))
    else:
        parent_cls = parent.static_class()
    bp = BP.BlueprintTools.create(folder, name, parent_cls)
    if not isinstance(bp, unreal.Blueprint):
        raise RuntimeError('BlueprintTools.create failed for %s' % path)
    log('  created %s' % path)
    return bp


def set_parent(bp, parent):
    """Reparent to a Blueprint asset path (clears nodes that no longer compile)."""
    parent_cls = bp_class(parent, os.path.basename(parent))
    bp = BP.BlueprintTools.set_parent(bp, parent_cls)
    log('  parent -> %s' % parent)
    return bp


def var_bool(bp, name, default=False, editable=True):
    BP.BlueprintTools.add_variable(bp, name, 'bool')
    if editable:
        BP.BlueprintTools.set_variable_instance_editable(bp, name, True)
    cdo(bp).set_editor_property(name, bool(default))


def var_str(bp, name, default='', editable=True):
    BP.BlueprintTools.add_variable(bp, name, 'string')
    if editable:
        BP.BlueprintTools.set_variable_instance_editable(bp, name, True)
    cdo(bp).set_editor_property(name, str(default))


def var_str_array(bp, name, default=None, editable=True):
    BP.BlueprintTools.add_variable(bp, name, 'string', None, ContainerType.ARRAY)
    if editable:
        BP.BlueprintTools.set_variable_instance_editable(bp, name, True)
    cdo(bp).set_editor_property(name, list(default or []))


def var_obj(bp, name, obj_class):
    """obj_class: native unreal class or Blueprint asset path."""
    if isinstance(obj_class, str) and obj_class.startswith('/'):
        cls = bp_class(obj_class, os.path.basename(obj_class))
    else:
        cls = obj_class
    BP.BlueprintTools.add_object_variable(bp, name, cls)
    BP.BlueprintTools.set_variable_instance_editable(bp, name, True)


def var_obj_array(bp, name, obj_class):
    if isinstance(obj_class, str) and obj_class.startswith('/'):
        cls = bp_class(obj_class, os.path.basename(obj_class))
    else:
        cls = obj_class
    BP.BlueprintTools.add_object_variable(bp, name, cls, None, ContainerType.ARRAY)
    BP.BlueprintTools.set_variable_instance_editable(bp, name, True)


def cdo(bp):
    return BP.BlueprintTools.get_default_object(bp)


def set_cdo(bp, prop, value):
    o = cdo(bp)
    o.set_editor_property(prop, value)
    return o


def event_graph(bp):
    g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    if g is None:
        gs = BP.BlueprintTools.list_graphs(bp)
        g = gs[0]
    return g


def fn_graph(bp, name, inputs=(), outputs=()):
    g = BP.BlueprintTools.add_function_graph(bp, name)
    have_in = set()
    have_out = set()
    for f in BP.BlueprintTools.list_functions(bp):
        if str(f.name) == name:
            break
    for pname, ptype in inputs:
        if _has_param(g, pname, True):
            continue
        BP.BlueprintTools.add_function_param(g, pname, ptype, True)
    for pname, ptype in outputs:
        if _has_param(g, pname, False):
            continue
        BP.BlueprintTools.add_function_param(g, pname, ptype, False)
    return g


def _has_param(graph, name, is_input):
    try:
        ni = BP.BlueprintTools.get_graph_info(graph)  # not present in 1.0
    except Exception:
        pass
    for pin_name in getattr(graph, '_kl_known_params', ()):
        if pin_name == name:
            return True
    # add_function_param raises when the param already exists -> treat that as present
    return False


def add_param(graph, name, ptype, is_input):
    try:
        BP.BlueprintTools.add_function_param(graph, name, ptype, is_input)
        return True
    except Exception as exc:
        if 'already exists' in str(exc):
            return True
        raise


def fn(bp, name, inputs=(), outputs=()):
    """Create a function graph and declare parameters idempotently."""
    g = BP.BlueprintTools.add_function_graph(bp, name)
    for pname, ptype in inputs:
        add_param(g, pname, ptype, True)
    for pname, ptype in outputs:
        add_param(g, pname, ptype, False)
    return g


def write(graph, code, label=''):
    try:
        BP.BlueprintTools.write_graph_dsl(graph, code)
        return True
    except Exception as exc:
        fail('write_graph_dsl %s: %s' % (label or graph.get_name(), exc))
        return False


def compile_bp(bp, label=''):
    try:
        BP.BlueprintTools.compile_blueprint(bp, warnings_as_errors=False)
        ok('compiled %s %s' % (bp.get_name(), label))
        return True
    except Exception as exc:
        fail('compile %s %s: %s' % (bp.get_name(), label, exc))
        return False


# ---- cross-blueprint helpers ------------------------------------------------ #

def call_id(other_bp_name, func_name):
    """Type id for calling a function defined on another Blueprint asset."""
    return '%s_C|%s' % (other_bp_name, func_name)


def cast_id(other_bp_name):
    return 'Utilities|Casting|CastTo%s' % other_bp_name


def own(func_name):
    return '|%s' % func_name


def has_id(graph, type_id):
    try:
        return bool(BP.BlueprintTools.find_node_types(graph, type_id))
    except Exception:
        return False


def require_ids(graph, ids, where):
    for i in ids:
        if not has_id(graph, i):
            warn('%s: node id not listed by the action database -> %s' % (where, i))


# --------------------------------------------------------------------------- #
# components
# --------------------------------------------------------------------------- #

def add_component(bp_or_component, comp_class, name, parent=None):
    owner = parent if parent is not None else bp_or_component
    try:
        c = ACT.ActorTools.add_component(owner, comp_class.static_class(), name)
        ok('component %s on %s' % (name, bp_or_component.get_name()
                                   if hasattr(bp_or_component, 'get_name') else '?'))
        return c
    except Exception as exc:
        fail('add_component %s: %r' % (name, exc))
        return None


def comp_of(actor, class_path):
    for c in ACT.ActorTools.get_components(actor):
        if c.get_class().get_path_name() == class_path:
            return c
    return None


def find_cdo_component(bp, class_path):
    return comp_of(cdo(bp), class_path)


# --------------------------------------------------------------------------- #
# scene
# --------------------------------------------------------------------------- #

def xform(loc=(0.0, 0.0, 0.0), rot=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0)):
    t = unreal.Transform()
    t.set_editor_property('translation', unreal.Vector(*loc))
    t.set_editor_property('rotation', unreal.Rotator(rot[0], rot[1], rot[2]))
    t.set_editor_property('scale3d', unreal.Vector(*scale))
    return t


def spawn(actor_class, name, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    try:
        a = SCENE.SceneTools.add_to_scene_from_class(
            actor_class, name, xform(loc, rot, scale))
        if a is None:
            fail('spawn %s returned None' % name)
        return a
    except Exception as exc:
        fail('spawn %s: %r' % (name, exc))
        return None


def spawn_bp(asset_path, name, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    obj = unreal.load_asset(asset_path)
    if obj is None:
        fail('spawn_bp missing asset %s' % asset_path)
        return None
    try:
        a = SCENE.SceneTools.add_to_scene_from_asset(
            asset_path, name, xform(loc, rot, scale))
        if a is None:
            fail('spawn_bp %s returned None' % name)
        return a
    except Exception as exc:
        fail('spawn_bp %s: %r' % (name, exc))
        return None


def set_actor_instance(actor, prop, value):
    try:
        actor.set_editor_property(prop, value)
    except Exception as exc:
        fail('set %s.%s: %r' % (actor.get_name(), prop, exc))


def label(actor, text):
    try:
        ACT.ActorTools.set_label(actor, text)
    except Exception:
        pass


def add_tag(actor, tag):
    try:
        ACT.ActorTools.add_tag(actor, tag)
    except Exception:
        pass


# --------------------------------------------------------------------------- #
# DSL helpers
# --------------------------------------------------------------------------- #

def sv(name):
    return '(Variables|Default|Set%s)' % name


def gv(name):
    return '(Variables|Default|Get%s)' % name


def txt(s):
    return '"%s"' % s.replace('\\', '\\\\').replace('"', '\\"')


def by_path(actor, class_path):
    return '(Actor|GetComponentbyClass %s "%s")' % (actor, class_path)


def run(main_fn, report_path):
    try:
        main_fn()
    except Exception:
        log(traceback.format_exc())
        fail('unhandled exception')
    finally:
        flush_report(report_path)
        log('')
        log('FAILURES: %d' % len(FAILURES))
        for f in FAILURES:
            log('   - %s' % f)
        unreal.log('KLBUILD_FAILURES=%d' % len(FAILURES))
