@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %ERRORLEVEL%==0 (
    py -3 -m venv .venv
) else (
    python -m venv .venv
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\create_shortcut.ps1"

echo.
echo Doclink ist installiert. Starte die App mit run_doclink_app.bat
pause
