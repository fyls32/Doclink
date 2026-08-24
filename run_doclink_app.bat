@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    call install_windows.bat
)

set HF_HUB_DISABLE_SYMLINKS=1
set HF_HUB_DISABLE_SYMLINKS_WARNING=1

".venv\Scripts\python.exe" doclink_app.py
