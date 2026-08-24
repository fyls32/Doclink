@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    call install_windows.bat
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
echo.
echo Installiere optionale Vision-Modelle fuer Bildtexte und Bildbeschreibungen.
echo Das kann lange dauern und mehrere GB Speicher benoetigen.
python -m pip install -r requirements-vision.txt

echo.
echo Fertig. Starte danach run_doclink_app.bat und aktiviere "Bildtexte per VLM".
pause
