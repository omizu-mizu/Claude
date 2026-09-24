@echo off
rem yt-dlp を最新版に更新する（YouTube 側の仕様変更で動かなくなったとき）
chcp 65001 >nul
cd /d "%~dp0"
call .venv\Scripts\activate.bat || (echo 先に setup.bat を実行してください。& pause & exit /b 1)
pip install -U yt-dlp
pause
