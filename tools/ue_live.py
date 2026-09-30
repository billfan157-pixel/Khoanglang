"""Execute a local diagnostic script in this project's live Unreal editor."""

import argparse
import json
import os
from pathlib import Path
import sys
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("script", type=Path)
    parser.add_argument("--engine-root", type=Path, default=Path(
        os.environ.get("ProgramFiles", "C:/Program Files")) / "Epic Games/UE_5.8")
    args = parser.parse_args()
    sys.path.insert(0, str(args.engine_root / "Engine/Plugins/Experimental/"
                          "PythonScriptPlugin/Content/Python"))
    import remote_execution as remote

    client = remote.RemoteExecution()
    client.start()
    try:
        root = Path(__file__).resolve().parents[1]
        projects = list(root.glob('*.uproject'))
        if len(projects) != 1:
            raise RuntimeError('Expected exactly one project file')
        deadline = time.monotonic() + 12
        nodes = []
        while time.monotonic() < deadline:
            nodes = [n for n in client.remote_nodes
                     if n.get("project_name") == projects[0].stem
                     and os.path.normcase(os.path.normpath(n.get('project_root', '')))
                         == os.path.normcase(os.path.normpath(str(root)))]
            if nodes:
                break
            time.sleep(0.2)
        if len(nodes) != 1:
            raise RuntimeError("Expected one live project editor, found %d" % len(nodes))
        client.open_command_connection(nodes[0]["node_id"])
        result = client.run_command(str(args.script.resolve()).replace("\\", "/"))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("success") else 1
    finally:
        client.stop()


if __name__ == "__main__":
    raise SystemExit(main())
