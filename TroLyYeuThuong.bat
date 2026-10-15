@echo off
chcp 65001 > nul
cd /d "%~dp0"
title Tro Ly Yeu Thuong

echo ======================================================
echo    HER PERSONAL ASSISTANT - TRO LY YEU THUONG
echo ======================================================
echo Dang khoi dong he thong, vui long cho...
echo.

"C:\Users\ADMIN\AppData\Local\Programs\Python\Python313\python.exe" run_app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [Loi] Khong the khoi dong. Nhan phim bat ky de thoat...
    pause > nul
)
