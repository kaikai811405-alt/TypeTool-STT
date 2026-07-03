@echo off
chcp 65001 >nul
cd /d "%~dp0"
if "%~1"=="" (
    echo 用法：把音檔拖曳到這個 .bat 檔上（會標記說話人1/2/3…）
    pause
    exit /b
)
venv\Scripts\python.exe transcribe_speaker.py "%~1"
pause
