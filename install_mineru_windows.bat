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
echo Installiere MinerU. Das ist gross und kann lange dauern.
echo Hinweis: MinerU unterstuetzt Windows aktuell am besten mit Python 3.10 bis 3.12.
python -m pip install --upgrade pip uv
uv pip install -U "mineru[all]"

echo.
echo Fertig. Starte danach run_doclink_app.bat und waehle Markdown-Modus "mineru".
pause
