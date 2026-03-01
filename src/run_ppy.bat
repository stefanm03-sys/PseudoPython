@echo off
setlocal

if "%~1"=="" (
  echo Usage: run_ppy.bat ^<file.ppy^>
  exit /b 1
)

for %%I in ("%~1") do set "PPY_FILE=%%~fI"
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
  py -3.12 main.py "%PPY_FILE%"
  if %errorlevel%==0 exit /b 0
)

where python >nul 2>nul
if %errorlevel%==0 (
  python main.py "%PPY_FILE%"
  exit /b %errorlevel%
)

echo Python not found. Install Python 3.x and ensure py or python is on PATH.
exit /b 1
