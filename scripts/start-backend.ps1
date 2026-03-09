$ErrorActionPreference = 'Stop'
$port = 8787

# Kill anything on port 8787
Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess -Unique |
  ForEach-Object {
    try { Stop-Process -Id $_ -Force -ErrorAction Stop } catch {}
  }

# Copy .env if missing
$backendDir = Join-Path $PSScriptRoot '..\backend'
if (-not (Test-Path "$backendDir\.env")) {
    Copy-Item "$backendDir\.env.example" "$backendDir\.env"
    Write-Host "Created backend\.env from .env.example — edit it if needed."
}

# Load .env
Get-Content "$backendDir\.env" | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($Matches[1].Trim(), $Matches[2].Trim(), 'Process')
    }
}

$env:PORT = "$port"
$env:COLOSSEUM_RELOAD = "0"

Push-Location $backendDir
python -m app.main
Pop-Location
