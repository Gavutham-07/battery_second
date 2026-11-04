@echo off
REM ==============================================================================
REM REVOLT PLATFORM LAUNCHER — Windows Batch Wrapper
REM ==============================================================================
TITLE ReVolt Platform Launcher
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_platform.ps1"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Platform failed to launch properly.
    pause
)

