# Launches the full Unreal Editor and captures the art pass.
#
#   .\art_90_shot.ps1
#
# A commandlet cannot screenshot: it has no tick loop and no render thread.
# This starts the real editor, runs art_90_shot.py through the console `py`
# command, and lets the script quit the editor when it is done.
param(
  [int]$TimeoutSec = 1500
)
$ErrorActionPreference = 'Continue'
$exe  = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
$proj = "C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\KhoangLang0217.uproject"
$dir  = "C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang"
$out  = "C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Saved\ArtShots"
$logDir = "C:\Users\phanb\AppData\Local\Temp\opencode\kl"
if (-not (Test-Path $out)) { New-Item -ItemType Directory -Path $out -Force | Out-Null }
$log = Join-Path $logDir "art_90_shot.log"
if (Test-Path $log) { Remove-Item $log -Force }
$script = (Join-Path $dir "art_90_shot.py") -replace '\\','/'

Get-Process -Name UnrealEditor -ErrorAction SilentlyContinue | ForEach-Object {
  Write-Output "NOTE: an editor is already running (pid $($_.Id))"
}

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $exe
# PowerShell 5.1 runs on .NET Framework, which has no ArgumentList, so the
# arguments go through the quoted Arguments string instead.
$psi.Arguments = ('"{0}" -ExecCmds="py {1}" -nosplash -NoLiveCoding -stdout ' -f $proj, $script) + `
                 '-FullStdOutLogOutput -log'
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
Write-Output "launching: $exe $($psi.Arguments)"
$proc = [System.Diagnostics.Process]::Start($psi)

$sw = [System.Diagnostics.Stopwatch]::StartNew()
$outTask = $proc.StandardOutput.ReadToEndAsync()
$errTask = $proc.StandardError.ReadToEndAsync()
while (-not $proc.HasExited -and $sw.Elapsed.TotalSeconds -lt $TimeoutSec) {
  Start-Sleep -Seconds 5
  $n = (Get-ChildItem -Path $out -Filter *.png -ErrorAction SilentlyContinue).Count
  Write-Output ("t={0,5:N0}s  shots={1}" -f $sw.Elapsed.TotalSeconds, $n)
}
if (-not $proc.HasExited) {
  Write-Output "TIMEOUT after $TimeoutSec s - killing editor"
  try { $proc.Kill() } catch {}
}
$sw.Stop()
[System.IO.File]::WriteAllText($log, $outTask.Result + "`n===STDERR===`n" + $errTask.Result)
Write-Output "EXIT=$($proc.ExitCode) elapsed=$([math]::Round($sw.Elapsed.TotalSeconds))s log=$log"
Get-ChildItem -Path $out -Filter *.png -ErrorAction SilentlyContinue |
  Select-Object Name, Length, LastWriteTime | Format-Table -AutoSize
exit 0
