@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    call install_windows.bat
)

".venv\Scripts\python.exe" doclink_app.py
