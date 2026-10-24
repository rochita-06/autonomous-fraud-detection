# Autonomous Fraud Investigation System - One-Click Deployment Script
Set-Location $PSScriptRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  🛡️ Deploying Autonomous Fraud Investigation System      " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Check if Docker daemon is running
Write-Host "`n[1/4] Verifying Docker Desktop..." -ForegroundColor Yellow
$dockerReady = $false
try {
    docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $dockerReady = $true
    }
} catch {
    $dockerReady = $false
}

if (-not $dockerReady) {
    Write-Host "[!] Docker daemon is not running." -ForegroundColor Red
    Write-Host "    Please launch 'Docker Desktop' from your Windows Start Menu." -ForegroundColor White
    Write-Host "    Waiting for Docker engine to become ready (press Ctrl+C to cancel)..." -ForegroundColor Gray
    
    $attempts = 0
    while ($attempts -lt 40) {
        Start-Sleep -Seconds 3
        try {
            docker info 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                $dockerReady = $true
                break
            }
        } catch {}
        $attempts++
        Write-Host "." -NoNewline -ForegroundColor Gray
    }
    Write-Host ""
}

if (-not $dockerReady) {
    Write-Host "`n[ERROR] Docker engine did not respond in time." -ForegroundColor Red
    Write-Host "Please start Docker Desktop manually, wait until the Docker icon in the taskbar turns solid green/active, and re-run:" -ForegroundColor White
    Write-Host "    powershell -ExecutionPolicy Bypass -File .\deploy.ps1" -ForegroundColor Green
    exit 1
}

Write-Host "Docker is online and responsive!" -ForegroundColor Green

# 2. Check environment configuration
Write-Host "`n[2/4] Checking environment (.env)..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "Created .env from .env.example." -ForegroundColor Green
    } else {
        New-Item -ItemType File -Name ".env" | Out-Null
        Write-Host "Created empty .env file." -ForegroundColor Green
    }
} else {
    Write-Host ".env configuration loaded." -ForegroundColor Green
}

# 3. Build & start containers
Write-Host "`n[3/4] Building and launching containers via Docker Compose..." -ForegroundColor Yellow
docker compose up --build -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n[ERROR] Docker Compose failed to build or start containers." -ForegroundColor Red
    exit 1
}

# 4. Wait for services to become healthy
Write-Host "`n[4/4] Waiting for services to become healthy..." -ForegroundColor Yellow
$services = @("postgres", "neo4j", "backend", "frontend", "n8n")
$deadline = (Get-Date).AddMinutes(3)

while ((Get-Date) -lt $deadline) {
    $allHealthy = $true
    $statuses = docker compose ps --format json | ConvertFrom-Json
    
    foreach ($svc in $statuses) {
        $name = $svc.Service
        $state = $svc.Health
        if (-not $state) { $state = $svc.State }
        
        if ($state -ne "healthy" -and $state -ne "running") {
            $allHealthy = $false
        }
    }
    
    if ($allHealthy -and $statuses.Count -ge 4) {
        break
    }
    Start-Sleep -Seconds 4
    Write-Host "." -NoNewline -ForegroundColor Gray
}
Write-Host ""

# Summary
Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "  ✅ Deployment Complete! All Services Are Running:       " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  🌐 Frontend Dashboard:    http://localhost:3000" -ForegroundColor Cyan
Write-Host "  ⚙️ Backend API Docs:       http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  🧠 Neo4j Graph Browser:   http://localhost:7474 (user: neo4j / pass: fraudgraph)" -ForegroundColor Cyan
Write-Host "  🔁 n8n Automation:        http://localhost:5678" -ForegroundColor Cyan
Write-Host "  🐘 PostgreSQL:            localhost:5432 (user: fraud / pass: fraudpass / db: frauddb)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "View live logs anytime with:  docker compose logs -f" -ForegroundColor Yellow
Write-Host "Stop the deployment with:     docker compose down" -ForegroundColor Yellow
