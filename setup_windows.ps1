$ErrorActionPreference = "Stop"

Write-Host "Word Helper - instalacion para Windows" -ForegroundColor Cyan

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "No se encontro Python. Instala Python 3.11+ desde https://www.python.org/downloads/ y vuelve a ejecutar este script."
}

if (-not (Get-Command tesseract -ErrorAction SilentlyContinue)) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "Instalando Tesseract OCR..."
        winget install --id UB-Mannheim.TesseractOCR --exact --accept-package-agreements --accept-source-agreements
    } else {
        Write-Warning "No se encontro Tesseract ni winget. Instala Tesseract OCR manualmente para usar capturas."
    }
}

if (-not (Test-Path ".venv")) {
    py -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

@"
@echo off
cd /d "%~dp0"
".venv\Scripts\pythonw.exe" main.py
"@ | Set-Content -Encoding ASCII "Word Helper.bat"

Write-Host ""
Write-Host "Listo. Abre 'Word Helper.bat' para iniciar la app." -ForegroundColor Green
