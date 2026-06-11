@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

set "PYTHONUTF8=1"
set "PIP_DISABLE_PIP_VERSION_CHECK=1"

echo ============================================================
echo LANCER1911 PDF Workshop - Windows setup
echo Current folder: %CD%
echo ============================================================

if not exist "requirements.txt" (
  echo [ERROR] requirements.txt not found. Please run this script from the pdf_workshop folder.
  pause
  exit /b 1
)

if not exist "venv\Scripts\python.exe" (
  call :CREATE_VENV
  if errorlevel 1 goto FAIL
) else (
  echo [INFO] Existing venv found: venv\
)

call :INSTALL_AND_VERIFY
if errorlevel 1 (
  if /I "%~1"=="--retry" goto FAIL
  echo.
  echo [WARN] Existing venv appears broken. Rebuilding venv from scratch...
  rmdir /s /q venv 2>nul
  call :CREATE_VENV
  if errorlevel 1 goto FAIL
  call :INSTALL_AND_VERIFY
  if errorlevel 1 goto FAIL
)

echo.
echo ============================================================
echo Setup completed successfully.
echo.
echo Run app:
echo   venv\Scripts\python.exe app.py
echo.
echo Or double-click:
echo   start_windows.bat
echo ============================================================
pause
exit /b 0

:CREATE_VENV
set "PY_CMD="
for %%C in ("py -3.12" "py -3.11" "py -3.10" "py -3" "python") do (
  call %%~C -c "import sys,struct; raise SystemExit(0 if sys.version_info >= (3,10) and struct.calcsize('P')*8 == 64 else 1)" >nul 2>nul
  if not errorlevel 1 (
    set "PY_CMD=%%~C"
    goto FOUND_PYTHON
  )
)

:FOUND_PYTHON
if not defined PY_CMD (
  echo [ERROR] No suitable 64-bit Python 3.10+ found.
  echo Recommended: Python 3.11 or 3.12 x64.
  pause
  exit /b 1
)

echo [1/4] Using Python command: %PY_CMD%
call %PY_CMD% -c "import sys,platform,struct; print(sys.version); print(platform.platform()); print('bits=', struct.calcsize('P')*8)"

echo [2/4] Creating virtual environment...
call %PY_CMD% -m venv venv
if errorlevel 1 exit /b 1
exit /b 0

:INSTALL_AND_VERIFY
call "venv\Scripts\activate.bat"

echo [3/4] Upgrading pip/setuptools/wheel...
python -m pip install -U pip setuptools wheel
if errorlevel 1 exit /b 1

echo [4/4] Installing project requirements...
python -m pip install --no-cache-dir -U -r requirements.txt
if errorlevel 1 exit /b 1

REM pywebview sometimes misses proxy_tools in old/dirty environments; force them explicitly.
python -m pip install --no-cache-dir -U proxy_tools pywebview bottle typing_extensions
if errorlevel 1 exit /b 1

echo [VERIFY] Checking imports...
python -c "import proxy_tools, webview, fitz, pikepdf, pypdf; print('OK: imports succeeded')"
if errorlevel 1 exit /b 1
exit /b 0

:FAIL
echo.
echo ============================================================
echo Setup failed.
echo Please copy the full output above and send it back.
echo ============================================================
pause
exit /b 1
