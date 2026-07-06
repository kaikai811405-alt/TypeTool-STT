@echo off
chcp 65001 >nul
cd /d "%~dp0"
title TypeTool-STT 更新
echo 從 GitHub 抓取最新版本 ...
git pull
if errorlevel 1 (
    echo.
    echo [提醒] 更新失敗。若本機有改過檔案，git 會擋下更新。
    echo 需要協助請把上面訊息貼給 Claude。
)
echo.
echo 完成。若提示「相依套件有變」才需要再跑一次 install.bat。
pause
