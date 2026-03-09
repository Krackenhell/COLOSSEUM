$ErrorActionPreference = 'Stop'
$frontendDir = Join-Path $PSScriptRoot '..\frontend'

Push-Location $frontendDir

# Install deps if needed
if (-not (Test-Path 'node_modules')) {
    Write-Host "Installing frontend dependencies..."
    npm install
}

# Copy .env if missing (empty VITE_API_BASE_URL = use proxy)
if (-not (Test-Path '.env')) {
    Copy-Item '.env.example' '.env'
}

# Use --mode flag to choose:
#   Default (no flag): Vite dev server with HMR (hot module replacement)
#   --stable:          Build + vite preview (no HMR, production-like, more stable)
$stable = $args -contains '--stable'

if ($stable) {
    Write-Host "Building frontend for stable preview mode..." -ForegroundColor Yellow
    $env:VITE_API_BASE_URL = "http://localhost:8787"
    npx vite build
    Write-Host "Starting frontend (stable preview) on http://localhost:8080 ..."
    npx vite preview --port 8080 --host 0.0.0.0
} else {
    Write-Host "Starting frontend (dev/HMR) on http://localhost:8080 ..."
    npx vite --port 8080
}

Pop-Location
