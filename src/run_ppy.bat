@echo off
setlocal
cd /d "%~dp0"

if "%~1"=="" (
  echo Usage: run_ppy.bat ^<file.ppy^>
  exit /b 1
)

where py >nul 2>nul
if %errorlevel%==0 (
  py main.py "%~1"
  exit /b %errorlevel%
)

where python >nul 2>nul
if %errorlevel%==0 (
  python main.py "%~1"
  exit /b %errorlevel%
)

echo Python not found. Install Python 3.x and ensure py or python is on PATH.
exit /b 1
