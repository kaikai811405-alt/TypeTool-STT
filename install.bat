@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title TypeTool-STT 一鍵安裝
cd /d "%~dp0"

echo ============================================================
echo   TypeTool-STT 一鍵安裝
echo   會在本資料夾建立 venv，並自動偵測顯卡選對 PyTorch 版本
echo ============================================================
echo.

REM ================= 1. Python 3.11 =================
echo [1/5] 檢查 / 安裝 Python 3.11 ...
set "PY311=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if not exist "%PY311%" (
    winget install --id Python.Python.3.11 --scope user --silent --accept-package-agreements --accept-source-agreements
)
if not exist "%PY311%" (
    echo [錯誤] 找不到 Python 3.11：%PY311%
    echo 請確認 winget 安裝成功，或手動安裝 Python 3.11 後重跑。
    pause & exit /b 1
)
echo     OK: %PY311%

REM ================= 2. ffmpeg =================
echo [2/5] 檢查 / 安裝 ffmpeg ...
where ffmpeg >nul 2>&1 || winget install --id Gyan.FFmpeg --scope user --silent --accept-package-agreements --accept-source-agreements
echo     OK

REM ================= 3. venv（建在本資料夾）=================
echo [3/5] 建立虛擬環境 venv ...
if not exist "venv\Scripts\python.exe" (
    "%PY311%" -m venv venv
)
set "VPY=venv\Scripts\python.exe"
"%VPY%" -m pip install --upgrade pip setuptools wheel
echo     OK

REM ================= 4. 偵測顯卡 → 裝對應 PyTorch =================
echo [4/5] 偵測顯卡 ...
set "TORCH_INDEX=https://download.pytorch.org/whl/cpu"
set "GPU=無獨立顯卡（CPU）"
where nvidia-smi >nul 2>&1 && (
    set "TORCH_INDEX=https://download.pytorch.org/whl/cu128"
    set "GPU=NVIDIA CUDA（cu128）"
)
echo     偵測結果: !GPU!
echo     安裝 PyTorch 2.9.1（來源: !TORCH_INDEX!）... 有 GPU 約 2.9GB，請耐心等
"%VPY%" -m pip install torch==2.9.1 torchaudio==2.9.1 --index-url !TORCH_INDEX!
if errorlevel 1 ( echo [錯誤] PyTorch 安裝失敗 & pause & exit /b 1 )
echo     OK

REM ================= 5. 其餘套件 =================
echo [5/5] 安裝 funasr / transformers / opencc 等（依 requirements.txt）...
"%VPY%" -m pip install -r requirements.txt
if errorlevel 1 ( echo [錯誤] 套件安裝失敗 & pause & exit /b 1 )
echo     OK

echo.
echo ============================================================
echo   驗證 ...
"%VPY%" -c "import torch;print('  PyTorch:',torch.__version__,'| CUDA 可用:',torch.cuda.is_available(),'| GPU:',torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
echo ============================================================
echo.
echo   安裝完成！用法：
echo   - 語音輸入：雙擊 語音輸入.bat（按住 Alt+Ctrl 講話）
echo   - 錄會議  ：雙擊 錄會議.bat（開會 → 按 Enter 停）
echo   - 轉逐字稿：把音檔拖到 轉逐字稿_拖曳音檔到此.bat
echo   - 說話人分離：把音檔拖到 說話人分離_拖曳音檔到此.bat
echo   （模型首次使用會自動下載，需網路）
echo ============================================================
pause
