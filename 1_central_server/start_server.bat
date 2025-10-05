@echo off
cd /d "%~dp0"
call activate venv  # If virtualenv
python server.py
pause
