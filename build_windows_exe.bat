@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"

set "APP_NAME=LANCER1911-PDF-Workshop"
set "ICON_FILE=assets\app.ico"

if not exist "%ICON_FILE%" (
  echo [ERROR] Missing icon: %ICON_FILE%
  pause
  exit /b 1
)

if not exist "venv\Scripts\python.exe" (
  call setup.bat
  if errorlevel 1 exit /b %errorlevel%
)

call "venv\Scripts\activate.bat"
python -c "import proxy_tools, webview, fitz, pikepdf, pypdf" >nul 2>nul
if errorlevel 1 (
  call setup.bat
  if errorlevel 1 exit /b %errorlevel%
  call "venv\Scripts\activate.bat"
)

echo [1/4] Installing PyInstaller...
python -m pip install --no-cache-dir -U pyinstaller
if errorlevel 1 goto ERR

echo [2/4] Cleaning old build files...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del /q "%APP_NAME%.spec" 2>nul

echo [3/4] Building Windows exe...
pyinstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --onefile ^
  --name "%APP_NAME%" ^
  --icon "%ICON_FILE%" ^
  --add-data "web;web" ^
  --add-data "assets;assets" ^
  --collect-submodules webview ^
  --collect-submodules fitz ^
  --hidden-import pymupdf ^
  --hidden-import proxy_tools ^
  app.py
if errorlevel 1 goto ERR

echo [4/4] Creating zip...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path 'dist\%APP_NAME%.exe' -DestinationPath 'dist\%APP_NAME%-Windows.zip' -Force"

echo.
echo Done: dist\%APP_NAME%.exe
echo Zip : dist\%APP_NAME%-Windows.zip
pause
exit /b 0

:ERR
echo.
echo Build failed.
pause
exit /b 1
