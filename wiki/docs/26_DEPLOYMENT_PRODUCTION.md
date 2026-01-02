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

## Wariant A: Nginx Proxy Manager (Jeśli już używasz NPM) {#nginx-proxy-manager}

**⚠️ Jeśli już masz zainstalowany Nginx Proxy Manager w osobnym Docker Compose, przejdź do tej sekcji zamiast standardowej konfiguracji Nginx.**

### Przegląd

Nginx Proxy Manager (NPM) to narzędzie z interfejsem webowym do zarządzania reverse proxy i certyfikatami SSL. Jeśli już go używasz, możesz łatwo podłączyć SzalasApp bez ręcznej konfiguracji Nginx.

### Architektura z NPM

```
Internet (HTTPS)
      ↓
[Port 443] Nginx Proxy Manager (Docker)
      ↓
[Sieć Docker] SzalasApp Container (port 8080)
      ↓
Firebase/Firestore + Google Cloud Storage
```

### Wymagania

- Nginx Proxy Manager już zainstalowany i działający
- Oba kontenery (NPM i SzalasApp) muszą być w tej samej sieci Docker lub możliwość komunikacji między sieciami

### Krok 1: Konfiguracja sieci Docker

**Opcja A: Wspólna sieć (zalecane)**

1. **Utwórz zewnętrzną sieć Docker** (jeśli jeszcze nie istnieje):

```bash
docker network create proxy-network
```

2. **Dodaj NPM do sieci** (jeśli jeszcze nie jest):

Edytuj docker-compose.yml Nginx Proxy Manager:

```yaml
services:
  nginx-proxy-manager:
    # ...existing config...
    networks:
      - proxy-network

networks:
  proxy-network:
    external: true
```

Restart NPM:

```bash
cd /path/to/nginx-proxy-manager
docker compose up -d
```

3. **Podłącz SzalasApp do tej samej sieci**

Utwórz `docker-compose.npm.yml` w katalogu SzalasApp:

```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: szalasapp
    # NIE eksponuj portów na zewnątrz - tylko wewnętrzna sieć Docker
    expose:
      - "8080"
    environment:
      - PORT=8080
      - HOST=0.0.0.0
      - DEBUG=${DEBUG:-False}
      - SECRET_KEY=${SECRET_KEY}
      - GOOGLE_PROJECT_ID=${GOOGLE_PROJECT_ID}
      - GOOGLE_CLOUD_STORAGE_BUCKET_NAME=${GOOGLE_CLOUD_STORAGE_BUCKET_NAME}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - RECAPTCHA_SITE_KEY=${RECAPTCHA_SITE_KEY}
      - RECAPTCHA_PROJECT_ID=${RECAPTCHA_PROJECT_ID}
      - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
      - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
      - SMTP_SERVER=${SMTP_SERVER:-smtp.gmail.com}
      - SMTP_PORT=${SMTP_PORT:-587}
      - SMTP_USERNAME=${SMTP_USERNAME}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
      - BASE_URL=${BASE_URL}
      - GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS:-/app/credentials/service-account.json}
    volumes:
      - ./credentials:/app/credentials:ro
    restart: unless-stopped
    networks:
      - proxy-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

networks:
  proxy-network:
    external: true
```

**Opcja B: Routing między sieciami Docker**

Jeśli wolisz zachować osobne sieci, NPM może routować do kontenera przez IP:

```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: szalasapp
    ports:
      - "127.0.0.1:8080:8080"  # Bind tylko do localhost
    # ...rest of config...
    networks:
      - szalasapp-network

networks:
  szalasapp-network:
    name: szalasapp-network
```

W tym przypadku w NPM użyjesz: `http://host.docker.internal:8080` (Windows/Mac) lub `http://172.17.0.1:8080` (Linux).

### Krok 2: Uruchomienie SzalasApp

```bash
cd ~/SzalasApp

# Przygotuj plik .env (patrz sekcja "Przygotowanie aplikacji")
cp .env.example .env
vim .env

# Uruchom z konfiguracją dla NPM
docker compose -f docker-compose.npm.yml up -d --build

# Sprawdź status
docker compose -f docker-compose.npm.yml ps

# Sprawdź logi
docker compose -f docker-compose.npm.yml logs -f
```

### Krok 3: Konfiguracja Proxy Host w NPM

1. **Otwórz Nginx Proxy Manager** w przeglądarce (np. `http://YOUR_SERVER_IP:81`)

2. **Zaloguj się** (domyślnie: admin@example.com / changeme)

3. **Dodaj nowy Proxy Host:**
   - Kliknij **"Proxy Hosts"** → **"Add Proxy Host"**

4. **Zakładka "Details":**
   - **Domain Names**: `szalasapp.kawak.uk`
   - **Scheme**: `http`
   - **Forward Hostname / IP**: 
     - Jeśli używasz wspólnej sieci: `szalasapp` (nazwa kontenera)
     - Jeśli osobne sieci (Windows/Mac): `host.docker.internal`
     - Jeśli osobne sieci (Linux): `172.17.0.1`
   - **Forward Port**: `8080`
   - **Cache Assets**: ✅ (włącz)
   - **Block Common Exploits**: ✅ (włącz)
   - **Websockets Support**: ✅ (włącz, jeśli planujesz)

5. **Zakładka "SSL":**
   - **SSL Certificate**: `Request a new SSL Certificate`
   - **Force SSL**: ✅ (włącz)
   - **HTTP/2 Support**: ✅ (włącz)
   - **HSTS Enabled**: ✅ (włącz)
   - **HSTS Subdomains**: ❌ (wyłącz, chyba że potrzebujesz)
   - **Email Address for Let's Encrypt**: Twój email
   - **I Agree to the Let's Encrypt Terms of Service**: ✅

6. **Zakładka "Advanced" (opcjonalne):**

   Dodaj niestandardową konfigurację Nginx dla lepszej wydajności:

   ```nginx
   # Zwiększ limit uploadu dla zdjęć
   client_max_body_size 50M;
   
   # Dodatkowe nagłówki bezpieczeństwa
   add_header X-Frame-Options "SAMEORIGIN" always;
   add_header X-Content-Type-Options "nosniff" always;
   add_header X-XSS-Protection "1; mode=block" always;
   add_header Referrer-Policy "strict-origin-when-cross-origin" always;
   
   # Przekazuj poprawne nagłówki do aplikacji
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
   ```

7. **Zapisz** - NPM automatycznie:
   - Skonfiguruje reverse proxy
   - Pobierze certyfikat SSL z Let's Encrypt
   - Skonfiguruje przekierowanie HTTP → HTTPS
   - Odnowi certyfikat automatycznie

### Krok 4: Weryfikacja

```bash
# Sprawdź czy aplikacja odpowiada wewnętrznie
docker exec szalasapp curl http://localhost:8080/health

# Sprawdź czy działa przez HTTPS
curl -I https://szalasapp.kawak.uk

# Otwórz w przeglądarce
# https://szalasapp.kawak.uk
```

### Krok 5: Testowanie OAuth i funkcjonalności

1. **Upewnij się, że BASE_URL w .env to HTTPS:**
   ```bash
   BASE_URL=https://szalasapp.kawak.uk
   ```

2. **Restart aplikacji po zmianie .env:**
   ```bash
   docker compose -f docker-compose.npm.yml restart app
   ```

3. **Sprawdź Google OAuth redirect URIs** (patrz sekcja "Przygotowanie aplikacji")

4. **Przetestuj:**
   - Logowanie przez Google
   - Upload zdjęć
   - Wszystkie funkcjonalności

### Zarządzanie

**Restart aplikacji:**
```bash
cd ~/SzalasApp
docker compose -f docker-compose.npm.yml restart app
```

**Logi aplikacji:**
```bash
docker compose -f docker-compose.npm.yml logs -f app
```

**Aktualizacja aplikacji:**
```bash
cd ~/SzalasApp
git pull
docker compose -f docker-compose.npm.yml up -d --build
```

**Zarządzanie certyfikatem:**
- W NPM: **SSL Certificates** → kliknij na certyfikat → **Renew**
- Auto-renewal: NPM automatycznie odnawia certyfikaty co 60 dni

**Logi NPM:**
```bash
# Przejdź do katalogu NPM
cd /path/to/nginx-proxy-manager
docker compose logs -f
```

### Troubleshooting dla NPM

**Problem: 502 Bad Gateway**

1. Sprawdź czy aplikacja działa:
   ```bash
   docker ps | grep szalasapp
   docker exec szalasapp curl http://localhost:8080/health
   ```

2. Sprawdź czy kontenery są w tej samej sieci:
   ```bash
   docker network inspect proxy-network
   # Powinny być widoczne: nginx-proxy-manager i szalasapp
   ```

3. Sprawdź konfigurację Forward Hostname w NPM:
   - Jeśli wspólna sieć: użyj nazwy kontenera (`szalasapp`)
   - Przetestuj ping: `docker exec nginx-proxy-manager ping szalasapp`

**Problem: SSL nie działa**

1. Sprawdź logi NPM:
   ```bash
   cd /path/to/nginx-proxy-manager
   docker compose logs certbot
   ```

2. Upewnij się, że DNS jest poprawnie skonfigurowany (Let's Encrypt weryfikuje przez port 80)

3. Spróbuj ręcznie odnowić certyfikat w interfejsie NPM

**Problem: OAuth redirect error**

1. Sprawdź BASE_URL w .env:
   ```bash
   docker exec szalasapp env | grep BASE_URL
   # Musi być: BASE_URL=https://szalasapp.kawak.uk
   ```

2. Sprawdź Google Cloud Console:
   - Authorized redirect URIs: `https://szalasapp.kawak.uk/oauth2callback`

### Zalety używania NPM

✅ Łatwy interfejs webowy (nie trzeba edytować plików Nginx)  
✅ Automatyczne zarządzanie certyfikatami SSL  
✅ Łatwe dodawanie wielu aplikacji/domen  
✅ Wbudowane logi i monitoring  
✅ Access Lists (kontrola dostępu)  
✅ Stream (TCP/UDP proxy)  

---

### Zaawansowane funkcje NPM dla SzalasApp

#### 1. Access Lists - Ograniczanie dostępu

Możesz ograniczyć dostęp do aplikacji tylko dla określonych adresów IP:

**Krok 1: Utwórz Access List**
1. W NPM: **Access Lists** → **Add Access List**
2. Nazwa: `SzalasApp Internal Access`
3. **Authorization** → **Allow**:
   ```
   192.168.1.0/24    # Sieć lokalna
   10.0.0.0/8        # VPN
   YOUR_HOME_IP      # Twój IP domowy
   ```

**Krok 2: Przypisz do Proxy Host**
1. **Proxy Hosts** → Edytuj `szalasapp.kawak.uk`
2. Zakładka **Details**
3. **Access List**: Wybierz `SzalasApp Internal Access`
4. **Save**

**Rezultat:** Tylko wybrane IP mogą dostać się do aplikacji

---

#### 2. Basic Authentication - Dodatkowa warstwa ochrony

Możesz dodać podstawowe uwierzytelnianie HTTP:

1. **Access Lists** → **Add Access List**
2. Nazwa: `SzalasApp Password Protection`
3. **Authorization** → **Username/Password**:
   - Username: `admin`
   - Password: `secure-password-123`
4. Przypisz do Proxy Host (jak wyżej)

**Rezultat:** Użytkownicy muszą podać login/hasło przed dostępem do OAuth

---

#### 3. Custom Locations - Zaawansowany routing

Jeśli potrzebujesz różnych ustawień dla różnych ścieżek:

W NPM Proxy Host → **Custom Locations** → **Add Location**

**Przykład 1: Różne timeouty dla uploadów**
```
Location: /upload
Scheme: http
Forward Hostname: szalasapp
Forward Port: 8080
Advanced:
  proxy_read_timeout 300s;
  proxy_send_timeout 300s;
  client_max_body_size 100M;
```

**Przykład 2: Cache dla statycznych plików**
```
Location: /static
Scheme: http
Forward Hostname: szalasapp
Forward Port: 8080
Advanced:
  proxy_cache_valid 200 1d;
  add_header X-Cache-Status $upstream_cache_status;
```

---

#### 4. Monitorowanie przez NPM

**Sprawdzanie logów w czasie rzeczywistym:**

1. W NPM: **Hosts** → **Proxy Hosts**
2. Kliknij na `szalasapp.kawak.uk`
3. **View Logs**

**Rodzaje logów:**
- **Access Logs**: Wszystkie żądania HTTP
- **Error Logs**: Błędy proxy (502, 503, etc.)

**Albo przez CLI:**
```bash
cd /path/to/nginx-proxy-manager

# Access logs
docker compose exec app tail -f /data/logs/proxy-host-1_access.log

# Error logs
docker compose exec app tail -f /data/logs/proxy-host-1_error.log
```

---

#### 5. Backup konfiguracji NPM

**Pełny backup NPM (z certyfikatami):**

```bash
cd /path/to/nginx-proxy-manager

# Backup wszystkiego
tar -czf npm-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  data/ \
  letsencrypt/

# Lista backupów
ls -lh npm-backup-*.tar.gz

# Przywracanie (jeśli potrzeba)
docker compose down
tar -xzf npm-backup-20260102-120000.tar.gz
docker compose up -d
```

**Backup tylko konfiguracji SzalasApp:**

```bash
# Eksportuj konfigurację proxy host do pliku
docker compose exec app sqlite3 /data/database.sqlite \
  "SELECT * FROM proxy_host WHERE domain_names LIKE '%szalasapp%';" \
  > szalasapp-npm-config.sql
```

---

### Migracja do NPM z innych rozwiązań

#### Jeśli już masz działający Nginx (bez NPM)

**Scenariusz:** Masz standardowy Nginx i chcesz przenieść się na NPM

**Krok 1: Zachowaj istniejącą konfigurację**
```bash
# Backup istniejącej konfiguracji
sudo cp /etc/nginx/sites-enabled/szalasapp /etc/nginx/sites-enabled/szalasapp.backup

# Wyłącz istniejący site
sudo rm /etc/nginx/sites-enabled/szalasapp
sudo systemctl reload nginx
```

**Krok 2: Zainstaluj NPM**
```bash
cd ~
mkdir nginx-proxy-manager
cd nginx-proxy-manager

# Utwórz docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  app:
    image: 'jc21/nginx-proxy-manager:latest'
    restart: unless-stopped
    ports:
      - '80:80'
      - '443:443'
      - '81:81'
    volumes:
      - ./data:/data
      - ./letsencrypt:/etc/letsencrypt
    networks:
      - proxy-network

networks:
  proxy-network:
    external: true
EOF

# Uruchom NPM
docker network create proxy-network
docker compose up -d
```

**Krok 3: Konfiguruj w NPM (jak opisano wcześniej)**

**Krok 4: Testuj**
```bash
# Test przez NPM
curl -I https://szalasapp.kawak.uk

# Jeśli działa, możesz usunąć stary Nginx
sudo systemctl stop nginx
sudo systemctl disable nginx
```

---

#### Jeśli masz Traefik

**Scenariusz:** Używasz Traefik i chcesz przejść na NPM

**Krok 1: Zachowaj labels Traefik (na później)**
```bash
# Zapisz labels z docker-compose.yml
docker compose config > docker-compose-traefik-backup.yml
```

**Krok 2: Usuń labels Traefik z SzalasApp**
```yaml
# Usuń sekcję labels:
# labels:
#   - "traefik.enable=true"
#   - "traefik.http.routers..."
```

**Krok 3: Dodaj do sieci NPM**
```yaml
services:
  app:
    # ...existing config...
    networks:
      - proxy-network  # Dodaj tę linię
```

**Krok 4: Konfiguruj w NPM**

---

### Najlepsze praktyki dla NPM + SzalasApp

#### 1. **Używaj zewnętrznej sieci Docker**

✅ **Dobrze:**
```yaml
networks:
  proxy-network:
    external: true
```

❌ **Źle:**
```yaml
networks:
  proxy-network:
    driver: bridge
```

**Dlaczego?** Zewnętrzna sieć przetrwa restart NPM i jest współdzielona z innymi aplikacjami.

---

#### 2. **Nie eksponuj portów aplikacji na zewnątrz**

✅ **Dobrze:** (tylko wewnętrzna sieć Docker)
```yaml
services:
  app:
    expose:
      - "8080"
```

❌ **Źle:** (dostępne bezpośrednio z internetu)
```yaml
services:
  app:
    ports:
      - "8080:8080"
```

**Dlaczego?** Aplikacja powinna być dostępna TYLKO przez NPM, nie bezpośrednio.

---

#### 3. **Używaj nazw kontenerów w Forward Hostname**

✅ **Dobrze:**
```
Forward Hostname: szalasapp
Forward Port: 8080
```

❌ **Źle:**
```
Forward Hostname: 172.17.0.1
Forward Port: 8080
```

**Dlaczego?** Nazwy DNS są stabilne, IP mogą się zmieniać.

---

#### 4. **Włącz wszystkie opcje bezpieczeństwa**

✅ **W NPM Details:**
- ✅ Cache Assets
- ✅ Block Common Exploits
- ✅ Websockets Support (jeśli używasz)

✅ **W NPM SSL:**
- ✅ Force SSL
- ✅ HTTP/2 Support
- ✅ HSTS Enabled

---

#### 5. **Regularnie sprawdzaj certyfikaty**

```bash
# Sprawdź datę wygaśnięcia certyfikatu
echo | openssl s_client -connect szalasapp.kawak.uk:443 2>/dev/null | \
  openssl x509 -noout -dates

# Lub w przeglądarce:
# Kliknij kłódkę → Certificate → Valid until
```

NPM automatycznie odnawia certyfikaty, ale dobrze jest sprawdzić.

---

#### 6. **Monitoruj logi regularnie**

```bash
# Sprawdzaj błędy 502/503
docker compose -f docker-compose.npm.yml logs app | grep -E "502|503"

# Sprawdzaj nietypowe żądania
cd /path/to/nginx-proxy-manager
docker compose exec app tail -100 /data/logs/proxy-host-1_access.log | grep -v "200"
```

---

### Skalowanie z NPM

Jeśli planujesz dodać więcej aplikacji lub zwiększyć ruch:

#### 1. **Dodaj więcej aplikacji do tej samej sieci**

```bash
# Każda nowa aplikacja:
cd ~/NewApp
docker compose up -d

# W NPM dodaj nowy Proxy Host:
# - Domain: newapp.kawak.uk
# - Forward to: newapp-container:port
```

Wszystkie aplikacje mogą używać tej samej sieci `proxy-network`.

---

#### 2. **Load Balancing (jeśli masz wiele instancji)**

Jeśli uruchomisz wiele kontenerów SzalasApp:

```yaml
# docker-compose.npm.yml
services:
  app1:
    build: .
    container_name: szalasapp-1
    expose: ["8080"]
    networks: [proxy-network]
  
  app2:
    build: .
    container_name: szalasapp-2
    expose: ["8080"]
    networks: [proxy-network]
```

W NPM **Custom Locations** → **Advanced**:
```nginx
upstream szalasapp_backend {
    server szalasapp-1:8080;
    server szalasapp-2:8080;
}

location / {
    proxy_pass http://szalasapp_backend;
}
```

---

### FAQ dla NPM

**Q: Czy NPM działa z Cloudflare?**  
A: Tak! Ustaw Cloudflare w trybie "DNS only" (szara chmurka) podczas konfiguracji SSL w NPM. Po uzyskaniu certyfikatu możesz włączyć proxy Cloudflare (pomarańczowa chmurka).

**Q: Czy mogę mieć wiele domen dla jednej aplikacji?**  
A: Tak! W NPM **Domain Names** dodaj wiele domen oddzielonych spacją:
```
szalasapp.kawak.uk www.szalasapp.kawak.uk app.kawak.uk
```

**Q: Czy NPM wspiera IPv6?**  
A: Tak, domyślnie. Upewnij się, że twój serwer ma adres IPv6.

**Q: Jak zmienić domyślny port 81 NPM Admin?**  
A: W docker-compose.yml NPM:
```yaml
ports:
  - '8081:81'  # Zmień 8081 na dowolny port
```

**Q: Czy mogę używać wildcards SSL (*.kawak.uk)?**  
A: Tak, ale wymaga konfiguracji DNS API w NPM. Wildcard SSL wymaga weryfikacji DNS, nie HTTP.

**Q: NPM zużywa dużo RAM, co zrobić?**  
A: NPM zazwyczaj używa 200-500MB RAM. Jeśli więcej:
```bash
# Wyczyść stare logi
docker compose exec app sh -c "rm -f /data/logs/*.log.*"
docker compose restart
```

---

### Przejdź dalej

Po skonfigurowaniu NPM przejdź do:
- [Przygotowanie aplikacji](#przygotowanie-aplikacji) - Konfiguracja zmiennych środowiskowych
- [Monitorowanie i utrzymanie](#monitorowanie) - Monitoring produkcyjny
- [Backup i odzyskiwanie](#backup) - Tworzenie kopii zapasowych
- [Troubleshooting](#troubleshooting) - Rozwiązywanie problemów

**Dodatkowe zasoby:**
- 📄 [DEPLOYMENT_NPM_QUICKSTART.md](../../DEPLOYMENT_NPM_QUICKSTART.md) - Szybka instrukcja
- ✅ [DEPLOYMENT_NPM_CHECKLIST.md](../../DEPLOYMENT_NPM_CHECKLIST.md) - Lista kontrolna
- ⚡ [NPM_CHEATSHEET.md](../../NPM_CHEATSHEET.md) - Ściągawka komend
- 🎯 [NPM_QUICK_REFERENCE.md](../../NPM_QUICK_REFERENCE.md) - Szybka referencja

---

### Automatyzacja wdrożeń z NPM

#### GitHub Actions - Automatyczne wdrożenie

Możesz skonfigurować automatyczne wdrożenie przy każdym pushu do głównej gałęzi.

**Krok 1: Utwórz plik `.github/workflows/deploy.yml`**

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Deploy to server
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.SERVER_HOST }}
        username: ${{ secrets.SERVER_USER }}
        key: ${{ secrets.SSH_PRIVATE_KEY }}
        script: |
          cd ~/SzalasApp
          git pull origin main
          docker compose -f docker-compose.npm.yml up -d --build
          
          # Sprawdź czy aplikacja działa
          sleep 10
          docker exec szalasapp curl -f http://localhost:8080/health || exit 1
          
          echo "✅ Deployment successful!"
```

**Krok 2: Dodaj secrets w GitHub**

W repozytorium GitHub: **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Dodaj:
- `SERVER_HOST`: Adres IP serwera
- `SERVER_USER`: Nazwa użytkownika SSH (np. `root`)
- `SSH_PRIVATE_KEY`: Twój prywatny klucz SSH

**Krok 3: Push i testuj**

```bash
git add .github/workflows/deploy.yml
git commit -m "Add automated deployment"
git push origin main
```

GitHub automatycznie wdroży aplikację!

---

#### Webhook - Wdrożenie przez webhook

Możesz utworzyć prosty webhook, który wdroży aplikację:

**Krok 1: Utwórz skrypt na serwerze**

```bash
# Na serwerze
sudo vim /usr/local/bin/deploy-szalasapp.sh
```

```bash
#!/bin/bash

# Webhook deploy script
LOG_FILE="/var/log/szalasapp-deploy.log"
REPO_DIR="/root/SzalasApp"

echo "$(date): Deployment started" >> $LOG_FILE

cd $REPO_DIR || exit 1

# Pull latest code
git pull origin main >> $LOG_FILE 2>&1

# Rebuild and restart
docker compose -f docker-compose.npm.yml up -d --build >> $LOG_FILE 2>&1

# Health check
sleep 10
if docker exec szalasapp curl -f http://localhost:8080/health; then
    echo "$(date): Deployment successful ✅" >> $LOG_FILE
    exit 0
else
    echo "$(date): Deployment failed ❌" >> $LOG_FILE
    exit 1
fi
```

```bash
# Nadaj uprawnienia
sudo chmod +x /usr/local/bin/deploy-szalasapp.sh
```

**Krok 2: Zainstaluj webhook listener**

```bash
# Zainstaluj webhook
sudo apt install -y webhook

# Utwórz konfigurację
sudo vim /etc/webhook.conf
```

```json
[
  {
    "id": "deploy-szalasapp",
    "execute-command": "/usr/local/bin/deploy-szalasapp.sh",
    "command-working-directory": "/root/SzalasApp",
    "response-message": "Deployment triggered!",
    "trigger-rule": {
      "match": {
        "type": "value",
        "value": "YOUR_SECRET_TOKEN",
        "parameter": {
          "source": "header",
          "name": "X-Hub-Signature"
        }
      }
    }
  }
]
```

**Krok 3: Uruchom webhook service**

```bash
# Utwórz systemd service
sudo vim /etc/systemd/system/webhook.service
```

```ini
[Unit]
Description=Webhook Server
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/webhook -hooks /etc/webhook.conf -verbose -port 9000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Uruchom service
sudo systemctl daemon-reload
sudo systemctl enable webhook
sudo systemctl start webhook

# Sprawdź status
sudo systemctl status webhook
```

**Krok 4: Skonfiguruj NPM dla webhooka**

W NPM dodaj nowy Proxy Host:
- Domain: `webhook.kawak.uk`
- Forward to: `localhost:9000`
- SSL: Request certificate

**Krok 5: Testuj webhook**

```bash
curl -X POST https://webhook.kawak.uk/hooks/deploy-szalasapp \
  -H "X-Hub-Signature: YOUR_SECRET_TOKEN"
```

**Krok 6: Dodaj w GitHub**

Repository → **Settings** → **Webhooks** → **Add webhook**
- Payload URL: `https://webhook.kawak.uk/hooks/deploy-szalasapp`
- Content type: `application/json`
- Secret: `YOUR_SECRET_TOKEN`
- Events: Push

Teraz każdy push do repo automatycznie wdroży aplikację!

---

#### Watchtower - Automatyczne aktualizacje obrazów Docker

Watchtower automatycznie sprawdza i aktualizuje obrazy Docker.

**Krok 1: Dodaj Watchtower do docker-compose.npm.yml**

```yaml
services:
  app:
    # ...existing config...
    image: szalasapp:latest
    labels:
      - "com.centurylinklabs.watchtower.enable=true"
  
  watchtower:
    image: containrrr/watchtower
    container_name: watchtower
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    command: --interval 300 --cleanup --label-enable
    restart: unless-stopped
    networks:
      - proxy-network
```

**Krok 2: Build i push obrazu (jeśli używasz registry)**

```bash
# Build image
docker build -t your-registry.com/szalasapp:latest .

# Push to registry
docker push your-registry.com/szalasapp:latest
```

Watchtower co 5 minut sprawdzi nowe wersje i automatycznie zaktualizuje!

---

#### Rollback - Cofnięcie wdrożenia

Jeśli wdrożenie pójdzie źle, szybko cofnij:

**Metoda 1: Git rollback**

```bash
cd ~/SzalasApp

# Zobacz ostatnie commity
git log --oneline -5

# Cofnij do poprzedniej wersji
git checkout <previous-commit-hash>

# Rebuild
docker compose -f docker-compose.npm.yml up -d --build

# Lub reset do poprzedniego commita
git reset --hard HEAD~1
git push -f origin main
```

**Metoda 2: Docker image rollback**

```bash
# Zobacz historię obrazów
docker images szalasapp

# Uruchom poprzednią wersję
docker tag szalasapp:latest szalasapp:backup
docker run -d --name szalasapp-old szalasapp:backup
```

**Metoda 3: Snapshot serwera (jeśli masz)**

W panelu VPS (DigitalOcean, Linode, etc.):
1. **Snapshots** → **Restore from snapshot**
2. Wybierz snapshot sprzed wdrożenia
3. Restore

---

#### Blue-Green Deployment z NPM

Wdróż nową wersję bez downtime:

**Krok 1: Uruchom drugą instancję (green)**

```yaml
# docker-compose.npm.yml
services:
  app-blue:
    container_name: szalasapp-blue
    # ...config...
  
  app-green:
    container_name: szalasapp-green
    # ...config...
```

**Krok 2: Wdróż nową wersję na green**

```bash
docker compose -f docker-compose.npm.yml up -d szalasapp-green --build
```

**Krok 3: Test green**

```bash
docker exec szalasapp-green curl http://localhost:8080/health
```

**Krok 4: Przełącz w NPM**

W NPM Proxy Host → **Edit** → **Forward Hostname**: zmień z `szalasapp-blue` na `szalasapp-green`

**Krok 5: Usuń starą wersję (blue)**

```bash
docker compose -f docker-compose.npm.yml stop szalasapp-blue
docker compose -f docker-compose.npm.yml rm szalasapp-blue
```

Zero downtime! ✅

---

#### Monitoring wdrożeń

**Slack notifications dla wdrożeń:**

```bash
# W deploy-szalasapp.sh dodaj na końcu:

SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

if [ $? -eq 0 ]; then
  curl -X POST -H 'Content-type: application/json' \
    --data '{"text":"✅ SzalasApp deployed successfully!"}' \
    $SLACK_WEBHOOK
else
  curl -X POST -H 'Content-type: application/json' \
    --data '{"text":"❌ SzalasApp deployment failed!"}' \
    $SLACK_WEBHOOK
fi
```

**Email notifications:**

```bash
# W deploy-szalasapp.sh:
if [ $? -eq 0 ]; then
  echo "Deployment successful" | mail -s "✅ SzalasApp deployed" admin@example.com
else
  echo "Deployment failed" | mail -s "❌ SzalasApp deployment error" admin@example.com
fi
```

**Discord notifications:**

```bash
DISCORD_WEBHOOK="https://discord.com/api/webhooks/YOUR/WEBHOOK"

curl -X POST -H 'Content-Type: application/json' \
  -d "{\"content\":\"✅ SzalasApp deployed at $(date)\"}" \
  $DISCORD_WEBHOOK
```

---

### Zero-Downtime Deployment - Best Practices

#### 1. Health Checks przed przełączeniem

```bash
# deploy-szalasapp.sh
docker compose -f docker-compose.npm.yml up -d --build

# Czekaj na health check
for i in {1..30}; do
  if docker exec szalasapp curl -f http://localhost:8080/health; then
    echo "✅ App is healthy"
    break
  fi
  if [ $i -eq 30 ]; then
    echo "❌ Health check failed after 30 attempts"
    exit 1
  fi
  echo "⏳ Waiting for app to be ready... ($i/30)"
  sleep 2
done
```

#### 2. Database migrations przed wdrożeniem

```bash
# deploy-szalasapp.sh (przed restart)

# Uruchom migrations
docker exec szalasapp python /app/scripts/migrate.py

# Jeśli failed, rollback
if [ $? -ne 0 ]; then
  echo "❌ Migration failed, rolling back..."
  git reset --hard HEAD~1
  docker compose -f docker-compose.npm.yml up -d --build
  exit 1
fi
```

#### 3. Backup przed wdrożeniem

```bash
# deploy-szalasapp.sh (na początku)

# Backup obecnej wersji
BACKUP_DIR="/backups/szalasapp"
mkdir -p $BACKUP_DIR

# Backup kodu
tar -czf $BACKUP_DIR/code-$(date +%Y%m%d-%H%M%S).tar.gz \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  /root/SzalasApp

# Backup Docker image
docker save szalasapp:latest | gzip > $BACKUP_DIR/image-$(date +%Y%m%d-%H%M%S).tar.gz

echo "✅ Backup completed"
```

---

## Wariant B: Standardowy Nginx (Bez NPM) {#konfiguracja-ssl}

**⚠️ Pomiń tę sekcję jeśli używasz Nginx Proxy Manager (patrz [Wariant A](#nginx-proxy-manager))**

### Konfiguracja SSL/HTTPS z Nginx i Let's Encrypt

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

