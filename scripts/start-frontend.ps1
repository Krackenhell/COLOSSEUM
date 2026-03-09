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

Write-Host "Starting frontend on http://localhost:8080 ..."
npx vite --port 8080

Pop-Location
