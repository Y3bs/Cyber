@echo off
setlocal enableextensions enabledelayedexpansion

REM Build Windows EXE for the Flask app

where pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller --quiet
)

REM Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist app.spec del /f /q app.spec

REM Ensure env exists
if not exist ".env" (
    echo WARNING: .env not found. The built app will require DB_TOKEN at runtime.
)

REM Collect data files (templates, static, json, icons)
set DATAS=
set DATAS=%DATAS% --add-data "templates;templates"
set DATAS=%DATAS% --add-data "static;static"
if exist current_day.json set DATAS=%DATAS% --add-data "current_day.json;."
if exist Logo.jpg set DATAS=%DATAS% --add-data "Logo.jpg;."
if exist "Logo(1).ico" (
  set ICON=--icon="Logo(1).ico"
) else (
  set ICON=
)

REM Ensure pywebview is installed
pip show pywebview >nul 2>&1 || pip install pywebview --quiet

REM Build one-file windowed exe using the GUI launcher
pyinstaller --noconfirm --clean %ICON% %DATAS% --name CyberCafe --collect-all nextcord --collect-all reportlab --collect-all dotenv --collect-all webview --onefile --windowed gui_launcher.py

if errorlevel 1 (
    echo Build failed.
    exit /b 1
)

echo Build complete. Run the app from: dist\CyberCafe.exe
exit /b 0
