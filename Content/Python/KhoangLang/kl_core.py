"""Khoang Lang 02:17 - shared Blueprint graph-building helpers (UE 5.8.3).

Wraps the Epic EditorToolset with a small, explicit layer so the build scripts
read like a wiring diagram instead of raw pin plumbing.

Every node type id / function path used here was verified against this editor
build by the probe_*.py discovery scripts (see docs/tech/MILESTONE1_NOTES.md).
A bad id fails loudly through `warn`/`fail` rather than silently.
"""

import os
import traceback

import unreal

from editor_toolset.toolsets import actor as ACT
from editor_toolset.toolsets import blueprint as BP
from editor_toolset.toolsets import scene as SCENE
from editor_toolset.toolsets.blueprint import ContainerType

BPT = BP.BlueprintTools

# --------------------------------------------------------------------------- #
# paths
# --------------------------------------------------------------------------- #

ROOT = '/Game/KhoangLang'
F_AUDIO = ROOT + '/Audio'
F_MAT = ROOT + '/Materials'
F_DATA = ROOT + '/Data'
F_CORE = ROOT + '/Blueprints/Core'
F_PROPS = F_CORE + '/Props'
F_PLAYER = ROOT + '/Blueprints/Player'
F_UI = ROOT + '/Blueprints/UI'
F_MAPS = ROOT + '/Maps'

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

# verified function paths
F_EQUAL_INT = '/Script/Engine.KismetMathLibrary:EqualEqual_IntInt'
F_TEXT2STR = '/Script/Engine.KismetTextLibrary:Conv_TextToString'
F_STR2TEXT = '/Script/Engine.KismetTextLibrary:Conv_StringToText'
F_INT2STR = '/Script/Engine.KismetStringLibrary:Conv_IntToString'
F_SELECT = 'Utilities|Select'
F_BRANCH = 'Utilities|FlowControl|Branch'
F_PRINT = 'Development|PrintString'
F_SET_HIDDEN = 'Development|SetHiddeninGame'
F_GET_OWNER = '/Script/Engine.ActorComponent:GetOwner'
F_GET_COMP = 'Actor|GetComponentbyClass'
F_GET_ACTOR_LOC = 'Transformation|GetActorLocation'
F_BREAK_HIT = 'Collision|BreakHitResult'
F_SPHERE_TRACE = 'Collision|SphereTraceByChannel'
F_ISVALID = '/Script/Engine.KismetSystemLibrary:IsValid'
F_KEY_DOWN = '/Script/Engine.PlayerController:WasInputKeyJustPressed'
F_MAKE_KEY = 'Utilities|Struct|MakeKey'
F_DELAY = '/Script/Engine.KismetSystemLibrary:Delay'
F_PLAY2D = 'Audio|PlaySound2D'
F_PLAYATLOC = '/Script/Engine.GameplayStatics:PlaySoundAtLocation'
F_SPAWNATLOC = '/Script/Engine.GameplayStatics:SpawnSoundAtLocation'
F_SPAWN2D = '/Script/Engine.GameplayStatics:SpawnSound2D'
F_AC_SET_SOUND = 'Audio|Components|Audio|SetSound'
F_AC_PLAY = 'Audio|Components|Audio|Play'
F_AC_STOP = 'Audio|Components|Audio|Stop'
F_AC_FADEIN = 'Audio|Components|Audio|FadeIn'
F_AC_FADEOUT = 'Audio|Components|Audio|FadeOut'
F_AC_VOL = 'Audio|Components|Audio|SetVolumeMultiplier'
F_AC_LP_ON = 'Audio|Components|Audio|SetLowPassFilterEnabled'
F_AC_LP_FREQ = 'Audio|Components|Audio|SetLowPassFilterFrequency'
F_LIGHT_INT = 'Rendering|Components|Light|SetIntensity'
F_LIGHT_COLOR = 'Rendering|Components|Light|SetLightColor'
F_ARR_ADD = 'Utilities|Array|Add'
F_LIGHTEN_COLOR = 'Math|Color|MakeColor'

# --------------------------------------------------------------------------- #
# reporting
# --------------------------------------------------------------------------- #

LOG = []
FAILS = []
REPORT_PATH = r'C:\Users\phanb\AppData\Local\Temp\opencode\kl\build.txt'


def log(msg):
    line = str(msg)
    LOG.append(line)
    unreal.log('KL: ' + line)
    try:
        with open(REPORT_PATH, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
            f.flush()
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
    FAILS.append(str(msg))
    log('  FAIL %s' % msg)


def flush():
    log('')
    log('FAILURES: %d' % len(FAILS))
    for f in FAILS:
        log('   - %s' % f)
    unreal.log('KL_FAILURES=%d' % len(FAILS))


def run(main_fn, clear=True):
    if clear and os.path.exists(REPORT_PATH):
        try:
            os.remove(REPORT_PATH)
        except Exception:
            pass
    try:
        main_fn()
    except Exception:
        log(traceback.format_exc())
        fail('unhandled exception')
    flush()


# --------------------------------------------------------------------------- #
# assets
# --------------------------------------------------------------------------- #

def eas():
    return unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)


def make_folders():
    for p in (ROOT, F_AUDIO, F_MAT, F_DATA, F_CORE, F_PROPS, F_PLAYER, F_UI, F_MAPS):
        try:
            eas().make_directory(p)
        except Exception as exc:
            warn('make_directory %s: %r' % (p, exc))


def load(path, cls=None):
    a = unreal.load_asset(path)
    if a is None:
        raise RuntimeError('asset not found: ' + path)
    if cls is not None and not isinstance(a, cls):
        raise RuntimeError('%s is %s, expected %s' % (path, a.get_class().get_name(), cls))
    return a


def bp_class(asset_path):
    """Generated class of a Blueprint asset.

    The package is loaded explicitly first: in a headless commandlet
    load_class() alone does not always find freshly written component classes.
    """
    name = asset_path.rsplit('/', 1)[-1]
    asset = unreal.load_asset(asset_path)
    if asset is not None:
        try:
            c = asset.generated_class()
            if c is not None:
                return c
        except Exception:
            pass
    c = unreal.load_class(None, '%s.%s_C' % (asset_path, name))
    if c is None:
        raise RuntimeError('no generated class for ' + asset_path)
    return c


def cls_path(asset_path):
    return '%s.%s_C' % (asset_path, asset_path.rsplit('/', 1)[-1])


def native(name):
    """UClass for a native engine class, e.g. native('DataAsset')."""
    c = unreal.load_class(None, '/Script/Engine.' + name)
    if c is None:
        raise RuntimeError('no native class ' + name)
    return c


def resolve_class(spec):
    """Accept '/Game/..' Blueprint path, '/Script/Engine.X', a bare native name,
    or a UClass, and return a UClass usable by the EditorToolset."""
    if isinstance(spec, str):
        if spec.startswith('/Game/'):
            return bp_class(spec)
        if spec.startswith('/Script/'):
            return unreal.load_class(None, spec)
        return native(spec)
    try:
        if isinstance(spec, unreal.Class):
            return spec
    except Exception:
        pass
    return spec.static_class()


def obj_pin(path):
    return path


def new_bp(folder, name, parent, reuse=True):
    """Create a Blueprint of `parent` (native class or Blueprint asset path)."""
    path = '%s/%s' % (folder, name)
    existing = unreal.load_asset(path)
    if existing is not None:
        if isinstance(existing, unreal.Blueprint):
            if not reuse:
                unreal.EditorAssetLibrary.delete_asset(path)
            else:
                log('  reuse %s' % path)
                return existing, path
        else:
            warn('replacing stale non-blueprint asset at %s' % path)
            try:
                unreal.EditorAssetLibrary.delete_asset(path)
            except Exception:
                pass
    if isinstance(parent, str) and parent.startswith('/Game/'):
        parent_cls = bp_class(parent)
    else:
        parent_cls = resolve_class(parent)
    bp = BPT.create(folder, name, parent_cls)
    if not isinstance(bp, unreal.Blueprint):
        raise RuntimeError('BlueprintTools.create failed for ' + path)
    BPT.compile_blueprint(bp)
    log('  created %s' % path)
    return bp, path


def new_data_asset(folder, name, data_asset_class_path):
    at = unreal.AssetToolsHelpers.get_asset_tools()
    path = '%s/%s' % (folder, name)
    target = bp_class(data_asset_class_path)
    existing = unreal.load_asset(path)
    if existing is not None:
        if existing.get_class() == target:
            log('  reuse %s' % path)
            return existing, path
        try:
            unreal.EditorAssetLibrary.delete_asset(path)
        except Exception as exc:
            raise RuntimeError('cannot replace %s: %r' % (path, exc))
    factory = unreal.DataAssetFactory()
    for prop in ('data_asset_class', 'DataAssetClass'):
        try:
            factory.set_editor_property(prop, target)
            break
        except Exception:
            continue
    inst = at.create_asset(name, folder, unreal.DataAsset, factory)
    if inst is None:
        raise RuntimeError('create_asset failed for ' + path)
    for prop in ('data_asset_class', 'DataAssetClass'):
        try:
            inst.set_editor_property(prop, target)
            break
        except Exception:
            continue
    log('  created %s  class=%s' % (path, inst.get_class().get_name()))
    return inst, path


def save(path):
    """Save an asset or a whole folder.

    EditorAssetSubsystem.save_directory only writes directories, so a single
    asset path has to go through EditorAssetLibrary.save_loaded_asset.
    """
    try:
        asset = unreal.load_asset(path)
        if asset is not None:
            saved = unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
        else:
            saved = eas().save_directory(path, only_if_is_dirty=False, recursive=True)
        if not saved:
            raise RuntimeError('Unreal save API returned failure')
        ok('saved %s' % path)
        return True
    except Exception as exc:
        fail('save %s: %r' % (path, exc))
        return False


# --------------------------------------------------------------------------- #
# variables
# --------------------------------------------------------------------------- #

def var(bp, name, type_name, editable=False):
    try:
        BPT.add_variable(bp, name, type_name)
    except Exception as exc:
        if 'already exists' not in str(exc):
            fail('add_variable %s: %r' % (name, exc))
            return
    if editable:
        BPT.set_variable_instance_editable(bp, name, True)


def var_arr(bp, name, type_name, editable=False):
    try:
        BPT.add_variable(bp, name, type_name, None, ContainerType.ARRAY)
    except Exception as exc:
        if 'already exists' not in str(exc):
            fail('add_variable %s: %r' % (name, exc))
            return
    if editable:
        BPT.set_variable_instance_editable(bp, name, True)


def var_obj(bp, name, obj_class, container=None, editable=False):
    try:
        BPT.add_object_variable(bp, name, resolve_class(obj_class), None, container)
    except Exception as exc:
        if 'already exists' not in str(exc):
            fail('add_object_variable %s: %r' % (name, exc))
            return
    if editable:
        BPT.set_variable_instance_editable(bp, name, True)


def cdo(bp):
    return BPT.get_default_object(bp)


def set_cdo(bp, prop, value):
    return cdo(bp).set_editor_property(prop, value)


def cdo_components(bp):
    return ACT.ActorTools.get_components(cdo(bp))


def find_comp(actor, class_name):
    for c in ACT.ActorTools.get_components(actor):
        if c.get_class().get_name() == class_name:
            return c
    return None


def find_comp_of(bp, class_name):
    return find_comp(cdo(bp), class_name)


def add_comp(bp, comp_class, name, parent=None):
    """Add a component once. Re-running the build must not stack duplicates."""
    cls = resolve_class(comp_class)
    wanted = cls.get_name()
    for c in cdo_components(bp):
        if c.get_class().get_name() == wanted:
            log('  reuse component %s (%s)' % (c.get_name(), wanted))
            return c
    c = ACT.ActorTools.add_component(bp, cls, name)
    if c is None:
        fail('add_component %s on %s' % (name, bp.get_name()))
        return None
    if parent is not None:
        try:
            ACT.ActorTools.set_parent_component(c, parent)
        except Exception as exc:
            warn('set_parent_component %s: %r' % (name, exc))
    return c


def cpr(bp, prop, value):
    """Set a property on the CDO of `bp` (a component BP or actor BP)."""
    try:
        cdo(bp).set_editor_property(prop, value)
        return True
    except Exception as exc:
        fail('set %s.%s: %r' % (bp.get_name(), prop, exc))
        return False


def comp_set(comp, prop, value, where=''):
    try:
        comp.set_editor_property(prop, value)
        return True
    except Exception as exc:
        fail('component prop %s.%s %s: %r' % (comp.get_name(), prop, where, exc))
        return False


# --------------------------------------------------------------------------- #
# graph builder
# --------------------------------------------------------------------------- #

class B(object):
    """Thin wiring helper over a single Blueprint graph."""

    def __init__(self, graph, label=''):
        self.graph = graph
        self.label = label
        self.ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        self._x = 0
        self._y = 0

    # -- node creation ----------------------------------------------------- #

    def _pos(self, node):
        try:
            node.set_editor_property('node_location', unreal.Vector2D(self._x, self._y))
        except Exception:
            try:
                node.set_editor_property('node_location', unreal.Vector(self._x, self._y))
            except Exception:
                pass
        self._x += 300
        return node

    def at(self, x, y):
        self._x = x
        self._y = y
        return self

    def clear(self, keep_prefixes=('K2Node_FunctionEntry', 'K2Node_FunctionResult')):
        """Drop nodes this build owns so re-runs stay idempotent.

        The First Person template graphs are preserved: anything that looks like
        an event / input node is kept.
        """
        drop = []
        for n in self.ed.list_all_nodes():
            cn = n.get_class().get_name()
            if any(cn.startswith(k) for k in keep_prefixes):
                continue
            if cn.startswith('K2Node_Event') or cn.startswith('K2Node_Input') \
                    or cn.startswith('K2Node_EnhancedInput'):
                continue
            drop.append(n)
        if drop:
            self.ed.remove_nodes(drop)
        return len(drop)

    def n(self, type_id):
        node = self.ed.create_node_from_name(type_id, unreal.Vector2D(0, 0), [], None)
        if node is None:
            fail('%s: node id not found: %s' % (self.label, type_id))
            return None
        return self._pos(node)

    def c(self, path):
        node = self.ed.add_call_function_node(path)
        if node is None:
            fail('%s: function not found: %s' % (self.label, path))
            return None
        return self._pos(node)

    def ev(self, event_id):
        return self.n('AddEvent|Event' + event_id)

    def g(self, name):
        node = self.ed.add_get_member_variable_node(unreal.Name(name))
        if node is None:
            fail('%s: no member variable %s' % (self.label, name))
            return None
        return self._pos(node)

    def s(self, name):
        node = self.ed.add_set_member_variable_node(unreal.Name(name))
        if node is None:
            fail('%s: no member variable %s' % (self.label, name))
            return None
        return self._pos(node)

    def branch(self):
        return self.n(F_BRANCH)

    def sel(self):
        return self.n(F_SELECT)

    def print(self, text, to_screen=True):
        node = self.n(F_PRINT)
        if node is None:
            return None
        self.setv(node, 'InString', text)
        self.setv(node, 'bPrintToScreen', 'true' if to_screen else 'false')
        self.setv(node, 'bPrintToLog', 'true')
        self.setv(node, 'Duration', '6.0')
        return node

    # -- pins -------------------------------------------------------------- #

    def info(self, node):
        return BPT.get_node_infos([node])[0]

    def out(self, node, name):
        for x in self.info(node).output_pins:
            if x.name == name:
                return x
        raise KeyError('%s: no output pin %r on %s (%s)' % (
            self.label, name, node.get_name(),
            [x.name for x in self.info(node).output_pins]))

    def out_any(self, node):
        for x in self.info(node).output_pins:
            if x.type_id != 'Exec' and x.type_id != 'Delegate':
                return x
        raise KeyError('%s: no value output on %s' % (self.label, node.get_name()))

    def inp(self, node, name):
        for x in self.info(node).input_pins:
            if x.name == name:
                return x
        raise KeyError('%s: no input pin %r on %s (%s)' % (
            self.label, name, node.get_name(),
            [x.name for x in self.info(node).input_pins]))

    def has_in(self, node, name):
        try:
            self.inp(node, name)
            return True
        except KeyError:
            return False

    # -- wiring ------------------------------------------------------------ #

    def link(self, src_node, src_pin, dst_node, dst_pin):
        return self.plink(self.out(src_node, src_pin), self.inp(dst_node, dst_pin))

    def plink(self, out_pin, in_pin):
        BPT.connect_pins(out_pin.pin_id, in_pin.pin_id)
        return True

    def self_link(self, node, var_name):
        """Wire a node's `self` pin from a get-member-variable of the same name."""
        gv = self.g(var_name)
        return self.link(gv, self.out_any(gv).name, node, 'self')

    def setv(self, node, pin, value):
        if node is None:
            return False
        try:
            BPT.set_pin_value(self.inp(node, pin).pin_id, value)
            return True
        except Exception as exc:
            fail('%s: set %s.%s = %r -> %r' % (self.label, node.get_name(), pin, value, exc))
            return False

    def set_exec(self, node, pin='execute', src=None, src_pin='then'):
        if src is not None:
            self.link(src, src_pin, node, pin)
        return node

    # -- common fragments -------------------------------------------------- #

    def andb(self, a_node, a_pin, b_node, b_pin):
        """a AND b as a single wildcard Select(false, b, a)."""
        s = self.sel()
        self.link(a_node, a_pin, s, 'Option 0')
        self.setv(s, 'Option 0', 'false')
        self.link(b_node, b_pin, s, 'Option 1')
        self.link(a_node, a_pin, s, 'Index')
        return s

    def orb(self, a_node, a_pin, b_node, b_pin):
        """a OR b as Select(true, b, a)."""
        s = self.sel()
        self.setv(s, 'Option 0', 'true')
        self.link(b_node, b_pin, s, 'Option 1')
        self.link(a_node, a_pin, s, 'Index')
        return s

    def notb(self, a_node, a_pin):
        s = self.sel()
        self.setv(s, 'Option 0', 'true')
        self.setv(s, 'Option 1', 'false')
        self.link(a_node, a_pin, s, 'Index')
        return s

    def cond_eq(self, a_node, a_pin, b_value):
        n = self.c(F_EQUAL_INT)
        self.link(a_node, a_pin, n, 'A')
        self.setv(n, 'B', str(b_value))
        return n

    def text2str(self, text_node, pin='ReturnValue'):
        n = self.c(F_TEXT2STR)
        self.link(text_node, pin, n, 'InText')
        return n

    def str2text(self, str_node, pin='ReturnValue'):
        n = self.c(F_STR2TEXT)
        self.link(str_node, pin, n, 'InString')
        return n

    def comp_of(self, actor_node, actor_pin, comp_class_path):
        """GetComponentByClass; returns a node whose single output is the component."""
        n = self.n(F_GET_COMP)
        self.link(actor_node, actor_pin, n, 'self')
        self.setv(n, 'ComponentClass', cls_path(comp_class_path)
                  if comp_class_path.startswith('/Game/') else comp_class_path)
        return n

    def owner_of(self, comp_node):
        n = self.c(F_GET_OWNER)
        self.plink(self.out_any(comp_node), self.inp(n, 'self'))
        return n

    def valid(self, node, pin='ReturnValue'):
        n = self.c(F_ISVALID)
        self.link(n, 'Object', node, pin)
        return n

    def decay(self, src_node, src_pin, cond_fn, then_fn, else_fn=None):
        """Branch on a boolean pin. cond_fn() -> bool output node/pin."""
        br = self.branch()
        self.plink(self.out(src_node, src_pin), self.inp(br, 'execute'))
        cond = cond_fn()
        if cond is None:
            return br
        self.plink(cond, self.inp(br, 'Condition'))
        if then_fn:
            then_fn(self.out(br, 'then'))
        if else_fn:
            else_fn(self.out(br, 'else'))
        return br

    def ret(self, value_node=None, value_pin='ReturnValue'):
        """Attach a return value without replacing an authored execution body."""
        r = None
        for n in self.ed.list_all_nodes():
            if n.get_class().get_name() == 'K2Node_FunctionResult':
                r = n
                break
        if r is None:
            r = self.ed.add_return_node()
        if r is None:
            fail('%s: add_return_node failed' % self.label)
            return None
        ri = self.info(r)
        exec_in = [x for x in ri.input_pins if x.type_id == 'Exec']
        val_in = [x for x in ri.input_pins if x.type_id != 'Exec']
        ent = self.entry(self.graph)
        if exec_in and ent is not None:
            entry_pin = self.out(ent, 'then')
            if not entry_pin.connected_pins:
                self.plink(entry_pin, exec_in[0])
        if value_node is not None and val_in:
            self.plink(self.out(value_node, value_pin), val_in[0])
        return r

    # -- function graphs --------------------------------------------------- #

    def functions(self, bp):
        return {g.get_name(): g for g in BPT.list_graphs(bp)}

    def fn(self, bp, name, params=()):
        """Create/load a function graph and declare params (idempotent)."""
        g = BPT.add_function_graph(bp, name)
        for pname, ptype, is_in in params:
            try:
                BPT.add_function_param(g, pname, ptype, is_in, None)
            except Exception as exc:
                if 'already exists' not in str(exc):
                    warn('add_function_param %s/%s: %r' % (name, pname, exc))
        return g

    def entry(self, graph):
        """The graph's function-entry / event node."""
        for n in self.ed.list_all_nodes():
            if n.get_class().get_name() in ('K2Node_FunctionEntry', 'K2Node_Event'):
                return n
        return None

    def param(self, graph, name):
        """Pin of a declared function parameter on the graph's entry node.

        Function *input* params surface as output pins of the entry node.
        """
        e = self.entry(graph)
        if e is None:
            return None
        for x in self.info(e).output_pins:
            if x.name == name:
                return x
        for x in self.info(e).input_pins:
            if x.name == name:
                return x
        return None

    def link_param(self, graph, pname, node, pin):
        p = self.param(graph, pname)
        if p is None:
            fail('%s: no parameter %r' % (self.label, pname))
            return False
        BPT.connect_pins(p.pin_id, self.inp(node, pin).pin_id)
        return True

    def key(self, letter):
        mk = self.n(F_MAKE_KEY)
        if mk is None:
            return None
        try:
            self.ed.add_node_pin(mk, unreal.Name('KeyName'), 'name')
        except Exception as exc:
            warn('add_node_pin KeyName: %r' % (exc,))
        if self.has_in(mk, 'KeyName'):
            self.setv(mk, 'KeyName', '"%s"' % letter)
        return mk

    def pressed(self, letter, pc_node=None, pc_pin='ReturnValue'):
        k = self.key(letter)
        n = self.c(F_KEY_DOWN)
        if k is not None:
            self.link(k, 'Key', n, 'Key')
        if pc_node is not None:
            self.link(pc_node, pc_pin, n, 'self')
        return n

    def set_bool(self, setter, pin, value):
        return self.setv(setter, pin, 'true' if value else 'false')

    # -- compile / verify -------------------------------------------------- #

    def compile(self, bp, label=''):
        try:
            BPT.compile_blueprint(bp, warnings_as_errors=False)
        except Exception as exc:
            fail('compile %s %s: %r' % (bp.get_name(), label, exc))
            return False
        errs = self.errors(bp)
        status = bp.get_editor_property('status')
        if status == unreal.BlueprintStatus.BS_ERROR:
            errs.append('Blueprint status is BS_ERROR')
        if errs:
            fail('compile errors in %s %s: %s' % (bp.get_name(), label, errs))
            return False
        ok('compiled %s %s' % (bp.get_name(), label))
        return True

    def audit(self, bp, prefixes=('Rendering|Components|', 'Audio|Components|',
                                  'Development|Set', 'Components|Activation',
                                  'Collision|Set')):
        """Report component-method nodes whose `self` pin is unconnected.

        An unconnected self pin compiles into the Blueprint's own class, which
        the Blueprint compiler rejects at load time with
        "This blueprint (self) is not a X, therefore 'Target' must have a
        connection" - easy to miss while building.
        """
        from editor_toolset.toolsets.blueprint import _get_node_type_id
        bad = []
        for g in BPT.list_graphs(bp):
            ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
            for n in ed.list_all_nodes():
                try:
                    tid = _get_node_type_id(n) or ''
                except Exception:
                    tid = ''
                if not any(tid.startswith(p) for p in prefixes):
                    continue
                for pin in BPT.get_node_infos([n])[0].input_pins:
                    if pin.name == 'self' and not pin.connected_pins:
                        bad.append('%s::%s -> %s' % (bp.get_name(), g.get_name(), tid))
        return bad

    def errors(self, bp):
        out = []
        for g in BPT.list_graphs(bp):
            e = unreal.BlueprintGraphEditor.get_graph_editor(g)
            for n in e.list_all_nodes():
                try:
                    if n.has_error():
                        out.append('%s::%s: %s' % (bp.get_name(), g.get_name(),
                                                   n.error_msg()))
                except Exception:
                    for meth in ('error_message', 'get_error_message'):
                        if hasattr(n, meth):
                            out.append('%s: %s' % (n.get_name(), getattr(n, meth)()))
                            break
        return out
