$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path (Split-Path -Parent $root) '.venv_week3\Scripts\python.exe'
if (-not (Test-Path $python)) { throw "Python environment not found: $python" }
& $python (Join-Path $PSScriptRoot 'run_production_model_demo_smoke.py')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Real local BERT/MobileCLIP demo smoke passed." -ForegroundColor Green
