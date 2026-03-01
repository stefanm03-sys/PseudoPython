@echo off
cd /d "%~dp0"

set "PPY_FILE=..\pseudo.ppy"
if not exist "%PPY_FILE%" set "PPY_FILE=pseudo.ppy"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py "%PPY_FILE%"
    goto :done
)

where py >nul 2>nul
if %errorlevel%==0 (
    py -3.12 main.py "%PPY_FILE%"
    if %errorlevel%==0 goto :done
)

where python >nul 2>nul
if %errorlevel%==0 (
    python main.py "%PPY_FILE%"
    if %errorlevel%==0 goto :done
)

echo Could not run PseudoPy with .venv, py -3.12, or python.
echo Check your Python installation and PATH, then reopen terminal/VS Code.

:done
pause
