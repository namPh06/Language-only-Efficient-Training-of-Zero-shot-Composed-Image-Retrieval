@echo off
cd /d "%~dp0"
set "PROJECT_PYTHON=python"
if exist "%~dp0..\.venv\Scripts\python.exe" set "PROJECT_PYTHON=%~dp0..\.venv\Scripts\python.exe"
if exist "%~dp0.venv\Scripts\python.exe" set "PROJECT_PYTHON=%~dp0.venv\Scripts\python.exe"
"%PROJECT_PYTHON%" -B -X utf8 benchmark_circo.py  %*
pause
