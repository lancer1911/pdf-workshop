@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo Repair Windows venv for LANCER1911 PDF Workshop
echo Current folder: %CD%
echo ============================================================

echo This will delete and recreate venv.
if exist "venv" rmdir /s /q venv
call setup.bat --retry
exit /b %errorlevel%
