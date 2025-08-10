@echo off
REM Superset Post Monitor - Startup Version
REM This version is optimized for Windows startup (no pauses, minimal output)

REM Change to the directory where this batch file is located
cd /d "%~dp0"

REM Start the monitor with auto-start flag
start /min "" python superset_gui_monitor.py --auto-start

REM Exit immediately
exit /b 0