@echo off
cd /d "%~dp0"
set "PROJECT_PYTHON=python"
set "NO_PROXY=localhost,127.0.0.1"
set "no_proxy=localhost,127.0.0.1"
if exist "%~dp0..\.venv\Scripts\python.exe" set "PROJECT_PYTHON=%~dp0..\.venv\Scripts\python.exe"
if exist "%~dp0.venv\Scripts\python.exe" set "PROJECT_PYTHON=%~dp0.venv\Scripts\python.exe"
"%PROJECT_PYTHON%" -B -X utf8 demo_fti.py  %*
pause
