@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Keine .venv gefunden. Fuehre zuerst install_windows.bat aus.
    pause
    exit /b 1
)

echo Pruefe PyTorch/CUDA in dieser Doclink-.venv...
".venv\Scripts\python.exe" -c "import sys; print('python:', sys.executable); import numpy; print('numpy:', numpy.__version__); import torch; print('torch:', torch.__version__); print('cuda build:', torch.version.cuda); print('cuda available:', torch.cuda.is_available()); print('gpu:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else '-')"

echo.
echo Wenn 'cuda available: False' steht, kann DocStrange local_gpu nicht laufen.
echo Wenn 'numpy: 2...' steht, install_docstrange_windows.bat erneut ausfuehren.
echo Dann install_docstrange_windows.bat erneut ausfuehren oder NVIDIA-Treiber aktualisieren.
pause
