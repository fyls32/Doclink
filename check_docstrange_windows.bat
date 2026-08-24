@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Keine .venv gefunden. Fuehre zuerst install_windows.bat aus.
    pause
    exit /b 1
)

set HF_HUB_DISABLE_SYMLINKS=1
set HF_HUB_DISABLE_SYMLINKS_WARNING=1

echo Pruefe DocStrange local_gpu in dieser Doclink-.venv...
".venv\Scripts\python.exe" -c "import numpy, torch; print('numpy:', numpy.__version__); print('torch:', torch.__version__); print('cuda build:', torch.version.cuda); print('cuda available:', torch.cuda.is_available()); print('gpu:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else '-'); from docstrange import DocumentExtractor; print('starte DocumentExtractor(gpu=True)...'); DocumentExtractor(gpu=True); print('DocStrange local_gpu startet korrekt.')"

echo.
echo Wenn oben ein Traceback steht, ist CUDA zwar sichtbar, aber DocStrange scheitert an diesem konkreten Fehler.
pause
