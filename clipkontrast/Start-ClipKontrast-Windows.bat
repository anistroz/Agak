@echo off
title ClipKontrast
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start-windows.ps1"
echo.
echo   ClipKontrast has stopped. Press any key to close this window.
pause >nul
