$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Python = if ($env:GRABIT_PYTHON) { $env:GRABIT_PYTHON } else { "py -3.11" }
function Invoke-Python {
  param([Parameter(Mandatory=$true)][string]$Command)
  & cmd.exe /c "$Python $Command"
  if ($LASTEXITCODE -ne 0) { throw "Python command failed with exit code $LASTEXITCODE." }
}
if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }
Invoke-Python "-m pip install --upgrade pip setuptools wheel"
Invoke-Python "-m pip install pyinstaller"
Invoke-Python "-m pip install -e . --no-deps"
Invoke-Python "-c ""import PySide6, requests, yt_dlp, gallery_dl, instaloader, yaml, pinterest_dl, gdown, bilix, twitcharchiver, sclib, RedDownloader, tiktok_downloader, instacapture, civitai_downloader; print('REQUIRED_IMPORTS_OK')"""
Invoke-Python "-m pytest -q"
Invoke-Python "-m PyInstaller --clean --noconfirm packaging/GrabIt.spec"
if (-not (Test-Path "dist/GrabIt.exe")) { throw "Expected dist/GrabIt.exe was not produced." }
Write-Host "Built: $(Resolve-Path dist/GrabIt.exe)"
