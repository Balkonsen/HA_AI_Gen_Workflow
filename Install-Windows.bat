@echo off
:: ============================================================================
:: Home Assistant AI Workflow - Windows Quick Installer
:: ============================================================================
:: This batch file provides an easy entry point for the PowerShell installer.
:: Just double-click this file to start the installation!
:: ============================================================================

title HA AI Workflow - Windows Installer

echo.
echo ============================================================================
echo   Home Assistant AI Workflow - Windows Installer
echo ============================================================================
echo.

:: Check if PowerShell is available
where powershell >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: PowerShell not found. Please install PowerShell first.
    pause
    exit /b 1
)

:: Check execution policy and run installer
echo Starting installation...
echo.

:: Run PowerShell installer with bypass for this script only
powershell -ExecutionPolicy Bypass -File "%~dp0install_windows.ps1" %*

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Installation completed successfully!
) else (
    echo.
    echo Installation encountered errors. Please check the log file.
)

echo.
pause
