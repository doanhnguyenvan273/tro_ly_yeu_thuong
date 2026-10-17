@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
cd /d "%~dp0"
title Tro Ly Yeu Thuong

echo ======================================================
echo    HER PERSONAL ASSISTANT - TRO LY YEU THUONG
echo ======================================================
echo Dang kiem tra moi truong va khoi dong he thong...
echo.

set "PY_CMD="

REM Kiem tra lenh py
where py >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=py"
    goto found_python
)

REM Kiem tra lenh python trong PATH
where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto found_python
)

REM Kiem tra AppData nguoi dung hien tai
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%D\python.exe" (
        set "PY_CMD="%%D\python.exe""
        goto found_python
    )
)

REM Kiem tra Program Files
for /d %%D in ("%ProgramFiles%\Python3*") do (
    if exist "%%D\python.exe" (
        set "PY_CMD="%%D\python.exe""
        goto found_python
    )
)

echo.
echo [CANH BAO] May tinh nay chua cai dat Python!
echo.
echo Huong dan cai dat Python nhanh trong 2 phut:
echo 1. Vao web: https://www.python.org/downloads/
echo 2. Tai ve va mo file cai dat Python 3.10 hoac moi hon.
echo 3. LUU Y QUAN TRONG: Tich chon vao o [Add Python to PATH] khi cai dat!
echo.
pause
exit /b 1

:found_python
echo [1/2] Tim thay Python tai: %PY_CMD%

REM Kiem tra va cai dat thu vien neu con thieu
%PY_CMD% -c "import streamlit" >nul 2>nul
if %errorlevel% neq 0 (
    echo [Thong bao] Dang cai dat thu vien can thiet, vui long cho 1-2 phut...
    %PY_CMD% -m pip install -r requirements.txt
)

REM Tu dong tao Shortcut trai tim ra Desktop neu chua co
if not exist "%USERPROFILE%\Desktop\Tro Ly Yeu Thuong.lnk" (
    %PY_CMD% create_desktop_shortcut.py >nul 2>nul
)

echo [2/2] Dang mo giao dien Tro Ly Yeu Thuong...
echo.
%PY_CMD% run_app.py

if %errorlevel% neq 0 (
    echo.
    echo [Loi] Khong the khoi dong. Nhan phim bat ky de thoat...
    pause >nul
)
