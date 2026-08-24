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
set HF_HUB_DISABLE_SYMLINKS=1
set HF_HUB_DISABLE_SYMLINKS_WARNING=1

python -m pip install --upgrade pip
echo.
echo Installiere Docling und Dokument-Abhaengigkeiten. Der erste Lauf kann ein paar Minuten dauern.
python -m pip uninstall -y opencv-python
python -m pip install -r requirements.txt
python -m pip install --upgrade --force-reinstall "numpy<2.0.0"

powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\create_shortcut.ps1"

echo.
echo Doclink ist installiert. Starte die App mit run_doclink_app.bat
pause
