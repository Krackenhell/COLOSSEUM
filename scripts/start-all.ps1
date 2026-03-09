$ErrorActionPreference = 'Stop'
$scriptDir = $PSScriptRoot

Write-Host "=== Starting COLOSSEUM Backend + Frontend ===" -ForegroundColor Cyan

# Start backend in background job
$backendJob = Start-Job -ScriptBlock {
    param($script)
    & $script
} -ArgumentList "$scriptDir\start-backend.ps1"

Write-Host "Backend starting on http://localhost:8787 ..."

# Wait a moment for backend
Start-Sleep -Seconds 3

# Start frontend in foreground
Write-Host "Frontend starting on http://localhost:8080 ..."
& "$scriptDir\start-frontend.ps1"
