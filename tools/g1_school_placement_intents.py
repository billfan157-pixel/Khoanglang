"""Extract declarative placements without importing destructive art generators."""
import ast
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]

def extract():
    source = ROOT / 'Content/Python/KhoangLang/art_80_level.py'
    tree = ast.parse(source.read_text(encoding='utf-8'))
    names = {'ARCH', 'FURN', 'CORR_X0', 'CORR_Y0', 'HALL_X0', 'HALL_Y0',
             'ROOM_X0', 'ROOM_Y0', 'H', 'T', 'DOOR_X0', 'DOOR_H', 'WIN_Y',
             'WIN_W', 'WIN_Z0'}
    functions = {'build_shell', 'build_openings', 'build_classroom',
                 'build_corridor', 'build_lighting', 'cx_room'}
    selected = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = {n.id for t in node.targets for n in ast.walk(t)
                       if isinstance(n, ast.Name)}
            if targets & names:
                selected.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name in functions:
            selected.append(node)
    kit = SimpleNamespace(H=320, T=20, W_CLASS='unused', MAT='unused',
        **{n: lambda *a, **kw: 'unused' for n in ('floor', 'ceiling', 'wall', 'wall_door', 'header')})
    placements, lights = [], []
    def put(name, mesh_path, loc, rot=(0, 0, 0), **kwargs):
        placements.append(dict(label='ART_' + name, location=loc, rotation=rot))
    def light(kind, name, loc, intensity, rgb, radius=900, rot=(0, 0, 0), shadows=False, cone=(28, 60)):
        lights.append(dict(label='ART_' + name, kind=kind, location=loc,
            rotation=rot, intensity=intensity, rgb=rgb, radius=radius, shadows=shadows, cone=cone))
    namespace = dict(KIT=kit, M=SimpleNamespace(log=lambda *a: None), put=put, light=light)
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(source), 'exec'), namespace)
    for name in ('build_shell', 'build_openings', 'build_classroom', 'build_corridor', 'build_lighting'):
        namespace[name]()
    return dict(source='Content/Python/KhoangLang/art_80_level.py', placements=placements, lights=lights)

if __name__ == '__main__':
    result = extract()
    target = ROOT / 'docs/agent/EVIDENCE/G1_school_placement_intents.json'
    target.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(dict(placements=len(result['placements']), lights=len(result['lights']))))
