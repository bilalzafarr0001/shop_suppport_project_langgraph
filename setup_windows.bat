@echo off
cd /d %~dp0
python -m venv venv
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist .env copy .env.example .env
notepad .env
echo Paste your Groq key, save it, then run start_windows.bat
