@echo off
chcp 65001 >nul
cd /d "%~dp0"
call .venv\Scripts\activate.bat || (echo 先に setup.bat を実行してください。& pause & exit /b 1)
ytmp3-web %*
pause
