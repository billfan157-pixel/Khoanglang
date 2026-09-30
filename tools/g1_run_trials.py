"""Run bounded, fresh-PIE G1 engineering scenarios; never qualify release."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def command(*args):
    result = subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True,
                            text=True, encoding='utf-8', errors='replace', timeout=45)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    if args[:3] == ('tools/ue_mcp.py', 'call', 'EditorToolset.EditorAppToolset'):
        payload = json.loads(result.stdout)
        if payload.get('result', payload).get('isError'):
            raise RuntimeError(result.stdout)
    return result.stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('cases', nargs='*', default=['held', 'names', 'wrong',
        'tier1', 'decay', 'contact', 'avoidance', 'interactions'])
    args = parser.parse_args()
    allowed = {'held', 'names', 'wrong', 'tier1', 'decay', 'contact', 'avoidance', 'interactions'}
    if any(c not in allowed for c in args.cases):
        raise ValueError('Unknown case')
    results = []
    options = ROOT / '_g1_trial_pie_options.json'
    options.write_text(json.dumps({'options': {'bSimulate': False,
        'playMode': 'PlayMode_InViewPort', 'warmupSeconds': 2}}), encoding='utf-8')
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT,
        capture_output=True, text=True, check=True).stdout.strip()
    for case in args.cases:
        source = ROOT / 'tools' / ('g1_interaction_trial.py' if case == 'interactions'
                                  else 'g1_school_loop_trial.py')
        output = ROOT / 'docs/agent/EVIDENCE' / ('G1_camera_interactions.json'
            if case == 'interactions' else 'G1_school_' + case + '_trial.json')
        # Ignored adapter leaves the checked-in scenario source unchanged.
        adapter = ROOT / '_g1_trial_adapter.py'
        adapter.write_text('from pathlib import Path\n'
            + 'exec(compile(Path(' + repr(source.as_posix())
            + ').read_text(encoding="utf-8"), ' + repr(source.as_posix()) + ', "exec"), '
            + repr({'__file__': source.as_posix(), '__name__': '__main__',
                    'G1_CASE': case, 'G1_SOURCE_REVISION': revision}) + ')\n',
            encoding='utf-8')
        before = output.stat().st_mtime_ns if output.exists() else None
        try:
            command('tools/ue_mcp.py', 'call', 'EditorToolset.EditorAppToolset',
                    'StartPIE', str(options))
            print(command('tools/ue_live.py', str(adapter)), flush=True)
            deadline = time.monotonic() + 95
            while time.monotonic() < deadline:
                if output.exists() and output.stat().st_mtime_ns != before:
                    try:
                        report = json.loads(output.read_text(encoding='utf-8'))
                    except json.JSONDecodeError:
                        time.sleep(.2)
                        continue
                    if report.get('status') != 'running':
                        break
                time.sleep(.5)
            else:
                raise TimeoutError(case + ' did not produce a fresh terminal report')
            results.append({'case': case, 'status': report['status'],
                            'report': output.relative_to(ROOT).as_posix()})
            print(json.dumps(results[-1]), flush=True)
        finally:
            command('tools/ue_mcp.py', 'call', 'EditorToolset.EditorAppToolset', 'StopPIE')
    evidence = {'qualified_release': False, 'method': 'Fresh PIE; engineering debug scenarios',
                'cases': results}
    (ROOT / 'docs/agent/EVIDENCE/G1_trial_suite.json').write_text(
        json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    return 0 if all(r['status'] == 'passed' for r in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
