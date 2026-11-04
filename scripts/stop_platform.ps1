# ==============================================================================
# REVOLT PLATFORM TEARDOWN — Graceful Shutdown Script
# ==============================================================================

Write-Host "Stopping ReVolt Platform services..." -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$pidFile = Join-Path $projectRoot ".revolt_pids.json"

if (Test-Path $pidFile) {
    try {
        $pids = Get-Content $pidFile | ConvertFrom-Json
        if ($pids.backend_pid) {
            Write-Host "Stopping Backend process (PID $($pids.backend_pid))..." -ForegroundColor Yellow
            Stop-Process -Id $pids.backend_pid -Force -ErrorAction SilentlyContinue
        }
        if ($pids.frontend_pid) {
            Write-Host "Stopping Frontend process (PID $($pids.frontend_pid))..." -ForegroundColor Yellow
            Stop-Process -Id $pids.frontend_pid -Force -ErrorAction SilentlyContinue
        }
        Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    } catch {
        Write-Host "Warning during PID cleanup: $_" -ForegroundColor DarkYellow
    }
}

# Cleanup any remaining processes listening on ports 8000 and 5173
try {
    $ports = @(8000, 5173)
    foreach ($port in $ports) {
        $netstatOut = netstat -ano | Select-String ":$port\s+.*LISTENING\s+(\d+)"
        foreach ($match in $netstatOut) {
            if ($match.Matches.Groups[1].Value) {
                $foundPid = [int]$match.Matches.Groups[1].Value
                Write-Host "Releasing port $port (Terminating PID $foundPid)..." -ForegroundColor Yellow
                Stop-Process -Id $foundPid -Force -ErrorAction SilentlyContinue
            }
        }
    }
} catch {
    # Ignore netstat/security permission errors in sandbox
}

Write-Host "ReVolt Platform stopped cleanly." -ForegroundColor Green

