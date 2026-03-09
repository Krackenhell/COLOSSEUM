$ErrorActionPreference = 'Stop'
$scriptDir = $PSScriptRoot
$rootDir = Split-Path $scriptDir -Parent

Write-Host "=== Starting COLOSSEUM Backend + Frontend ===" -ForegroundColor Cyan

# ── Backend ──
$backendDir = Join-Path $rootDir 'backend'

# Kill anything on port 8787
Get-NetTCPConnection -LocalPort 8787 -State Listen -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess -Unique |
  ForEach-Object { try { Stop-Process -Id $_ -Force -ErrorAction Stop } catch {} }

# Copy .env if missing
if (-not (Test-Path "$backendDir\.env")) {
    Copy-Item "$backendDir\.env.example" "$backendDir\.env"
    Write-Host "Created backend\.env from .env.example"
}

# Load .env
Get-Content "$backendDir\.env" | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($Matches[1].Trim(), $Matches[2].Trim(), 'Process')
    }
}

$env:PORT = "8787"
$env:COLOSSEUM_RELOAD = "0"

Write-Host "Starting backend on http://localhost:8787 ..." -ForegroundColor Green
$backendProc = Start-Process -FilePath "python" -ArgumentList "-m","app.main" `
    -WorkingDirectory $backendDir -PassThru -WindowStyle Hidden
Write-Host "Backend PID: $($backendProc.Id)"

Start-Sleep -Seconds 3

# ── Frontend (serve built dist for stability) ──
$frontendDir = Join-Path $rootDir 'frontend'

# Kill anything on port 8080
Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess -Unique |
  ForEach-Object { try { Stop-Process -Id $_ -Force -ErrorAction Stop } catch {} }

Push-Location $frontendDir
if (-not (Test-Path 'node_modules')) {
    Write-Host "Installing frontend dependencies..."
    npm install
}

# For preview mode, API calls go direct to backend (no vite proxy)
$env:VITE_API_BASE_URL = "http://localhost:8787"

# Build if dist is stale or missing
$needBuild = $false
if (-not (Test-Path 'dist\index.html')) { $needBuild = $true }
else {
    $distTime = (Get-Item 'dist\index.html').LastWriteTime
    $srcFiles = Get-ChildItem -Path 'src' -Recurse -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($srcFiles -and $srcFiles.LastWriteTime -gt $distTime) { $needBuild = $true }
}

if ($needBuild) {
    Write-Host "Building frontend..." -ForegroundColor Yellow
    npx vite build
}

Write-Host "Starting frontend preview on http://localhost:8080 ..." -ForegroundColor Green
$frontendProc = Start-Process -FilePath "npx" -ArgumentList "vite","preview","--port","8080","--host","0.0.0.0" `
    -WorkingDirectory $frontendDir -PassThru -WindowStyle Hidden
Write-Host "Frontend PID: $($frontendProc.Id)"
Pop-Location

Write-Host ""
Write-Host "=== COLOSSEUM Running ===" -ForegroundColor Cyan
Write-Host "  Backend:  http://localhost:8787"
Write-Host "  Frontend: http://localhost:8080"
Write-Host "  Press Ctrl+C to stop both."
Write-Host ""

# Wait and handle Ctrl+C
try {
    while (-not $backendProc.HasExited -and -not $frontendProc.HasExited) {
        Start-Sleep -Seconds 2
    }
    if ($backendProc.HasExited) { Write-Host "Backend exited with code $($backendProc.ExitCode)" -ForegroundColor Red }
    if ($frontendProc.HasExited) { Write-Host "Frontend exited with code $($frontendProc.ExitCode)" -ForegroundColor Red }
} finally {
    Write-Host "Stopping processes..." -ForegroundColor Yellow
    if (-not $backendProc.HasExited) { Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue }
    if (-not $frontendProc.HasExited) { Stop-Process -Id $frontendProc.Id -Force -ErrorAction SilentlyContinue }
}
