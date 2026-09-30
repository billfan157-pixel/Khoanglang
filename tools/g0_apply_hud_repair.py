"""Rebuild the canonical HUD after the duplicate graph passed the pin audit."""

import os
import sys

import unreal


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "Content", "Python", "KhoangLang")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import build_20_blueprints as build  # noqa: E402
import kl_core as K  # noqa: E402


PATH = K.F_UI + "/BP_KL_HUD"
result = build.build_hud()
if result != PATH or K.FAILS:
    raise RuntimeError("HUD rebuild failed: %s; %s" % (result, K.FAILS))

asset = unreal.load_asset(PATH)
status = asset.get_editor_property("status")
unreal.log("G0REPAIR: canonical HUD status=%s" % status)
if status == unreal.BlueprintStatus.BS_ERROR:
    raise RuntimeError("canonical HUD still has BS_ERROR")
