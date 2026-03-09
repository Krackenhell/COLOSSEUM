$ErrorActionPreference = 'Stop'
$port = 8787

Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess -Unique |
  ForEach-Object {
    try { Stop-Process -Id $_ -Force -ErrorAction Stop } catch {}
  }

$env:PORT = "$port"
$env:COLOSSEUM_RELOAD = "0"
$env:MARKET_SOURCE = "chainlink"
$env:CHAINLINK_RPC_URL = "https://avax-mainnet.g.alchemy.com/v2/6evpjOd1KcH2a5Qra3FtceXxeajc-GoH"
$env:CHAINLINK_CACHE_TTL_SEC = "10"
$env:CHAINLINK_MAX_STALENESS_SEC = "3600"

python -m uvicorn app.main:app --app-dir "C:\Users\Administrator\.openclaw\workspace\colosseum-new-version\COLOSSEUM" --host 127.0.0.1 --port $port
