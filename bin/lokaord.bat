@echo off
SETLOCAL

REM Usage:
REM lokaord -h

set PYTHONDONTWRITEBYTECODE=1

for /f "tokens=2 delims= " %%i in ('python --version') do set v=%%i

for /f "tokens=1,2 delims=." %%j in ("%v%") do (
    if %%j LSS 3 (
        echo Python 3.10 or higher is required
        exit /B
    )
    if %%j EQU 3 (
        if %%k LSS 10 (
            echo Python 3.10 or higher is required
            exit /B
        )
    )
)

cd /d %~dp0..

python main.py %*
