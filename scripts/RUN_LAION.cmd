@echo off
cd /d "%~dp0.."
set "PROJECT_PYTHON=python"
set "NO_PROXY=localhost,127.0.0.1"
set "no_proxy=localhost,127.0.0.1"
if exist "%CD%\.venv\Scripts\python.exe" set "PROJECT_PYTHON=%CD%\.venv\Scripts\python.exe"
"%PROJECT_PYTHON%" -B -X utf8 -m lincir.data.prepare_laion
if errorlevel 1 goto done
"%PROJECT_PYTHON%" -B -X utf8 -m lincir.apps.demo_fti --source laion %*
:done
pause
