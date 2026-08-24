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
echo Hinweis: DocStrange lokal benoetigt fuer Nanonets OCR eine funktionierende CUDA/PyTorch-Installation.
python -m pip install --upgrade pip
python -m pip install -U docstrange

if "%PYTORCH_CUDA_INDEX%"=="" (
    set PYTORCH_CUDA_INDEX=https://download.pytorch.org/whl/cu121
)

echo.
echo Installiere CUDA-faehiges PyTorch in diese .venv.
echo Index: %PYTORCH_CUDA_INDEX%
python -m pip install --upgrade --force-reinstall torch torchvision torchaudio --index-url "%PYTORCH_CUDA_INDEX%"

echo.
echo Setze NumPy zurueck auf 1.x, weil Docling/DocStrange-Modelle aktuell kein NumPy 2.x moegen.
python -m pip uninstall -y opencv-python
python -m pip install --upgrade --force-reinstall "numpy<2.0.0" "opencv-python-headless<5"

echo.
echo Pruefe CUDA in dieser .venv...
python -c "import numpy, torch; print('numpy:', numpy.__version__); print('torch:', torch.__version__); print('cuda build:', torch.version.cuda); print('cuda available:', torch.cuda.is_available()); print('gpu:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else '-')"

echo.
echo Fertig. Starte danach run_doclink_app.bat und waehle Markdown-Modus "docstrange".
pause
