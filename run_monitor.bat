@echo off
REM Change to the directory where this batch file is located
cd /d "%~dp0"

echo Starting Superset Post Monitor...
echo Working directory: %CD%
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    if not "%1"=="--auto-start" pause
    exit /b 1
)

REM Install requirements if needed (skip if auto-starting)
if not "%1"=="--auto-start" (
    echo Checking and installing required packages...
    pip install -r requirements.txt
)

REM Create icon if it doesn't exist
if not exist "notification-bell.png" (
    echo Creating application icon...
    python create_icon.py
)

REM Run the monitor
echo.
echo Starting the GUI application...
if "%1"=="--auto-start" (
    python superset_gui_monitor.py --auto-start
) else (
    python superset_gui_monitor.py
)

REM Only pause if not auto-starting
if not "%1"=="--auto-start" pause