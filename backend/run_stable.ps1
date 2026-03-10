$ErrorActionPreference = 'Continue'
$port = 8787

Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess -Unique |
  ForEach-Object {
    try { Stop-Process -Id $_ -Force -ErrorAction Stop } catch {}
  }

$env:PORT = "$port"
$env:COLOSSEUM_RELOAD = "0"

$restarts = 0
$maxRestarts = 5

while ($restarts -le $maxRestarts) {
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Starting backend on port $port (attempt $($restarts + 1))..." -ForegroundColor Green
    python -m app.main
    $exitCode = $LASTEXITCODE
    $restarts++
    if ($restarts -le $maxRestarts) {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Backend exited ($exitCode), restarting in 3s... ($restarts/$maxRestarts)" -ForegroundColor Yellow
        Start-Sleep -Seconds 3
    } else {
        Write-Host "[FATAL] Backend exceeded max restarts." -ForegroundColor Red
    }
}
