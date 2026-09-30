# Launches the full Unreal Editor and captures the school furniture shots.
#
#   .\art_96_schoolfurn_shot.ps1
#
# A commandlet cannot screenshot: no tick loop, no render thread. This starts
# the real editor, runs art_96_schoolfurn_shot.py through the console `py`
# command, and lets the script quit the editor when it is done.
#
# -unattended is deliberate: the script adds a temporary camera to two maps and
# deliberately does NOT save them, and unattended is what makes the editor exit
# on quit_editor() without a save prompt. Nothing on disk changes.
param(
  [int]$TimeoutSec = 2400
)
$ErrorActionPreference = 'Continue'
$exe  = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
$proj = "C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\KhoangLang0217.uproject"
$dir  = "C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang"
$out  = "C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Saved\FurnitureShots"
$logDir = "C:\Users\phanb\AppData\Local\Temp\opencode\kl"
if (-not (Test-Path $out)) { New-Item -ItemType Directory -Path $out -Force | Out-Null }
$log = Join-Path $logDir "art_96_schoolfurn_shot.log"
if (Test-Path $log) { Remove-Item $log -Force }
$script = (Join-Path $dir "art_96_schoolfurn_shot.py") -replace '\\','/'

Get-Process -Name UnrealEditor -ErrorAction SilentlyContinue | ForEach-Object {
  Write-Output "NOTE: an editor is already running (pid $($_.Id))"
}

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $exe
$psi.Arguments = ('"{0}" -ExecCmds="py {1}" -unattended -nosplash -NoLiveCoding ' -f $proj, $script) + `
                 '-stdout -FullStdOutLogOutput -log'
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
Write-Output "launching: $exe $($psi.Arguments)"
$proc = [System.Diagnostics.Process]::Start($psi)

$sw = [System.Diagnostics.Stopwatch]::StartNew()
$outTask = $proc.StandardOutput.ReadToEndAsync()
$errTask = $proc.StandardError.ReadToEndAsync()
while (-not $proc.HasExited -and $sw.Elapsed.TotalSeconds -lt $TimeoutSec) {
  Start-Sleep -Seconds 10
  $n = (Get-ChildItem -Path $out -Filter *.png -ErrorAction SilentlyContinue).Count
  Write-Output ("t={0,5:N0}s  shots={1}" -f $sw.Elapsed.TotalSeconds, $n)
}
if (-not $proc.HasExited) {
  Write-Output "TIMEOUT after $TimeoutSec s - killing editor"
  try { $proc.Kill() } catch {}
  Start-Sleep -Seconds 5
}
$sw.Stop()
[System.IO.File]::WriteAllText($log, $outTask.Result + "`n===STDERR===`n" + $errTask.Result)
Write-Output "EXIT=$($proc.ExitCode) elapsed=$([math]::Round($sw.Elapsed.TotalSeconds))s log=$log"
Get-ChildItem -Path $out -Filter *.png -ErrorAction SilentlyContinue |
  Select-Object Name, Length, LastWriteTime | Format-Table -AutoSize
exit 0
