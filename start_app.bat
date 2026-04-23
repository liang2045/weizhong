@echo off
chcp 65001 >nul
cd /d %~dp0
echo 彩票助手正在启动，请稍候...
python start_app.py
pause
