# Runs an UnrealEditor-Cmd python build script headless.
#   .\run_ue_script.ps1 probe_02.py
param(
  [Parameter(Mandatory = $true)][string]$Script,
  [int]$TimeoutSec = 1800
)
$ErrorActionPreference = 'Continue'
$exe  = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
$proj = "C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\KhoangLang0217.uproject"
$dir  = "C:\Users\phanb\Documents\Unreal Projects\KhoangLang0217\Content\Python\KhoangLang"
$logDir = "C:\Users\phanb\AppData\Local\Temp\opencode\kl"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }

$base = [System.IO.Path]::GetFileNameWithoutExtension($Script)
$scr  = Join-Path $dir $Script
$log  = Join-Path $logDir "$base.log"
if (Test-Path $log) { Remove-Item $log -Force }

if (-not (Test-Path $scr)) { Write-Output "MISSING SCRIPT: $scr"; exit 2 }

$argList = @($proj, "-run=pythonscript", "-script=$scr", "-unattended", "-nullrhi",
             "-nosplash", "-nop4", "-stdout", "-FullStdOutLogOutput")
$sw = [System.Diagnostics.Stopwatch]::StartNew()
& $exe @argList 2>&1 | Out-File -FilePath $log -Encoding utf8
$code = $LASTEXITCODE
$sw.Stop()
Write-Output "EXIT=$code  elapsed=$([math]::Round($sw.Elapsed.TotalSeconds))s  log=$log"
exit $code
