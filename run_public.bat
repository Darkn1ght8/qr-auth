@echo off
rem Start the site with a public https link that opens from any phone, laptop or computer.
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
".venv\Scripts\python.exe" manage.py runpublic --port 8000
pause
