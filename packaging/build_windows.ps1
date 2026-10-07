$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Venv = Join-Path $Root ".venv-grabit-release"
$PythonLauncher = if ($env:GRABIT_PYTHON) { $env:GRABIT_PYTHON } else { "py" }
$PythonArgs = if ($env:GRABIT_PYTHON) { @() } else { @("-3.11") }

function Invoke-BasePython {
  param([Parameter(Mandatory = $true)][string[]]$Arguments)
  & $PythonLauncher @PythonArgs @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "Base Python command failed with exit code $LASTEXITCODE."
  }
}

function Invoke-VenvPython {
  param([Parameter(Mandatory = $true)][string[]]$Arguments)
  & $VenvPython @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "Packaging Python command failed with exit code $LASTEXITCODE."
  }
}

if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }
if (Test-Path $Venv) { Remove-Item $Venv -Recurse -Force }

Invoke-BasePython @("-m", "venv", $Venv)

$VenvPython = Join-Path $Venv "Scripts" "python.exe"
if (-not (Test-Path $VenvPython)) {
  throw "Packaging virtual environment Python was not created: $VenvPython"
}

Invoke-VenvPython @("-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel")
Invoke-VenvPython @("-m", "pip", "install", "-r", "requirements-packaging.txt")
Invoke-VenvPython @("-m", "pip", "install", "pyinstaller", "pytest")
Invoke-VenvPython @("-m", "pip", "install", "-e", ".", "--no-deps")

Invoke-VenvPython @("-c", @"
import PySide6, requests, yt_dlp, gallery_dl, instaloader, yaml
print("PACKAGING_CORE_IMPORTS_OK")
"@)

$installed = & $VenvPython -m pip list --format=freeze
if ($LASTEXITCODE -ne 0) {
  throw "Could not inspect packaging environment."
}
$installed | Out-Host

$unexpectedHeavy = $installed | Select-String -Pattern '^(torch|torchvision|torchaudio|tensorflow|tensorflow-cpu|tensorflow-gpu|gradio|scipy)=='
if ($unexpectedHeavy) {
  $unexpectedHeavy | ForEach-Object { Write-Error "Unexpected heavy package in isolated packaging environment: $($_.Line)" }
  throw "Packaging environment is contaminated by an unexpected heavy dependency."
}

Invoke-VenvPython @("-m", "pytest", "-q")
Invoke-VenvPython @("-m", "PyInstaller", "--clean", "--noconfirm", "packaging/GrabIt.spec")

if (-not (Test-Path "dist/GrabIt.exe")) {
  throw "Expected dist/GrabIt.exe was not produced."
}

Write-Host "Built: $(Resolve-Path dist/GrabIt.exe)"
