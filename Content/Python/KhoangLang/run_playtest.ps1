# Launches a real game session of the prototype level and runs the runtime
# smoke test inside it.  Results land in
#   C:\Users\phanb\AppData\Local\Temp\opencode\kl\playtest.txt
param(
  [int]$TimeoutSec = 300,
  [string]$Seconds = '12'
)
$ErrorActionPreference = 'Continue'
$exe   = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
$proj  = "C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\KhoangLang0217.uproject"
$map   = "/Game/KhoangLang/Maps/Lvl_KL_School3"
$dir   = "C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang"
$logDir = "C:\Users\phanb\AppData\Local\Temp\opencode\kl"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$src = Join-Path $dir "run_60_playtest.py"
# the project path contains spaces, which breaks -ExecCmds argument parsing:
# run the script from a space-free location instead
$stage = Join-Path $logDir "playtest_script.py"
Copy-Item $src $stage -Force
$scr = ($stage -replace '\\', '/')
$log = Join-Path $logDir "playtest.log"
if (Test-Path $log) { Remove-Item $log -Force }

$argList = @($proj, $map, "-game", "-nullrhi", "-unattended", "-nosplash",
             "-nop4", "-stdout", "-FullStdOutLogOutput",
             "-ExecCmds=py `"$scr`"")
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$p = Start-Process -FilePath $exe -ArgumentList $argList -PassThru -NoNewWindow `
     -RedirectStandardOutput $log -RedirectStandardError "$log.err"
if (-not $p.WaitForExit($TimeoutSec * 1000)) {
  Write-Output "TIMEOUT after $TimeoutSec s - killing"
  try { $p.Kill() } catch {}
}
$sw.Stop()
Write-Output "EXIT=$($p.ExitCode)  elapsed=$([math]::Round($sw.Elapsed.TotalSeconds))s"
if (Test-Path "$log.err") {
  $e = Get-Content "$log.err" -Raw
  if ($e) { Write-Output "--- stderr ---"; Write-Output $e }
}
if (Test-Path (Join-Path $logDir "playtest.txt")) {
  Write-Output "--- playtest.txt ---"
  Get-Content (Join-Path $logDir "playtest.txt")
} else {
  Write-Output "NO PLAYTEST OUTPUT"
}
