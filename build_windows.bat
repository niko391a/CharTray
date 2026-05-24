@echo off
echo Installing dependencies...
pip install pystray pillow pyperclip keyboard pyinstaller

echo.
echo Building CharTray.exe...
python -m PyInstaller --onefile --windowed --name CharTray --hidden-import pystray._win32 chartray.py

echo.
echo Done! Your exe is in the dist\ folder.
pause