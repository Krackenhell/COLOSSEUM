$ErrorActionPreference = 'Stop'
$port = 8787

Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess -Unique |
  ForEach-Object {
    try { Stop-Process -Id $_ -Force -ErrorAction Stop } catch {}
  }

$env:PORT = "$port"
$env:COLOSSEUM_RELOAD = "0"
python -m app.main
