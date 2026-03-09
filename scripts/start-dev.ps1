# Development mode: backend + vite dev server with HMR and proxy
$ErrorActionPreference = 'Stop'
$scriptDir = $PSScriptRoot

Write-Host "=== COLOSSEUM Dev Mode ===" -ForegroundColor Cyan

# Start backend in background
$backendProc = Start-Process powershell -ArgumentList "-File","$scriptDir\start-backend.ps1" -PassThru -WindowStyle Minimized
Write-Host "Backend starting (PID: $($backendProc.Id))..."
Start-Sleep -Seconds 3

# Start frontend dev server in foreground
Write-Host "Frontend dev server on http://localhost:8080 ..."
& "$scriptDir\start-frontend.ps1"
