<#
.SYNOPSIS
  Stable review launcher for COLOSSEUM — backend + frontend with self-healing.
.DESCRIPTION
  - Kills stale processes on ports 8787/8080
  - Starts backend with log file and health-check
  - Builds frontend if needed, serves via vite preview
  - Monitors both processes and restarts on crash
.USAGE
  powershell -ExecutionPolicy Bypass -File scripts\start-review.ps1
#>

$ErrorActionPreference = 'Continue'
$rootDir = Split-Path $PSScriptRoot -Parent
$backendDir = Join-Path $rootDir 'backend'
$frontendDir = Join-Path $rootDir 'frontend'
$logsDir = Join-Path $rootDir 'logs'

if (-not (Test-Path $logsDir)) { New-Item -ItemType Directory -Path $logsDir -Force | Out-Null }

$backendLog = Join-Path $logsDir "backend.log"
$frontendLog = Join-Path $logsDir "frontend.log"

function Kill-Port($port) {
    Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique |
        ForEach-Object { try { Stop-Process -Id $_ -Force -ErrorAction Stop; Write-Host "  Killed PID $_ on port $port" } catch {} }
}

function Wait-Health($url, $timeoutSec = 30) {
    $end = (Get-Date).AddSeconds($timeoutSec)
    while ((Get-Date) -lt $end) {
        try {
            $r = Invoke-RestMethod -Uri $url -TimeoutSec 3 -ErrorAction Stop
            if ($r.status -eq 'ok') { return $true }
        } catch {}
        Start-Sleep -Seconds 1
    }
    return $false
}

function Start-Backend {
    Write-Host "`n[Backend] Starting..." -ForegroundColor Green

    Kill-Port 8787
    Start-Sleep -Seconds 1

    # Load .env
    if (-not (Test-Path "$backendDir\.env")) {
        if (Test-Path "$backendDir\.env.example") {
            Copy-Item "$backendDir\.env.example" "$backendDir\.env"
            Write-Host "  Created .env from .env.example"
        }
    }
    if (Test-Path "$backendDir\.env") {
        Get-Content "$backendDir\.env" | ForEach-Object {
            if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
                [Environment]::SetEnvironmentVariable($Matches[1].Trim(), $Matches[2].Trim(), 'Process')
            }
        }
    }

    $env:PORT = "8787"
    $env:COLOSSEUM_RELOAD = "0"

    # Clear old log
    "" | Set-Content $backendLog

    $proc = Start-Process -FilePath "python" -ArgumentList "-m","app.main" `
        -WorkingDirectory $backendDir -PassThru -WindowStyle Hidden `
        -RedirectStandardOutput $backendLog -RedirectStandardError (Join-Path $logsDir "backend_err.log")

    Write-Host "  PID: $($proc.Id)"

    if (Wait-Health "http://localhost:8787/health" 20) {
        Write-Host "  [OK] Backend healthy on http://localhost:8787" -ForegroundColor Green
    } else {
        Write-Host "  [WARN] Backend not healthy yet — may still be starting" -ForegroundColor Yellow
        if ($proc.HasExited) {
            Write-Host "  [ERROR] Backend exited with code $($proc.ExitCode). Check $backendLog" -ForegroundColor Red
            Get-Content (Join-Path $logsDir "backend_err.log") -Tail 20 -ErrorAction SilentlyContinue
        }
    }
    return $proc
}

function Start-Frontend {
    Write-Host "`n[Frontend] Starting..." -ForegroundColor Green

    Kill-Port 8080
    Start-Sleep -Seconds 1

    Push-Location $frontendDir
    if (-not (Test-Path 'node_modules')) {
        Write-Host "  Installing dependencies..."
        npm install 2>&1 | Out-Null
    }

    # In preview mode, VITE_API_BASE_URL must point to backend (no vite proxy)
    $env:VITE_API_BASE_URL = "http://localhost:8787"

    # Build if needed
    $needBuild = $false
    if (-not (Test-Path 'dist\index.html')) { $needBuild = $true }
    else {
        $distTime = (Get-Item 'dist\index.html').LastWriteTime
        $srcFiles = Get-ChildItem -Path 'src' -Recurse -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($srcFiles -and $srcFiles.LastWriteTime -gt $distTime) { $needBuild = $true }
    }

    if ($needBuild) {
        Write-Host "  Building frontend (this may take a minute)..." -ForegroundColor Yellow
        npx vite build 2>&1 | Out-Null
        if (-not (Test-Path 'dist\index.html')) {
            Write-Host "  [ERROR] Frontend build failed!" -ForegroundColor Red
            Pop-Location
            return $null
        }
        Write-Host "  Build complete."
    }

    $proc = Start-Process -FilePath "npx" -ArgumentList "vite","preview","--port","8080","--host","0.0.0.0" `
        -WorkingDirectory $frontendDir -PassThru -WindowStyle Hidden `
        -RedirectStandardOutput $frontendLog -RedirectStandardError (Join-Path $logsDir "frontend_err.log")

    Write-Host "  PID: $($proc.Id)"
    Start-Sleep -Seconds 3
    Write-Host "  [OK] Frontend on http://localhost:8080" -ForegroundColor Green
    Pop-Location
    return $proc
}

# ═══════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════
Write-Host "╔══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   COLOSSEUM — Stable Review Mode     ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════╝" -ForegroundColor Cyan

$backendProc = Start-Backend
$frontendProc = Start-Frontend

Write-Host ""
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Backend:  http://localhost:8787"
Write-Host "  Frontend: http://localhost:8080"
Write-Host "  Logs:     $logsDir"
Write-Host "  Press Ctrl+C to stop."
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# ── Watch loop with auto-restart ──
$backendRestarts = 0
$maxRestarts = 5

try {
    while ($true) {
        Start-Sleep -Seconds 5

        # Check backend
        if ($backendProc -and $backendProc.HasExited) {
            $backendRestarts++
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Backend died (exit $($backendProc.ExitCode)), restart $backendRestarts/$maxRestarts" -ForegroundColor Red
            if ($backendRestarts -le $maxRestarts) {
                Start-Sleep -Seconds 2
                $backendProc = Start-Backend
            } else {
                Write-Host "[FATAL] Backend exceeded max restarts. Check logs: $backendLog" -ForegroundColor Red
                break
            }
        }

        # Check frontend
        if ($frontendProc -and $frontendProc.HasExited) {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Frontend died, restarting..." -ForegroundColor Yellow
            $frontendProc = Start-Frontend
        }
    }
} finally {
    Write-Host "`nStopping all processes..." -ForegroundColor Yellow
    if ($backendProc -and -not $backendProc.HasExited) { Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue }
    if ($frontendProc -and -not $frontendProc.HasExited) { Stop-Process -Id $frontendProc.Id -Force -ErrorAction SilentlyContinue }
    Kill-Port 8787
    Kill-Port 8080
    Write-Host "Done." -ForegroundColor Green
}
