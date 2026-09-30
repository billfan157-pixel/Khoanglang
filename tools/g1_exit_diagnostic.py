"""Bounded shutdown diagnostic on an exact package; never qualifies rendering."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import time
from verify_release import ROOT, package_digest, write_json

parser = argparse.ArgumentParser()
parser.add_argument('build_run', type=Path)
parser.add_argument('--map', help='Explicit cooked map for a diagnostic control')
args = parser.parse_args()
build = args.build_run.resolve()/'WindowsBuild'
before = package_digest(build)
stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
run = ROOT/'_release_work'/('g1_exit_nullrhi_'+stamp)
run.mkdir()
exe = build/'Engine/Binaries/Win64/UnrealGame.exe'
command = [str(exe),'../../../KhoangLang0217/KhoangLang0217.uproject',
    '-NullRHI','-nosound','-unattended','-SaveToUserDir',
    '-UserDir='+str(run/'UserData'),'-abslog='+str(run/'runtime.log'),
    '-csvCaptureFrames=60','-csvCompression=0','-ExitAfterCsvProfiling',
    '-ExecCmds=t.MaxFPS 0,csv.ForceExit 0']
if args.map:
    command.insert(2,args.map)
report = {'scope':'Same G1 package, NullRHI/no sound shutdown diagnostic only',
          'artifact_sha256':before['sha256'],'argv':command,
          'started_utc':datetime.now(timezone.utc).isoformat(),
          'rendering_qualified':False,'audio_qualified':False}
report['requested_map']=args.map
startup = subprocess.STARTUPINFO()
startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
startup.wShowWindow = 0
with (run/'stdout.log').open('w',encoding='utf-8') as output:
    process = subprocess.Popen(command,cwd=exe.parent,stdout=output,
        stderr=subprocess.STDOUT,startupinfo=startup,shell=False)
    report['pid']=process.pid
    write_json(run/'process_binding.json',report)
    try:
        report['exit_code']=process.wait(timeout=60)
    except subprocess.TimeoutExpired:
        report['status']='RUNNING_AT_OBSERVATION_TIMEOUT'
report['artifact_unchanged']=package_digest(build)['sha256']==before['sha256']
report['run']=run.relative_to(ROOT).as_posix()
write_json(run/'result.json',report)
print(json.dumps(report,indent=2))
raise SystemExit(0 if report.get('exit_code') == 0 and report['artifact_unchanged'] else 1)
