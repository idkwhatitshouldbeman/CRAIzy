@echo off
cd /d "%~dp0"
call activate venv
python main.py
pause
