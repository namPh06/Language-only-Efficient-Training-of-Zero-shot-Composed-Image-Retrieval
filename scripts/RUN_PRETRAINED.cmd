@echo off
cd /d "%~dp0.."
set "PROJECT_PYTHON=python"
if exist "%CD%\..\.venv\Scripts\python.exe" set "PROJECT_PYTHON=%CD%\..\.venv\Scripts\python.exe"
if exist "%CD%\.venv\Scripts\python.exe" set "PROJECT_PYTHON=%CD%\.venv\Scripts\python.exe"
"%PROJECT_PYTHON%" -B -X utf8 -m lincir.apps.run_pretrained %*
pause
