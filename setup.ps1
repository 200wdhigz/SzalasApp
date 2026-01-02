# Quick Start Script for Windows PowerShell
# Run with: .\setup.ps1

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "SzalasApp Setup Script" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check if Poetry is installed
Write-Host "Checking for Poetry..." -ForegroundColor Yellow
$poetryPath = Get-Command poetry -ErrorAction SilentlyContinue
if (-not $poetryPath) {
    Write-Host "Poetry not found. Installing Poetry..." -ForegroundColor Red
    (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
    Write-Host "Please restart your terminal and run this script again." -ForegroundColor Yellow
    exit
} else {
    Write-Host "Poetry found: $($poetryPath.Source)" -ForegroundColor Green
}

# Check Python version
Write-Host ""
Write-Host "Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "Found: $pythonVersion" -ForegroundColor Green

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies with Poetry..." -ForegroundColor Yellow
Set-Location app
poetry install
Set-Location ..
if ($LASTEXITCODE -eq 0) {
    Write-Host "Dependencies installed successfully!" -ForegroundColor Green
} else {
    Write-Host "Failed to install dependencies." -ForegroundColor Red
    exit 1
}

# Create .env file if it doesn't exist
Write-Host ""
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host ".env file created. Please edit it with your configuration." -ForegroundColor Yellow
} else {
    Write-Host ".env file already exists." -ForegroundColor Green
}

# Create credentials directory
Write-Host ""
if (-not (Test-Path "credentials")) {
    Write-Host "Creating credentials directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path "credentials" | Out-Null
    Write-Host "Please place your service-account.json in the credentials/ directory." -ForegroundColor Yellow
} else {
    Write-Host "Credentials directory already exists." -ForegroundColor Green
}

# Summary
Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env file with your configuration" -ForegroundColor White
Write-Host "2. Place service-account.json in credentials/ directory" -ForegroundColor White
Write-Host "3. Run the application:" -ForegroundColor White
Write-Host "   Development: cd app && poetry run python app.py" -ForegroundColor Cyan
Write-Host "   Production:  cd app && poetry run gunicorn --bind 0.0.0.0:8080 app:app" -ForegroundColor Cyan
Write-Host "   Docker:      docker-compose up --build" -ForegroundColor Cyan
Write-Host ""
Write-Host "Documentation:" -ForegroundColor Yellow
Write-Host "  - Poetry Guide: POETRY_GUIDE.md" -ForegroundColor White
Write-Host "  - Docker Guide: DOCKER_GUIDE.md" -ForegroundColor White
Write-Host ""

