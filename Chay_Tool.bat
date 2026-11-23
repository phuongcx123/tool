@echo off
title Tool Danh Tuong 3Q - newsgs.zce8.com
cd /d "%~dp0"
echo Dang khoi dong Tool...
python gui.py
if %errorlevel% neq 0 (
    echo.
    echo Co loi xay ra khi khoi chay. Nhan phim bat ky de thoat...
    pause >nul
)
