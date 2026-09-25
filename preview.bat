@echo off
chcp 65001 > nul
cd /d "%~dp0"

where ruby > nul 2>&1
if errorlevel 1 (
  echo [エラー] Ruby が見つかりません。README-blog.md の手順で Ruby+Devkit をインストールしてください。
  pause
  exit /b 1
)

echo 必要なパッケージを確認しています（初回は数分かかります）...
call bundle install > preview-log.txt 2>&1
if errorlevel 1 (
  type preview-log.txt
  echo.
  echo [エラー] パッケージのインストールに失敗しました。この画面か preview-log.txt を Claude に見せてください。
  pause
  exit /b 1
)

echo.
echo ブログのローカルプレビューを起動します。
echo 準備ができたらブラウザで http://localhost:4000/blog/ が自動で開きます。
echo 終了するときは、この画面で Ctrl + C を押してください。
echo.

rem サーバーの起動を待ってからブラウザを開く（最大2分）
start "" /b powershell -NoProfile -WindowStyle Hidden -Command "for($i=0;$i -lt 120;$i++){try{$c=New-Object Net.Sockets.TcpClient('127.0.0.1',4000);$c.Close();Start-Process 'http://localhost:4000/blog/';break}catch{Start-Sleep 1}}"

powershell -NoProfile -Command "bundle exec jekyll serve --host 127.0.0.1 --port 4000 2>&1 | ForEach-Object { \"$_\" } | Tee-Object -FilePath preview-log.txt -Append"

echo.
echo プレビューを終了しました。エラーが出ていた場合は preview-log.txt を Claude に見せてください。
pause
