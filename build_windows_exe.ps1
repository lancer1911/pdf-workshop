$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$AppName = "LANCER1911-PDF-Workshop"
$IconFile = "assets\app.ico"

if (!(Test-Path $IconFile)) { throw "Missing icon: $IconFile" }

if (!(Test-Path "venv\Scripts\python.exe")) {
  & cmd /c setup.bat
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

. .\venv\Scripts\Activate.ps1
python -c "import proxy_tools, webview, fitz, pikepdf, pypdf" | Out-Null
if ($LASTEXITCODE -ne 0) {
  & cmd /c setup.bat
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  . .\venv\Scripts\Activate.ps1
}

python -m pip install --no-cache-dir -U pyinstaller

Remove-Item build, dist -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$AppName.spec" -Force -ErrorAction SilentlyContinue

pyinstaller `
  --noconfirm `
  --clean `
  --windowed `
  --onefile `
  --name "$AppName" `
  --icon "$IconFile" `
  --add-data "web;web" `
  --add-data "assets;assets" `
  --collect-submodules webview `
  --collect-submodules fitz `
  --hidden-import pymupdf `
  --hidden-import proxy_tools `
  app.py

Compress-Archive -Path "dist\$AppName.exe" -DestinationPath "dist\$AppName-Windows.zip" -Force
Write-Host "Done: dist\$AppName.exe"
Write-Host "Zip : dist\$AppName-Windows.zip"
