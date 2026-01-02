# Wdrożenie Produkcyjne z Docker i SSL/HTTPS

## Spis treści
1. [Wprowadzenie](#wprowadzenie)
2. [Wymagania](#wymagania)
3. [Architektura wdrożenia](#architektura-wdrożenia)
4. [Przygotowanie serwera](#przygotowanie-serwera)
5. [Konfiguracja domeny](#konfiguracja-domeny)
6. **[Wariant A: Nginx Proxy Manager (Jeśli już używasz NPM)](#nginx-proxy-manager)**
   - [Konfiguracja sieci Docker](#krok-1-konfiguracja-sieci-docker)
   - [Uruchomienie SzalasApp](#krok-2-uruchomienie-szalasapp)
   - [Konfiguracja Proxy Host](#krok-3-konfiguracja-proxy-host-w-npm)
   - [Zaawansowane funkcje NPM](#zaawansowane-funkcje-npm-dla-szalasapp)
     - Access Lists
     - Basic Authentication
     - Custom Locations
     - Monitorowanie
     - Backup konfiguracji
   - [Migracja do NPM](#migracja-do-npm-z-innych-rozwiązań)
   - [Najlepsze praktyki](#najlepsze-praktyki-dla-npm--szalasapp)
   - [Skalowanie](#skalowanie-z-npm)
   - [FAQ](#faq-dla-npm)
   - [Automatyzacja wdrożeń](#automatyzacja-wdrożeń-z-npm)
     - GitHub Actions
     - Webhook
     - Watchtower
     - Blue-Green Deployment
     - Zero-Downtime Best Practices
7. **[Wariant B: Standardowy Nginx](#konfiguracja-ssl)**
8. [Przygotowanie aplikacji](#przygotowanie-aplikacji)
9. [Wdrożenie z Docker Compose](#wdrożenie-docker)
10. [Monitorowanie i utrzymanie](#monitorowanie)
11. [Backup i odzyskiwanie](#backup)
12. [Troubleshooting](#troubleshooting)

## Wprowadzenie

Ten poradnik opisuje krok po kroku, jak wdrożyć aplikację SzalasApp na serwerze produkcyjnym z:
- **Docker i Docker Compose** - konteneryzacja aplikacji
- **Nginx** - reverse proxy i obsługa SSL
- **Let's Encrypt (Certbot)** - darmowe certyfikaty SSL
- **HTTPS** dla domeny `szalasapp.kawak.uk`

### 🎯 Wybierz wariant wdrożenia

**Wariant A: Nginx Proxy Manager** (Jeśli już masz NPM) ⭐ ZALECANE
- ✅ Łatwiejszy - interfejs webowy
- ✅ Automatyczne zarządzanie certyfikatami
- ✅ Idealne jeśli hostujesz więcej aplikacji
- 📄 [Przejdź do Wariant A](#nginx-proxy-manager)
- 📄 [Szybki Start NPM](../../DEPLOYMENT_NPM_QUICKSTART.md) - skrócona instrukcja

**Wariant B: Standardowy Nginx** (Ręczna konfiguracja)
- 🔧 Pełna kontrola nad konfiguracją
- 🔧 Wymaga edycji plików konfiguracyjnych
- 🔧 Dla zaawansowanych użytkowników
- 📄 [Przejdź do Wariant B](#konfiguracja-ssl)

**Oba warianty prowadzą do tego samego rezultatu - działającej aplikacji z HTTPS.**

## Wymagania

### Serwer
- **System operacyjny**: Ubuntu 22.04 LTS lub nowszy (lub inny Linux)
- **RAM**: minimum 2GB (zalecane 4GB)
- **Dysk**: minimum 20GB wolnego miejsca
- **Procesor**: 2 vCPU (zalecane)
- **Publiczny adres IP**
- **Otwarte porty**: 80 (HTTP), 443 (HTTPS), 22 (SSH)

### Domena
- Domena: `kawak.uk` z subdomeną `szalasapp`
- Dostęp do panelu DNS dostawcy domeny

### Oprogramowanie na serwerze
- Docker (>= 24.0)
- Docker Compose (>= 2.20)
- Nginx
- Certbot (Let's Encrypt client)
- Git

### Wymagane dane konfiguracyjne
- Service Account JSON z Google Cloud
- OAuth credentials (Google)
- reCAPTCHA keys
- Secret Key dla Flask
- Dane SMTP (opcjonalne)

## Architektura wdrożenia

### Wariant A: Z Nginx Proxy Manager

```
┌─────────────────────────────────────────────────────────────┐
│                        INTERNET                             │
│                    (HTTPS Traffic)                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Port 443 (HTTPS)
                         │ Port 80 (HTTP → redirect to HTTPS)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              NGINX PROXY MANAGER                            │
│              (Docker Container)                             │
│                                                             │
│  • SSL Termination (Let's Encrypt)                         │
│  • Automatic certificate renewal                           │
│  • Web UI for configuration                                │
│  • Reverse proxy routing                                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Docker Network: proxy-network
                         │ Internal: szalasapp:8080
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              SZALASAPP                                      │
│              (Docker Container)                             │
│                                                             │
│  Flask App + Gunicorn                                       │
│  Port 8080 (internal only)                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ API Calls
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         GOOGLE CLOUD SERVICES                               │
│                                                             │
│  • Firebase Authentication                                  │
│  • Firestore Database                                       │
│  • Cloud Storage (photos)                                   │
│  • reCAPTCHA Enterprise                                     │
└─────────────────────────────────────────────────────────────┘
```

### Wariant B: Ze standardowym Nginx

```
┌─────────────────────────────────────────────────────────────┐
│                        INTERNET                             │
│                    (HTTPS Traffic)                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Port 443 (HTTPS)
                         │ Port 80 (HTTP → redirect to HTTPS)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              NGINX (System Service)                         │
│              /etc/nginx/sites-available/szalasapp           │
│                                                             │
│  • SSL Termination (Let's Encrypt via Certbot)            │
│  • Manual certificate renewal (or cron)                    │
│  • Manual configuration files                              │
│  • Reverse proxy to localhost:8080                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ localhost:8080
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              SZALASAPP                                      │
│              (Docker Container)                             │
│                                                             │
│  Flask App + Gunicorn                                       │
│  Port 8080 (bound to 127.0.0.1:8080)                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ API Calls
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         GOOGLE CLOUD SERVICES                               │
│                                                             │
│  • Firebase Authentication                                  │
│  • Firestore Database                                       │
│  • Cloud Storage (photos)                                   │
│  • reCAPTCHA Enterprise                                     │
└─────────────────────────────────────────────────────────────┘
```

### Kluczowe różnice

| Aspekt | Nginx Proxy Manager | Standardowy Nginx |
|--------|-------------------|------------------|
| Konfiguracja | Web UI (graficzny) | Pliki tekstowe |
| Certyfikaty SSL | Automatyczne (1 klik) | Ręczne (certbot commands) |
| Odnowienie certyfikatu | Automatyczne | Ręczne lub cron |
| Łatwość zarządzania | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Wiele aplikacji | Bardzo łatwe | Wymaga wielu plików config |
| Docker networking | Wspólna sieć Docker | localhost binding |
| Logi | UI + pliki | Tylko pliki |

**Przepływ ruchu (oba warianty):**
1. Użytkownik wchodzi na `https://szalasapp.kawak.uk`
2. Nginx/NPM odbiera żądanie HTTPS (port 443)
3. Nginx/NPM weryfikuje certyfikat SSL
4. Nginx/NPM przekazuje żądanie do Docker container (port 8080)
5. Aplikacja Flask/Gunicorn przetwarza żądanie
6. Aplikacja komunikuje się z Firebase/GCS
7. Odpowiedź wraca do użytkownika przez Nginx/NPM

## Przygotowanie serwera

### 1. Zakup/przygotowanie serwera VPS

Rekomendowane dostawcy:
- **DigitalOcean** (Droplet)
- **Linode** (Compute Instance)
- **Hetzner** (Cloud Server)
- **AWS EC2** (t3.small lub większy)
- **Google Cloud** (e2-small lub większy)

**Minimalna konfiguracja:**
- Ubuntu 22.04 LTS
- 2GB RAM
- 20GB SSD
- 1 vCPU

### 2. Połączenie z serwerem

```bash
# Połącz się przez SSH (Windows: użyj PowerShell lub PuTTY)
ssh root@YOUR_SERVER_IP
```

### 3. Aktualizacja systemu

```bash
# Aktualizuj system
sudo apt update && sudo apt upgrade -y

# Zainstaluj podstawowe narzędzia
sudo apt install -y curl wget git vim ufw software-properties-common
```

### 4. Konfiguracja firewall (UFW)

```bash
# Włącz firewall
sudo ufw enable

# Zezwól na SSH
sudo ufw allow 22/tcp

# Zezwól na HTTP i HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Sprawdź status
sudo ufw status
```

### 5. Instalacja Docker

```bash
# Usuń stare wersje (jeśli istnieją)
sudo apt remove docker docker-engine docker.io containerd runc

# Dodaj oficjalne repozytorium Docker
sudo apt install -y ca-certificates curl gnupg lsb-release

sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Zainstaluj Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Sprawdź instalację
docker --version
docker compose version

# Dodaj użytkownika do grupy docker (opcjonalne)
sudo usermod -aG docker $USER
```

### 6. Instalacja Nginx

```bash
# Zainstaluj Nginx
sudo apt install -y nginx

# Uruchom i włącz autostart
sudo systemctl start nginx
sudo systemctl enable nginx

# Sprawdź status
sudo systemctl status nginx
```

### 7. Instalacja Certbot (Let's Encrypt)

```bash
# Zainstaluj Certbot
sudo apt install -y certbot python3-certbot-nginx

# Sprawdź instalację
certbot --version
```

## Konfiguracja domeny

### 1. Konfiguracja DNS

Zaloguj się do panelu DNS swojego dostawcy domeny (np. Cloudflare, GoDaddy, Namecheap) i dodaj rekord:

**Rekord A:**
```
Type: A
Name: szalasapp
Value: YOUR_SERVER_IP
TTL: 3600 (lub Auto)
```

**Przykład:**
```
A    szalasapp    123.456.789.012    3600
```

### 2. Weryfikacja DNS

```bash
# Sprawdź, czy domena wskazuje na twój serwer (po 5-15 minutach)
nslookup szalasapp.kawak.uk

# Lub użyj dig
dig szalasapp.kawak.uk +short
```

Powinno zwrócić adres IP twojego serwera.

## Konfiguracja SSL/HTTPS z Nginx i Let's Encrypt {#konfiguracja-ssl}

### 1. Podstawowa konfiguracja Nginx (przed SSL)

Utwórz plik konfiguracyjny:

```bash
sudo vim /etc/nginx/sites-available/szalasapp
```

Dodaj następującą konfigurację:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name szalasapp.kawak.uk;

    # Lokalizacja dla weryfikacji Let's Encrypt
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Tymczasowe przekierowanie do aplikacji (przed SSL)
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Aktywuj konfigurację:

```bash
# Utwórz symlink
sudo ln -s /etc/nginx/sites-available/szalasapp /etc/nginx/sites-enabled/

# Usuń domyślną konfigurację (opcjonalne)
sudo rm /etc/nginx/sites-enabled/default

# Sprawdź konfigurację
sudo nginx -t

# Przeładuj Nginx
sudo systemctl reload nginx
```

### 2. Uzyskanie certyfikatu SSL

```bash
# Uruchom Certbot (automatycznie skonfiguruje Nginx)
sudo certbot --nginx -d szalasapp.kawak.uk --email your-email@example.com --agree-tos --no-eff-email

# Opcje:
# --nginx: użyj pluginu nginx
# -d: domena
# --email: twój email (dla powiadomień o wygaśnięciu)
# --agree-tos: akceptuj warunki
# --no-eff-email: nie udostępniaj emaila EFF
```

Certbot automatycznie:
- Weryfikuje domenę
- Pobiera certyfikat SSL
- Modyfikuje konfigurację Nginx
- Dodaje przekierowanie HTTP → HTTPS

### 3. Finalna konfiguracja Nginx z SSL

Po uruchomieniu Certbot, zmodyfikuj konfigurację dla lepszej wydajności:

```bash
sudo vim /etc/nginx/sites-available/szalasapp
```

**Finalna konfiguracja:**

```nginx
# Przekierowanie HTTP → HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name szalasapp.kawak.uk;

    # Lokalizacja dla weryfikacji Let's Encrypt
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Przekieruj wszystko na HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

# Konfiguracja HTTPS
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name szalasapp.kawak.uk;

    # Certyfikaty SSL (Certbot je uzupełni automatycznie)
    ssl_certificate /etc/letsencrypt/live/szalasapp.kawak.uk/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/szalasapp.kawak.uk/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Dodatkowe nagłówki bezpieczeństwa
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Maksymalny rozmiar uploadu (dla zdjęć)
    client_max_body_size 50M;

    # Logi
    access_log /var/log/nginx/szalasapp_access.log;
    error_log /var/log/nginx/szalasapp_error.log;

    # Proxy do aplikacji Docker
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        
        # Timeouty
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buforowanie
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;
    }

    # Cache dla plików statycznych
    location /static/ {
        proxy_pass http://localhost:8080/static/;
        proxy_cache_valid 200 30d;
        add_header Cache-Control "public, immutable";
    }

    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8080/health;
        access_log off;
    }
}
```

Sprawdź i przeładuj:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 4. Auto-odnowienie certyfikatu

Certbot automatycznie konfiguruje odnowienie. Sprawdź:

```bash
# Sprawdź timer systemd
sudo systemctl status certbot.timer

# Test odnowienia (dry-run)
sudo certbot renew --dry-run
```

Certyfikaty Let's Encrypt są ważne 90 dni i automatycznie odnawiane co 60 dni.

## Przygotowanie aplikacji

### 1. Klonowanie repozytorium na serwer

```bash
# Przejdź do katalogu domowego
cd ~

# Sklonuj repozytorium
git clone https://github.com/YOUR_USERNAME/SzalasApp.git

# Lub skopiuj pliki przez SCP z lokalnej maszyny (Windows PowerShell):
# scp -r C:\Users\uzyt\PycharmProjects\SzalasApp root@YOUR_SERVER_IP:~/SzalasApp

cd SzalasApp
```

### 2. Przygotowanie pliku .env

```bash
# Skopiuj przykładowy plik
cp .env.example .env

# Edytuj plik .env
vim .env
```

**Wypełnij wszystkie wymagane wartości:**

```bash
# Flask Configuration
SECRET_KEY=WYGENERUJ_SILNY_KLUCZ_32_ZNAKI  # Użyj: python -c "import secrets; print(secrets.token_hex(32))"
DEBUG=False
PORT=8080
HOST=0.0.0.0

# Google Cloud / Firebase Configuration
GOOGLE_PROJECT_ID=twoj-projekt-id
GOOGLE_CLOUD_STORAGE_BUCKET_NAME=twoj-bucket-name
GOOGLE_API_KEY=twoj-api-key
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account.json

# ReCAPTCHA Configuration
RECAPTCHA_SITE_KEY=twoj-recaptcha-site-key
RECAPTCHA_PROJECT_ID=twoj-recaptcha-project-id

# OAuth Configuration
GOOGLE_CLIENT_ID=twoj-oauth-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=twoj-oauth-client-secret

# Email/SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=twoj-email@gmail.com
SMTP_PASSWORD="twoja-app-password"

# Application URL (WAŻNE: użyj HTTPS!)
BASE_URL=https://szalasapp.kawak.uk
```

**Generowanie SECRET_KEY:**

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Przygotowanie credentials

Utwórz folder i skopiuj service account JSON:

```bash
# Utwórz folder credentials
mkdir -p credentials

# Skopiuj service-account.json (z lokalnej maszyny przez SCP lub vim)
# Opcja 1: SCP z Windows PowerShell
# scp C:\Users\uzyt\PycharmProjects\SzalasApp\credentials\service-account.json root@YOUR_SERVER_IP:~/SzalasApp/credentials/

# Opcja 2: Ręcznie utworzyć plik
vim credentials/service-account.json
# Wklej zawartość JSON

# Ustaw odpowiednie uprawnienia
chmod 600 credentials/service-account.json
```

### 4. Aktualizacja OAuth Redirect URIs

**WAŻNE:** W Google Cloud Console dodaj nowy Redirect URI:

1. Przejdź do [Google Cloud Console](https://console.cloud.google.com/)
2. Wybierz projekt
3. **APIs & Services** → **Credentials**
4. Kliknij na OAuth 2.0 Client ID
5. Dodaj do **Authorized redirect URIs**:
   ```
   https://szalasapp.kawak.uk/oauth2callback
   ```
6. Zapisz zmiany

### 5. Aktualizacja reCAPTCHA Domain

W Google Cloud Console (reCAPTCHA):
1. Przejdź do **reCAPTCHA Enterprise**
2. Edytuj swój klucz
3. Dodaj domenę: `szalasapp.kawak.uk`
4. Zapisz

## Wdrożenie z Docker Compose {#wdrożenie-docker}

### 1. Budowanie i uruchomienie kontenera

```bash
# Przejdź do katalogu projektu
cd ~/SzalasApp

# Zbuduj i uruchom kontener w tle
docker compose up -d --build

# Sprawdź status
docker compose ps

# Sprawdź logi
docker compose logs -f
```

### 2. Weryfikacja aplikacji

```bash
# Sprawdź czy aplikacja odpowiada lokalnie
curl http://localhost:8080/health

# Sprawdź czy aplikacja jest dostępna przez HTTPS
curl https://szalasapp.kawak.uk
```

### 3. Podstawowe komendy Docker Compose

```bash
# Zatrzymanie aplikacji
docker compose stop

# Uruchomienie aplikacji
docker compose start

# Restart aplikacji
docker compose restart

# Zatrzymanie i usunięcie kontenerów
docker compose down

# Przebudowanie i restart
docker compose up -d --build --force-recreate

# Zobacz logi w czasie rzeczywistym
docker compose logs -f app

# Zobacz ostatnie 100 linii logów
docker compose logs --tail=100 app

# Wejście do kontenera (debugging)
docker compose exec app bash
```

### 4. Zarządzanie zasobami

**docker-compose.yml - dodatkowe opcje (opcjonalne):**

Możesz rozszerzyć `docker-compose.yml` o limity zasobów:

```yaml
services:
  app:
    # ...existing config...
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## Monitorowanie i utrzymanie

### 1. Monitorowanie logów aplikacji

```bash
# Logi Docker
docker compose logs -f app

# Logi Nginx
sudo tail -f /var/log/nginx/szalasapp_access.log
sudo tail -f /var/log/nginx/szalasapp_error.log

# Logi systemowe
sudo journalctl -u docker -f
sudo journalctl -u nginx -f
```

### 2. Monitorowanie zasobów

```bash
# Użycie zasobów przez kontenery
docker stats

# Użycie dysku
df -h

# Pamięć i CPU serwera
htop
# lub
top

# Zainstaluj htop jeśli nie jest zainstalowany
sudo apt install htop
```

### 3. Health checks

```bash
# Sprawdź endpoint health
curl http://localhost:8080/health

# Lub przez HTTPS
curl https://szalasapp.kawak.uk/health
```

### 4. Automatyczne restarty

Docker Compose jest skonfigurowany z `restart: unless-stopped`, co oznacza:
- Kontener automatycznie restartuje się po awarii
- Kontener uruchamia się automatycznie po restarcie serwera

### 5. Aktualizacje aplikacji

```bash
cd ~/SzalasApp

# Pobierz najnowszy kod
git pull

# Przebuduj i uruchom ponownie
docker compose up -d --build

# Sprawdź logi
docker compose logs -f
```

### 6. Czyszczenie Docker

```bash
# Usuń nieużywane obrazy
docker image prune -a

# Usuń nieużywane wolumeny
docker volume prune

# Usuń nieużywane sieci
docker network prune

# Kompletne czyszczenie (UWAGA: usuwa wszystko nieużywane)
docker system prune -a --volumes
```

## Backup i odzyskiwanie

### 1. Backup aplikacji

**Skrypt backup:**

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="szalasapp_backup_${DATE}.tar.gz"

# Utwórz katalog backup
mkdir -p ${BACKUP_DIR}

# Backup plików aplikacji
cd ~/SzalasApp
tar -czf ${BACKUP_DIR}/${BACKUP_FILE} \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='*.pyc' \
    .env credentials/ app/

echo "Backup utworzony: ${BACKUP_DIR}/${BACKUP_FILE}"

# Usuń backupy starsze niż 30 dni
find ${BACKUP_DIR} -name "szalasapp_backup_*.tar.gz" -mtime +30 -delete
```

Użycie:

```bash
# Nadaj uprawnienia
chmod +x backup.sh

# Uruchom backup
./backup.sh
```

### 2. Automatyczny backup (cron)

```bash
# Edytuj crontab
crontab -e

# Dodaj wpis (backup codziennie o 3:00 AM)
0 3 * * * /root/SzalasApp/backup.sh >> /var/log/szalasapp_backup.log 2>&1
```

### 3. Backup Firebase/Firestore

Firebase Firestore automatycznie tworzy backupy, ale możesz je eksportować:

```bash
# Użyj Google Cloud CLI (gcloud)
gcloud firestore export gs://your-backup-bucket/backups/$(date +%Y%m%d)
```

### 4. Odzyskiwanie z backup

```bash
# Zatrzymaj aplikację
cd ~/SzalasApp
docker compose down

# Przywróć pliki
cd ~
tar -xzf /root/backups/szalasapp_backup_YYYYMMDD_HHMMSS.tar.gz -C SzalasApp/

# Uruchom ponownie
cd ~/SzalasApp
docker compose up -d
```

## Troubleshooting

### Problem: Aplikacja nie startuje

```bash
# Sprawdź logi
docker compose logs app

# Sprawdź czy port 8080 jest zajęty
sudo netstat -tulpn | grep 8080

# Sprawdź czy kontener działa
docker compose ps

# Restart kontenera
docker compose restart app
```

### Problem: Nginx zwraca 502 Bad Gateway

**Przyczyny:**
1. Aplikacja Docker nie działa
2. Aplikacja nie nasłuchuje na porcie 8080
3. Firewall blokuje połączenie

**Rozwiązanie:**

```bash
# Sprawdź czy aplikacja działa
docker compose ps

# Sprawdź czy aplikacja odpowiada lokalnie
curl http://localhost:8080/health

# Sprawdź logi Nginx
sudo tail -f /var/log/nginx/szalasapp_error.log

# Sprawdź konfigurację Nginx
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# Restart aplikacji
docker compose restart app
```

### Problem: Certyfikat SSL nie działa

```bash
# Sprawdź status certyfikatu
sudo certbot certificates

# Test odnowienia
sudo certbot renew --dry-run

# Sprawdź logi Certbot
sudo tail -f /var/log/letsencrypt/letsencrypt.log

# Wymuś odnowienie (jeśli certyfikat wygasł)
sudo certbot renew --force-renewal

# Sprawdź konfigurację Nginx
sudo nginx -t
```

### Problem: OAuth nie działa (redirect error)

**Przyczyny:**
1. Nieprawidłowy BASE_URL w .env
2. Brak redirect URI w Google Cloud Console

**Rozwiązanie:**

1. Sprawdź `.env`:
   ```bash
   grep BASE_URL .env
   # Powinno być: BASE_URL=https://szalasapp.kawak.uk
   ```

2. Sprawdź Google Cloud Console:
   - Authorized redirect URIs: `https://szalasapp.kawak.uk/oauth2callback`

3. Restart aplikacji:
   ```bash
   docker compose restart app
   ```

### Problem: Wolna wydajność

**Rozwiązania:**

1. **Zwiększ liczbę workerów Gunicorn:**
   
   Edytuj `Dockerfile`:
   ```dockerfile
   CMD gunicorn --bind 0.0.0.0:${PORT} \
       --workers 8 \        # Zwiększ z 4 do 8
       --threads 4 \        # Zwiększ z 2 do 4
       --timeout 120 \
       --access-logfile - \
       --error-logfile - \
       app:app
   ```

2. **Zwiększ zasoby serwera** (RAM, CPU)

3. **Włącz caching w Nginx** (już skonfigurowane w poradniku)

### Problem: Brak miejsca na dysku

```bash
# Sprawdź użycie dysku
df -h

# Usuń stare obrazy Docker
docker image prune -a

# Usuń stare logi
sudo journalctl --vacuum-time=7d

# Usuń stare backupy
find /root/backups -mtime +30 -delete
```

### Problem: Nie można połączyć się z Firebase

**Rozwiązania:**

1. Sprawdź `credentials/service-account.json`:
   ```bash
   docker compose exec app cat /app/credentials/service-account.json
   ```

2. Sprawdź zmienne środowiskowe:
   ```bash
   docker compose exec app env | grep GOOGLE
   ```

3. Sprawdź logi aplikacji:
   ```bash
   docker compose logs app | grep -i firebase
   ```

### Przydatne komendy diagnostyczne

```bash
# Sprawdź wszystkie otwarte porty
sudo netstat -tulpn

# Sprawdź procesy Nginx
ps aux | grep nginx

# Sprawdź procesy Docker
ps aux | grep docker

# Sprawdź wykorzystanie zasobów
free -h
df -h
top

# Sprawdź logi systemowe
sudo journalctl -xe

# Test DNS
nslookup szalasapp.kawak.uk
dig szalasapp.kawak.uk

# Test połączenia HTTPS
curl -I https://szalasapp.kawak.uk

# Test certyfikatu SSL
openssl s_client -connect szalasapp.kawak.uk:443 -servername szalasapp.kawak.uk
```

## Checklist wdrożenia

### Przed wdrożeniem
- [ ] Serwer VPS zakupiony i skonfigurowany
- [ ] Domena `szalasapp.kawak.uk` skonfigurowana (rekord A)
- [ ] Docker i Docker Compose zainstalowane
- [ ] Nginx zainstalowany
- [ ] Firewall skonfigurowany (porty 80, 443, 22)
- [ ] Plik `.env` wypełniony wszystkimi wartościami
- [ ] `service-account.json` skopiowany
- [ ] OAuth redirect URI dodany w Google Cloud Console
- [ ] Domena dodana w reCAPTCHA

### Podczas wdrożenia
- [ ] DNS propagacja zakończona (nslookup działa)
- [ ] Nginx uruchomiony
- [ ] Certyfikat SSL uzyskany (Certbot)
- [ ] Docker Compose uruchomiony
- [ ] Aplikacja odpowiada na `http://localhost:8080/health`
- [ ] HTTPS działa: `https://szalasapp.kawak.uk`
- [ ] Logowanie OAuth działa
- [ ] reCAPTCHA działa
- [ ] Upload zdjęć działa

### Po wdrożeniu
- [ ] Auto-odnowienie certyfikatu skonfigurowane
- [ ] Backup skrypt utworzony
- [ ] Cron job dla backupów skonfigurowany
- [ ] Monitorowanie skonfigurowane
- [ ] Dokumentacja aktualizowana

## Dodatkowe zasoby

### Bezpieczeństwo

**Rekomendacje dodatkowe:**

1. **Fail2ban** - ochrona przed brute-force SSH:
   ```bash
   sudo apt install fail2ban
   sudo systemctl enable fail2ban
   ```

2. **Zmiana portu SSH** (opcjonalne):
   ```bash
   sudo vim /etc/ssh/sshd_config
   # Zmień Port 22 na np. Port 2222
   sudo systemctl restart sshd
   sudo ufw allow 2222/tcp
   ```

3. **Wyłącz logowanie root przez SSH**:
   ```bash
   sudo vim /etc/ssh/sshd_config
   # Ustaw: PermitRootLogin no
   # Utwórz najpierw użytkownika non-root!
   ```

### Monitoring zaawansowany

**Opcjonalne narzędzia:**

1. **Uptime monitoring**: UptimeRobot, Pingdom
2. **Error tracking**: Sentry
3. **Logs management**: Loki, ELK Stack
4. **Metrics**: Prometheus + Grafana

### CI/CD (opcjonalne)

Możesz skonfigurować automatyczne wdrożenia przez GitHub Actions:

1. Dodaj GitHub Secrets (IP serwera, SSH key)
2. Utwórz workflow `.github/workflows/deploy.yml`
3. Przy pushu do `main` automatycznie:
   - Połącz z serwerem
   - Git pull
   - Docker compose up --build

## Podsumowanie

Po wykonaniu wszystkich kroków aplikacja SzalasApp będzie:
- ✅ Dostępna pod `https://szalasapp.kawak.uk`
- ✅ Zabezpieczona certyfikatem SSL (Let's Encrypt)
- ✅ Uruchomiona w Docker container
- ✅ Automatycznie restartowana po awarii
- ✅ Automatycznie odnawiana certyfikat SSL
- ✅ Monitorowana i backupowana

**Główne komendy do zapamiętania:**

```bash
# Restart aplikacji
cd ~/SzalasApp && docker compose restart app

# Zobacz logi
docker compose logs -f app

# Aktualizacja aplikacji
git pull && docker compose up -d --build

# Restart Nginx
sudo systemctl restart nginx

# Sprawdź status
docker compose ps
sudo systemctl status nginx

# Odnów certyfikat SSL (manualnie)
sudo certbot renew
```

---

**Powodzenia z wdrożeniem! 🚀**

Jeśli napotkasz problemy, sprawdź sekcję [Troubleshooting](#troubleshooting) lub logi aplikacji.

