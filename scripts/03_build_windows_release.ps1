$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$projectRoot = Split-Path -Parent $root
$flutter = Join-Path $projectRoot 'dev_env\flutter\bin\flutter.bat'
$app = Join-Path $root 'app\offline_retrieval_ui'
$source = Join-Path $app 'build\windows\x64\runner\Release'
$release = Join-Path $root 'release\windows'
$client = Join-Path $release 'offline_retrieval_ui'
if (-not (Test-Path $flutter)) { throw "Flutter SDK not found: $flutter" }
Push-Location $app
try {
  & $flutter pub get --offline
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  & $flutter analyze
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  & $flutter build windows --release
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally { Pop-Location }
New-Item -ItemType Directory -Path $client -Force | Out-Null
Copy-Item (Join-Path $source '*') $client -Recurse -Force
Copy-Item (Join-Path $root 'run_backend.py') $release -Force
Copy-Item (Join-Path $root 'src') $release -Recurse -Force
foreach ($name in @('LICENSE','NOTICE','THIRD_PARTY_NOTICES.md','MODEL_AND_DATA_LICENSES.md')) { Copy-Item (Join-Path $root $name) $release -Force }
New-Item -ItemType Directory -Path (Join-Path $release 'data') -Force | Out-Null
Write-Host "Windows release built at $release" -ForegroundColor Green
