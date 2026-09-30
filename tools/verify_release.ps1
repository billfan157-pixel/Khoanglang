$ErrorActionPreference = 'Stop'
# Keep all verification options in the Python CLI; forward them unchanged.
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { throw 'Python 3 is required; no installation is attempted.' }
& $python.Source (Join-Path $PSScriptRoot 'verify_release.py') @args
exit $LASTEXITCODE
