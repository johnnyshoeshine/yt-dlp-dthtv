@echo off
echo Building DHTV Brander EXE...
".\venv\Scripts\pyinstaller" --onefile --noconsole --name "DHTV_Brander" ui.py
echo Build complete.
pause
