@echo off
cd /d "%~dp0"
call activate venv
python train_ppo.py --batch mock_batch.json
pause
