@echo off
cd /d %~dp0
call .venv\Scripts\activate.bat
echo 正在启动 EdgePdM-Agent 训练控制台 (服务端窗口，可 Ctrl+C 关闭) ...
start "" python training_marathon.py
echo 等待服务端就绪 ...
timeout /t 7 /nobreak >nul
start "" http://127.0.0.1:8765
echo 浏览器已打开 http://127.0.0.1:8765
echo 若页面显示"一直断开连接"，请确认本窗口的服务端仍在运行。
pause
