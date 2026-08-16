$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path (Split-Path -Parent $root) '.venv_week3\Scripts\python.exe'
if (-not (Test-Path $python)) { throw "Python environment not found: $python" }
& $python (Join-Path $PSScriptRoot 'prepare_week1_demo.py')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Week 1 demo data is ready." -ForegroundColor Green
