@echo off
setlocal
cd /d "%~dp0"
if not exist .tmp mkdir .tmp
set "TEMP=%~dp0.tmp"
set "TMP=%~dp0.tmp"
where python >nul 2>nul || (echo Install Python 3.11+ and add it to PATH. & pause & exit /b 1)
where node >nul 2>nul || (echo Install Node.js 20.19+ or 22.12+. & pause & exit /b 1)
python -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)"
if errorlevel 1 (echo Python 3.11 or newer is required. & pause & exit /b 1)
node -e "const [a,b]=process.versions.node.split('.').map(Number);process.exit(a===20?b>=19?0:1:a===22?b>=12?0:1:a>22?0:1)"
if errorlevel 1 (echo Node.js 20.19+ or 22.12+ LTS is required. & pause & exit /b 1)
if not exist .venv\Scripts\python.exe python -m venv .venv
if errorlevel 1 goto failed
.venv\Scripts\python.exe -m pip --version >nul 2>nul || .venv\Scripts\python.exe -m ensurepip --upgrade
if errorlevel 1 goto failed
.venv\Scripts\python.exe -m pip install --disable-pip-version-check -r backend\requirements-lock.txt
if errorlevel 1 goto failed
if not exist .env copy .env.example .env >nul
pushd frontend
if exist node_modules\.package-lock.json (call npm install --prefer-offline --no-audit --no-fund) else (call npm ci --no-audit --no-fund)
if errorlevel 1 (popd & goto failed)
popd
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start-services.ps1"
if errorlevel 1 goto service_failed
echo Ready. The default browser has been requested to open the console.
echo If AI services report a missing key, configure .env and restart the backend.
pause
exit /b 0
:failed
echo Dependency installation failed. Check your network and the message above.
pause
exit /b 1
:service_failed
echo Service startup failed. See the specific message above and logs in .tmp.
pause
exit /b 1
