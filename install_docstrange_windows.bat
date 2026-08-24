@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    call install_windows.bat
)

call ".venv\Scripts\activate.bat"
set HF_HUB_DISABLE_SYMLINKS=1
set HF_HUB_DISABLE_SYMLINKS_WARNING=1

echo.
echo Installiere DocStrange fuer lokale Verarbeitung.
echo Hinweis: Local CPU kann langsam sein. Local GPU benoetigt eine funktionierende CUDA-Installation.
python -m pip install --upgrade pip
python -m pip install -U docstrange

echo.
echo Fertig. Starte danach run_doclink_app.bat und waehle Markdown-Modus "docstrange".
pause
