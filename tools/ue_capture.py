"""Capture the live Unreal viewport through Epic's local MCP endpoint."""

import argparse
import base64
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _mcp_tool as mcp


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--camera", type=float, nargs=6,
                        metavar=("X", "Y", "Z", "PITCH", "YAW", "ROLL"))
    parser.add_argument("--ui", action="store_true")
    args = parser.parse_args()
    transform = None
    if args.camera:
        x, y, z, pitch, yaw, roll = args.camera
        transform = {"location": dict(x=x, y=y, z=z),
                     "rotation": dict(pitch=pitch, yaw=yaw, roll=roll),
                     "scale": dict(x=1, y=1, z=1)}
    result = mcp.rpc("tools/call", {"name": "call_tool", "arguments": {
        "toolset_name": "EditorToolset.EditorAppToolset",
        "tool_name": "CaptureViewport", "arguments": {
            "captureTransform": transform, "annotations": None,
            "bShowUI": args.ui}}}, timeout=45)
    payload = result.get("result", {})
    if payload.get("isError") or result.get("error"):
        raise RuntimeError(str(result)[:1500])
    for block in payload.get("content", []):
        if block.get("type") == "text":
            decoded = json.loads(block["text"])
            value = decoded.get("returnValue", {})
            image = value.pop("image", None)
            if image and image.get("data"):
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_bytes(base64.b64decode(image["data"]))
                args.output.with_suffix(".json").write_text(
                    json.dumps(value, indent=2), encoding="utf-8")
                print(json.dumps({"image": str(args.output),
                                  "bytes": args.output.stat().st_size,
                                  "metadata": value}))
                return
    raise RuntimeError("Capture returned no image")


if __name__ == "__main__":
    main()
