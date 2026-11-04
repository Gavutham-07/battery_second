# ==============================================================================
# REVOLT PLATFORM LAUNCHER — Automated Startup Script
# Smart EV Battery Assessment, Valuation and Circularity Platform
# ==============================================================================

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "                REVOLT PLATFORM LAUNCHER                              " -ForegroundColor Green
Write-Host "   Smart EV Battery Assessment, Valuation and Circularity Platform    " -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

# 1. Resolve Python executable
$pythonExe = Join-Path $projectRoot "venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}
Write-Host "[1/5] Using Python environment: $pythonExe" -ForegroundColor Yellow

# 2. Seed / Refresh Database Fixtures
Write-Host "[2/5] Seeding demonstration scenarios..." -ForegroundColor Yellow
& $pythonExe "scripts/seed_database.py"

# 3. Launch FastAPI Backend Service
Write-Host "[3/5] Starting FastAPI Backend on http://127.0.0.1:8000 ..." -ForegroundColor Yellow
$backendProcess = Start-Process -FilePath $pythonExe -ArgumentList "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000" -WorkingDirectory $projectRoot -PassThru

# 4. Launch Vite Frontend Service
Write-Host "[4/5] Starting Vite Frontend on http://localhost:5173 ..." -ForegroundColor Yellow
$frontendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "npm --prefix frontend run dev" -WorkingDirectory $projectRoot -PassThru

# Save process identifiers for stop_platform.ps1
$pidInfo = @{
    backend_pid = $backendProcess.Id
    frontend_pid = $frontendProcess.Id
    started_at = (Get-Date).ToString("o")
} | ConvertTo-Json

Set-Content -Path (Join-Path $projectRoot ".revolt_pids.json") -Value $pidInfo

# 5. Readiness Notification & Endpoint Directory
Start-Sleep -Seconds 2
Write-Host "`n[5/5] ReVolt Platform is ONLINE!" -ForegroundColor Green
Write-Host "----------------------------------------------------------------------" -ForegroundColor Gray
Write-Host " Web Portal:                http://localhost:5173" -ForegroundColor White
Write-Host " REST API & Swagger UI:     http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host " Backend Health:            http://127.0.0.1:8000/api/health" -ForegroundColor White
Write-Host " Demo Passport Check:       http://localhost:5173/verify/BAT-103" -ForegroundColor White
Write-Host "----------------------------------------------------------------------" -ForegroundColor Gray
Write-Host "To gracefully stop the platform, run: powershell -File scripts\stop_platform.ps1`n" -ForegroundColor Cyan

