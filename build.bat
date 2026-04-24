@echo off
echo Building DHTV Brander Pro EXE...
".\venv\Scripts\pyinstaller" --onefile --noconsole --name "DHTV_Brander_Pro" ui.py
echo Build complete.
pause
