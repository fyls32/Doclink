@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    call install_windows.bat
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pyinstaller
pyinstaller --noconfirm --windowed --name Doclink ^
    --hidden-import=docling ^
    --hidden-import=rapidocr_onnxruntime ^
    --hidden-import=easyocr ^
    --hidden-import=pypdfium2 ^
    --hidden-import=pypdf ^
    --hidden-import=docx ^
    --hidden-import=bs4 ^
    --hidden-import=openpyxl ^
    --hidden-import=pptx ^
    doclink_app.py

echo.
echo Fertig. Die EXE liegt unter dist\Doclink\Doclink.exe
pause
