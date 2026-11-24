$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { throw 'Run start.bat once to install development dependencies.' }
Push-Location frontend
try {
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
} finally { Pop-Location }
& $python -m pip install 'pyinstaller>=6.11,<7'
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller installation failed.' }
$ffmpeg = (& $python -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())').Trim()
New-Item -ItemType Directory -Force .tmp\portable-tools | Out-Null
Copy-Item -LiteralPath $ffmpeg -Destination .tmp\portable-tools\ffmpeg.exe -Force
& $python -m PyInstaller --noconfirm --clean --onedir --console --name AI-Salon-Commentator --distpath release --workpath .tmp\pyinstaller --specpath .tmp --paths $projectRoot --add-data "$projectRoot/frontend/dist;frontend/dist" --add-data "$projectRoot/backend/prompts;backend/prompts" --add-binary "$projectRoot/.tmp/portable-tools/ffmpeg.exe;tools" --collect-data imageio_ffmpeg --collect-submodules uvicorn --collect-all certifi portable.py
if ($LASTEXITCODE -ne 0) { throw 'Portable EXE build failed.' }
$output = Join-Path $projectRoot 'release\AI-Salon-Commentator'
Copy-Item .env.example (Join-Path $output '.env') -Force
Copy-Item PORTABLE-README.txt $output -Force
& $python scripts/package-release.py
if ($LASTEXITCODE -ne 0) { throw 'ZIP creation failed.' }
Write-Host "Built: $output"
Write-Host 'The real .env/API key was NOT copied. Zip this entire folder for distribution.'

