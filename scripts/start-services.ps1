param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot

function Test-SalonService([string]$kind, [int]$port) {
    try {
        if ($kind -eq 'backend') {
            $schema = Invoke-RestMethod "http://127.0.0.1:$port/openapi.json" -TimeoutSec 3
            return $schema.info.title -eq 'AI Salon Commentator'
        }
        $page = Invoke-WebRequest "http://127.0.0.1:$port/" -UseBasicParsing -TimeoutSec 3
        return $page.Content -match '<title>AI Salon Commentator'
    } catch { return $false }
}

try {
    foreach ($service in @(@{kind='backend'; port=8000}, @{kind='frontend'; port=5173})) {
        $kind = $service.kind
        $port = $service.port
        if (Test-SalonService $kind $port) {
            Write-Host "Salon $kind is already running on port $port. Reusing it."
            continue
        }
        if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
            throw "Port $port is occupied by another or unresponsive service. Close it and retry. No process was terminated."
        }
        if ($kind -eq 'backend') {
            Start-Process -FilePath (Join-Path $projectRoot '.venv\Scripts\python.exe') -ArgumentList '-m uvicorn backend.main:app --host 127.0.0.1 --port 8000' -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $projectRoot '.tmp\backend.log') -RedirectStandardError (Join-Path $projectRoot '.tmp\backend-error.log') | Out-Null
        } else {
            Start-Process -FilePath (Get-Command node.exe).Source -ArgumentList 'node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173 --strictPort' -WorkingDirectory (Join-Path $projectRoot 'frontend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $projectRoot '.tmp\frontend.log') -RedirectStandardError (Join-Path $projectRoot '.tmp\frontend-error.log') | Out-Null
        }
        $ready = $false
        for ($attempt = 0; $attempt -lt 15; $attempt++) {
            if (Test-SalonService $kind $port) { $ready = $true; break }
            Start-Sleep -Milliseconds 300
        }
        if (-not $ready) { throw "Salon $kind did not start. Check .tmp/$kind-error.log." }
        Write-Host "Salon $kind started on port $port."
    }
    Write-Host 'Open http://127.0.0.1:5173'
    if (-not $NoBrowser) {
        try {
            Start-Process 'http://127.0.0.1:5173/'
        } catch {
            Write-Warning 'Services are ready, but Windows could not open the default browser. Open http://127.0.0.1:5173/ manually.'
        }
    }
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
