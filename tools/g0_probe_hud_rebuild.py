"""Rebuild a duplicate HUD, leaving the shipped HUD untouched for G0 diagnosis."""

import os
import sys

import unreal


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "Content", "Python", "KhoangLang")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import build_20_blueprints as build  # noqa: E402
import kl_core as K  # noqa: E402
from kl_core import BPT  # noqa: E402


SOURCE = K.F_UI + "/BP_KL_HUD"
COPY_NAME = "BP_KL_HUD_G0Repair"
COPY = K.F_UI + "/" + COPY_NAME


def report(message):
    unreal.log("G0REPAIR: " + str(message))


if unreal.EditorAssetLibrary.does_asset_exist(COPY):
    raise RuntimeError("probe copy already exists; inspect it before rerunning")
copy = unreal.EditorAssetLibrary.duplicate_asset(SOURCE, COPY)
if copy is None:
    raise RuntimeError("could not duplicate original HUD")
report("duplicated %s to %s" % (SOURCE, COPY))

rebuilt = build.build_hud(COPY_NAME)
if rebuilt != COPY:
    raise RuntimeError("duplicate HUD rebuild failed: %s; %s" % (rebuilt, K.FAILS))

asset = unreal.load_asset(COPY)
status = asset.get_editor_property("status")
report("duplicate status=%s" % status)
if status == unreal.BlueprintStatus.BS_ERROR:
    raise RuntimeError("duplicate HUD still has BS_ERROR")

targets = 0
missing = []
for graph in BPT.list_graphs(asset):
    editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for node in editor.list_all_nodes():
        for pin in BPT.get_node_infos([node])[0].input_pins:
            if (pin.name == "self" and
                    ("BP KL Investigation Component" in str(pin.type_id) or
                     "BP KL Listening Component" in str(pin.type_id))):
                targets += 1
                if not pin.connected_pins:
                    missing.append(node.get_node_title())
report("component targets=%d disconnected=%d %s" % (
    targets, len(missing), missing[:5]))
if targets < 10 or missing:
    raise RuntimeError("duplicate HUD targets are not fully connected")
