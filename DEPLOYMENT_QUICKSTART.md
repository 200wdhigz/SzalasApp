# Szybki przewodnik wdrożenia SzalasApp z HTTPS

> Uproszczona instrukcja wdrożenia aplikacji na serwerze z Docker i SSL/HTTPS

## 🎯 Cel

Wdrożenie aplikacji pod adresem: **https://szalasapp.kawak.uk**

## 📋 Wymagania

- Serwer VPS (Ubuntu 22.04, 2GB RAM, 20GB dysk)
- Domena: `kawak.uk` z dostępem do DNS
- Service Account JSON z Google Cloud
- OAuth credentials

## ⚡ Szybkie wdrożenie (5 kroków)

### 1️⃣ Konfiguracja DNS

W panelu DNS dodaj rekord A:

```
Type: A
Name: szalasapp
Value: [IP_TWOJEGO_SERWERA]
TTL: 3600
```

Sprawdź po 5-15 minutach:
```bash
nslookup szalasapp.kawak.uk
```

### 2️⃣ Przygotowanie serwera

Połącz się przez SSH i uruchom:

```bash
# Pobierz i uruchom skrypt setup
wget https://raw.githubusercontent.com/YOUR_REPO/SzalasApp/main/deploy-setup.sh
chmod +x deploy-setup.sh
./deploy-setup.sh
```

Skrypt automatycznie:
- ✅ Zaktualizuje system
- ✅ Skonfiguruje firewall
- ✅ Zainstaluje Docker, Nginx, Certbot
- ✅ Skonfiguruje Nginx dla twojej domeny
- ✅ Uzyska certyfikat SSL

**Lub ręcznie (bez skryptu):**

```bash
# Aktualizuj system
sudo apt update && sudo apt upgrade -y

# Zainstaluj Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Zainstaluj Docker Compose
sudo apt install docker-compose-plugin

# Zainstaluj Nginx i Certbot
sudo apt install -y nginx certbot python3-certbot-nginx

# Skonfiguruj firewall
sudo ufw enable
sudo ufw allow 22,80,443/tcp
```

### 3️⃣ Konfiguracja Nginx

Utwórz plik `/etc/nginx/sites-available/szalasapp`:

```nginx
server {
    listen 80;
    server_name szalasapp.kawak.uk;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Aktywuj:

```bash
sudo ln -s /etc/nginx/sites-available/szalasapp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Uzyskaj certyfikat SSL:

```bash
sudo certbot --nginx -d szalasapp.kawak.uk --email twoj@email.com --agree-tos
```

### 4️⃣ Przygotowanie aplikacji

```bash
# Sklonuj repozytorium
cd ~
git clone https://github.com/YOUR_REPO/SzalasApp.git
cd SzalasApp

# Skopiuj i wypełnij .env
cp .env.example .env
nano .env  # lub vim .env
```

**Najważniejsze zmienne w .env:**

```bash
SECRET_KEY=WYGENERUJ_LOSOWY_KLUCZ_32_ZNAKI
DEBUG=False
APP_URL=https://szalasapp.kawak.uk

GOOGLE_PROJECT_ID=twoj-projekt-id
GOOGLE_CLOUD_STORAGE_BUCKET_NAME=twoj-bucket
GOOGLE_CLIENT_ID=twoj-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=twoj-secret

RECAPTCHA_SITE_KEY=twoj-site-key
RECAPTCHA_PROJECT_ID=twoj-projekt-id
```

Wygeneruj SECRET_KEY:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Skopiuj credentials:
```bash
mkdir -p credentials
# Skopiuj service-account.json (SCP lub vim)
nano credentials/service-account.json
chmod 600 credentials/service-account.json
```

### 5️⃣ Uruchomienie aplikacji

```bash
# Zbuduj i uruchom
docker compose up -d --build

# Sprawdź status
docker compose ps

# Zobacz logi
docker compose logs -f
```

Sprawdź w przeglądarce: **https://szalasapp.kawak.uk** 🚀

## 🔧 Podstawowe komendy

```bash
# Restart aplikacji
docker compose restart app

# Zatrzymanie
docker compose stop

# Uruchomienie
docker compose start

# Logi
docker compose logs -f app

# Aktualizacja (po git pull)
docker compose up -d --build
```

## 🔒 OAuth - WAŻNE!

W Google Cloud Console dodaj redirect URI:
```
https://szalasapp.kawak.uk/oauth2callback
```

W reCAPTCHA dodaj domenę:
```
szalasapp.kawak.uk
```

## 💾 Backup

Skopiuj skrypt backup:

```bash
chmod +x backup.sh

# Ręczny backup
./backup.sh

# Automatyczny backup (codziennie o 3:00)
crontab -e
# Dodaj linię:
0 3 * * * /root/SzalasApp/backup.sh >> /var/log/szalasapp_backup.log 2>&1
```

## 🆘 Problemy?

### 502 Bad Gateway
```bash
# Sprawdź czy aplikacja działa
docker compose ps
curl http://localhost:8080/health

# Restart
docker compose restart app
sudo systemctl restart nginx
```

### SSL nie działa
```bash
# Sprawdź certyfikat
sudo certbot certificates

# Wymuszenie odnowienia
sudo certbot renew --force-renewal
```

### DNS nie działa
```bash
# Sprawdź propagację DNS
nslookup szalasapp.kawak.uk
dig szalasapp.kawak.uk +short
```

## 📚 Pełna dokumentacja

Zobacz: [26_DEPLOYMENT_PRODUCTION.md](./26_DEPLOYMENT_PRODUCTION.md)

## ✅ Checklist

- [ ] Serwer VPS przygotowany
- [ ] DNS skonfigurowane (rekord A)
- [ ] Docker zainstalowany
- [ ] Nginx zainstalowany
- [ ] Certbot zainstalowany
- [ ] Certyfikat SSL uzyskany
- [ ] Plik .env wypełniony
- [ ] service-account.json skopiowany
- [ ] OAuth redirect URI dodany
- [ ] Domena w reCAPTCHA dodana
- [ ] Aplikacja uruchomiona
- [ ] HTTPS działa ✨

---

**Powodzenia! 🚀**

W razie problemów sprawdź logi: `docker compose logs -f app`

