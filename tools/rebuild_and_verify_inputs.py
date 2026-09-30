"""Rebuild player character, school loop, and verify all keyboard input pins."""
import importlib
import json
from pathlib import Path
import sys
import unreal

ROOT = Path(unreal.Paths.project_dir())
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'Content/Python/KhoangLang'))

from editor_toolset.toolsets import blueprint as BP
BPT = BP.BlueprintTools

print("=== 1. REBUILDING NATIVE PLAYER (BP_KL_SchoolPlayer) ===")
import g1_build_native_player as bnp
importlib.reload(bnp)
bnp.main()

print("\n=== 2. REBUILDING SCHOOL LOOP (BP_KL_SchoolLoop) ===")
import g1_build_school_loop as bsl
importlib.reload(bsl)
bsl.main()

print("\n=== 3. REBUILDING SCHOOL PRESENTATION (BP_KL_SchoolCharacter) ===")
import g1_build_school_presentation as bsp
importlib.reload(bsp)
bsp.build_player()

print("\n=== 4. STAGING CANONICAL SCHOOL MAP (Lvl_KL_SchoolSlice) ===")
import g1_stage_school as stage
importlib.reload(stage)
stage.main()

print("\n=== 5. VERIFYING ALL KEY PINS ACROSS BLUEPRINTS ===")
blueprints_to_check = [
    ("/Game/KhoangLang/Production/G1Canon/BP_KL_SchoolPlayer", "PollNativeInput"),
    ("/Game/KhoangLang/Production/G1Canon/BP_KL_SchoolLoop", "PollSchoolKeys"),
    ("/Game/KhoangLang/Production/G1Canon/BP_KL_SchoolCharacter", "PollKeys"),
]

all_passed = True
total_keys_checked = 0

for bp_path, target_graph in blueprints_to_check:
    print(f"\nChecking {bp_path} -> {target_graph}:")
    bp = unreal.load_asset(bp_path)
    if bp is None:
        print(f"  ERROR: Could not load {bp_path}")
        all_passed = False
        continue
    
    found_graph = False
    for g in BPT.list_graphs(bp):
        if g.get_name() == target_graph:
            found_graph = True
            ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
            nodes = ed.list_all_nodes()
            infos = BPT.get_node_infos(nodes)
            for n, info in zip(nodes, infos):
                title = n.get_node_title()
                if 'IsInputKeyDown' in title or 'WasInputKeyJustPressed' in title:
                    for p in info.input_pins:
                        if p.name == 'Key':
                            total_keys_checked += 1
                            val = p.value
                            print(f"  [{title}] Key pin = {repr(val)}")
                            if val == '(' or val == '' or val is None:
                                print(f"    FAILED! Invalid key value: {repr(val)}")
                                all_passed = False
                            else:
                                print(f"    OK: {repr(val)}")
    if not found_graph:
        print(f"  ERROR: Graph {target_graph} not found in {bp_path}")
        all_passed = False

print(f"\nChecked {total_keys_checked} key nodes.")
if all_passed and total_keys_checked > 0:
    print("ALL KEY PINS ARE VALID AND VERIFIED!")
else:
    print("SOME KEY PINS FAILED VERIFICATION!")
    raise RuntimeError("Key pin verification failed!")
