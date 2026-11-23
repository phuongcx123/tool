@echo off
title Tool Danh Tuong 3Q - Web Online (newsgs.zce8.com)
cd /d "%~dp0"
echo ============================================================
echo   KHOI DONG WEB TOOL DANH TUONG 3Q ONLINE
echo ============================================================
echo.
python web_app.py
if %errorlevel% neq 0 (
    echo.
    echo Co loi xay ra khi khoi chay Web. Nhan phim bat ky de thoat...
    pause >nul
)
