@echo off
rem 初回だけ実行: 仮想環境を作って ytmp3 をインストールする
chcp 65001 >nul
cd /d "%~dp0"
py -3 -m venv .venv || python -m venv .venv || goto :error
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -e . || goto :error
where ffmpeg >nul 2>nul || echo [注意] ffmpeg が見つかりません。README の手順でインストールしてください。
echo.
echo セットアップ完了。start_web.bat をダブルクリックすると起動します。
pause
exit /b 0
:error
echo セットアップに失敗しました。
pause
exit /b 1
