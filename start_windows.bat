@echo off
setlocal
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
  call setup.bat
  if errorlevel 1 exit /b %errorlevel%
)
call "venv\Scripts\activate.bat"
python -c "import proxy_tools, webview, fitz, pikepdf, pypdf" >nul 2>nul
if errorlevel 1 (
  call setup.bat
  if errorlevel 1 exit /b %errorlevel%
)
python app.py
pause
