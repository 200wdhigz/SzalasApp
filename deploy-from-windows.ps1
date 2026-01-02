# PowerShell script to deploy SzalasApp to production server
# Użycie: .\deploy-from-windows.ps1

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerIP,

    [Parameter(Mandatory=$false)]
    [string]$ServerUser = "root",

    [Parameter(Mandatory=$false)]
    [string]$Domain = "szalasapp.kawak.uk"
)

$ErrorActionPreference = "Stop"

Write-Host "=====================================" -ForegroundColor Green
Write-Host "  SzalasApp - Wdrożenie z Windows" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""

$ProjectPath = $PSScriptRoot

# Sprawdź czy SCP jest dostępne
if (-not (Get-Command scp -ErrorAction SilentlyContinue)) {
    Write-Host "❌ SCP nie jest dostępne. Zainstaluj OpenSSH Client:" -ForegroundColor Red
    Write-Host "   Settings -> Apps -> Optional Features -> OpenSSH Client" -ForegroundColor Yellow
    exit 1
}

Write-Host "📦 Przygotowanie plików..." -ForegroundColor Yellow

# Sprawdź wymagane pliki
$requiredFiles = @(
    ".env",
    "credentials\service-account.json"
)

foreach ($file in $requiredFiles) {
    $fullPath = Join-Path $ProjectPath $file
    if (-not (Test-Path $fullPath)) {
        Write-Host "❌ Brak pliku: $file" -ForegroundColor Red
        Write-Host "   Utwórz ten plik przed wdrożeniem" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "✅ Wszystkie wymagane pliki znalezione" -ForegroundColor Green
Write-Host ""

Write-Host "📤 Kopiowanie plików na serwer..." -ForegroundColor Yellow

# Utwórz katalog na serwerze
ssh "${ServerUser}@${ServerIP}" "mkdir -p ~/SzalasApp/credentials"

# Kopiuj pliki aplikacji (bez __pycache__, .git, etc.)
$filesToCopy = @(
    "app",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.prod.yml",
    "nginx-config-example.conf",
    "backup.sh",
    ".env",
    "credentials"
)

foreach ($item in $filesToCopy) {
    $sourcePath = Join-Path $ProjectPath $item
    if (Test-Path $sourcePath) {
        Write-Host "   Kopiowanie: $item"
        scp -r $sourcePath "${ServerUser}@${ServerIP}:~/SzalasApp/"
    }
}

Write-Host "✅ Pliki skopiowane" -ForegroundColor Green
Write-Host ""

Write-Host "🚀 Uruchamianie aplikacji na serwerze..." -ForegroundColor Yellow

# Uruchom aplikację przez SSH
$deployCommands = @"
cd ~/SzalasApp
echo '✅ Pliki skopiowane na serwer'
echo '🐳 Uruchamianie Docker Compose...'
docker compose down 2>/dev/null || true
docker compose up -d --build
echo '✅ Aplikacja uruchomiona'
echo ''
echo '📊 Status kontenera:'
docker compose ps
echo ''
echo '📝 Ostatnie logi (naciśnij Ctrl+C aby przerwać):'
docker compose logs --tail=50 app
"@

ssh -t "${ServerUser}@${ServerIP}" $deployCommands

Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "  Wdrożenie zakończone! ✨" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""
Write-Host "Aplikacja powinna być dostępna pod:" -ForegroundColor Cyan
Write-Host "  https://$Domain" -ForegroundColor Cyan
Write-Host ""
Write-Host "Przydatne komendy:" -ForegroundColor Yellow
Write-Host "  Zobacz logi:" -ForegroundColor Gray
Write-Host "    ssh ${ServerUser}@${ServerIP} 'cd ~/SzalasApp && docker compose logs -f'" -ForegroundColor Gray
Write-Host "  Restart aplikacji:" -ForegroundColor Gray
Write-Host "    ssh ${ServerUser}@${ServerIP} 'cd ~/SzalasApp && docker compose restart'" -ForegroundColor Gray
Write-Host "  Status:" -ForegroundColor Gray
Write-Host "    ssh ${ServerUser}@${ServerIP} 'cd ~/SzalasApp && docker compose ps'" -ForegroundColor Gray
Write-Host ""

