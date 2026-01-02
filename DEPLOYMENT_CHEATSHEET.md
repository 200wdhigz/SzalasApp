# Cheatsheet - Przydatne komendy dla SzalasApp

## 🚀 Wdrożenie

### Pierwszy raz - Setup serwera (Linux)
```bash
# Na serwerze - automatyczny setup
wget https://raw.githubusercontent.com/YOUR_REPO/SzalasApp/main/deploy-setup.sh
chmod +x deploy-setup.sh
./deploy-setup.sh
```

### Z Windows na serwer
```powershell
.\deploy-from-windows.ps1 -ServerIP 123.456.789.012 -Domain szalasapp.kawak.uk
```

### Ręczne wdrożenie
```bash
# Na serwerze
cd ~/SzalasApp
cp .env.example .env
nano .env  # Wypełnij wszystkie wartości

# Uruchom aplikację
docker compose up -d --build
```

## 🔧 Zarządzanie aplikacją

### Docker Compose
```bash
# Status
docker compose ps

# Logi (na żywo)
docker compose logs -f

# Logi (ostatnie 100 linii)
docker compose logs --tail=100

# Restart aplikacji
docker compose restart

# Zatrzymaj
docker compose stop

# Uruchom
docker compose start

# Zatrzymaj i usuń
docker compose down

# Przebuduj i uruchom ponownie
docker compose up -d --build --force-recreate

# Wejdź do kontenera (debugging)
docker compose exec app bash
```

### Docker (podstawowe)
```bash
# Lista kontenerów
docker ps

# Statystyki zasobów
docker stats

# Czyszczenie
docker system prune -a        # Usuń wszystko nieużywane
docker image prune -a         # Usuń stare obrazy
docker volume prune           # Usuń nieużywane wolumeny
```

## 🌐 Nginx

### Zarządzanie
```bash
# Test konfiguracji
sudo nginx -t

# Przeładuj konfigurację
sudo systemctl reload nginx

# Restart
sudo systemctl restart nginx

# Status
sudo systemctl status nginx

# Zatrzymaj
sudo systemctl stop nginx

# Uruchom
sudo systemctl start nginx
```

### Logi
```bash
# Logi dostępu (live)
sudo tail -f /var/log/nginx/szalasapp_access.log

# Logi błędów (live)
sudo tail -f /var/log/nginx/szalasapp_error.log

# Ostatnie 50 linii
sudo tail -n 50 /var/log/nginx/szalasapp_error.log
```

## 🔒 SSL/Certbot

### Zarządzanie certyfikatami
```bash
# Lista certyfikatów
sudo certbot certificates

# Test odnowienia (dry-run)
sudo certbot renew --dry-run

# Wymuś odnowienie
sudo certbot renew --force-renewal

# Automatyczne odnowienie (sprawdź status)
sudo systemctl status certbot.timer

# Logi Certbot
sudo tail -f /var/log/letsencrypt/letsencrypt.log
```

### Uzyskanie nowego certyfikatu
```bash
sudo certbot --nginx -d szalasapp.kawak.uk --email twoj@email.com --agree-tos
```

## 💾 Backup

### Ręczny backup
```bash
cd ~/SzalasApp
./backup.sh
```

### Lista backupów
```bash
ls -lh /root/backups/
```

### Przywracanie z backupu
```bash
# Zatrzymaj aplikację
cd ~/SzalasApp
docker compose down

# Przywróć pliki
tar -xzf /root/backups/szalasapp_backup_YYYYMMDD_HHMMSS.tar.gz -C ~/SzalasApp/

# Uruchom ponownie
docker compose up -d
```

### Automatyczny backup (cron)
```bash
# Edytuj crontab
crontab -e

# Dodaj (backup codziennie o 3:00 AM):
0 3 * * * /root/SzalasApp/backup.sh >> /var/log/szalasapp_backup.log 2>&1
```

## 🔍 Diagnostyka

### Sprawdzenie statusu
```bash
# Aplikacja
curl http://localhost:8080/health

# HTTPS
curl https://szalasapp.kawak.uk/health

# Nagłówki odpowiedzi
curl -I https://szalasapp.kawak.uk
```

### DNS
```bash
# Sprawdź DNS
nslookup szalasapp.kawak.uk

# Lub dig
dig szalasapp.kawak.uk +short

# Szczegółowe info
dig szalasapp.kawak.uk
```

### Porty
```bash
# Lista otwartych portów
sudo netstat -tulpn

# Sprawdź konkretny port
sudo netstat -tulpn | grep 8080
sudo netstat -tulpn | grep 443
```

### Procesy
```bash
# Wszystkie procesy Dockera
ps aux | grep docker

# Procesy Nginx
ps aux | grep nginx

# Zasoby systemu
htop  # lub top
free -h
df -h
```

### Certyfikat SSL
```bash
# Test certyfikatu
openssl s_client -connect szalasapp.kawak.uk:443 -servername szalasapp.kawak.uk

# Data wygaśnięcia
echo | openssl s_client -connect szalasapp.kawak.uk:443 -servername szalasapp.kawak.uk 2>/dev/null | openssl x509 -noout -dates
```

## 🐛 Troubleshooting

### 502 Bad Gateway
```bash
# Sprawdź czy aplikacja działa
docker compose ps
curl http://localhost:8080/health

# Sprawdź logi aplikacji
docker compose logs --tail=100 app

# Sprawdź logi Nginx
sudo tail -f /var/log/nginx/szalasapp_error.log

# Restart wszystkiego
docker compose restart app
sudo systemctl restart nginx
```

### Aplikacja nie startuje
```bash
# Zobacz logi
docker compose logs app

# Sprawdź czy port jest zajęty
sudo netstat -tulpn | grep 8080

# Sprawdź zmienne środowiskowe
docker compose exec app env | grep GOOGLE

# Restart z pełnym przebudowaniem
docker compose down
docker compose up -d --build
```

### Brak miejsca na dysku
```bash
# Sprawdź użycie
df -h

# Wyczyść Docker
docker system prune -a --volumes

# Wyczyść logi systemowe
sudo journalctl --vacuum-time=7d

# Usuń stare backupy
find /root/backups -mtime +30 -delete
```

## 📊 Monitorowanie

### Logi w czasie rzeczywistym
```bash
# Aplikacja
docker compose logs -f app

# Nginx access
sudo tail -f /var/log/nginx/szalasapp_access.log

# Nginx errors
sudo tail -f /var/log/nginx/szalasapp_error.log

# Systemowe
sudo journalctl -u docker -f
sudo journalctl -u nginx -f
```

### Zasoby
```bash
# Użycie przez kontenery
docker stats

# Użycie dysku
df -h
du -sh ~/SzalasApp/*

# Pamięć
free -h

# CPU i procesy
htop
```

## 🔄 Aktualizacja

### Z Git
```bash
cd ~/SzalasApp

# Pobierz najnowsze zmiany
git pull

# Przebuduj i uruchom ponownie
docker compose up -d --build

# Sprawdź logi
docker compose logs -f
```

### Ręczna (z lokalnej maszyny)
```bash
# Windows PowerShell
.\deploy-from-windows.ps1 -ServerIP YOUR_IP -Domain szalasapp.kawak.uk
```

## 🔥 Firewall (UFW)

### Podstawowe komendy
```bash
# Status
sudo ufw status

# Włącz
sudo ufw enable

# Wyłącz
sudo ufw disable

# Zezwól na port
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp

# Usuń regułę
sudo ufw delete allow 80/tcp

# Reset (usuń wszystkie reguły)
sudo ufw reset
```

## 📝 Zmienne środowiskowe (.env)

### Edycja
```bash
cd ~/SzalasApp
nano .env
# lub
vim .env
```

### Wymagane zmienne
```bash
SECRET_KEY=          # python -c "import secrets; print(secrets.token_hex(32))"
APP_URL=https://szalasapp.kawak.uk
GOOGLE_PROJECT_ID=
GOOGLE_CLOUD_STORAGE_BUCKET_NAME=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
RECAPTCHA_SITE_KEY=
RECAPTCHA_PROJECT_ID=
```

### Restart po zmianie .env
```bash
docker compose down
docker compose up -d
```

## 🔗 Przydatne linki

### Dokumentacja
- Pełny poradnik: `wiki/docs/26_DEPLOYMENT_PRODUCTION.md`
- Szybki start: `DEPLOYMENT_QUICKSTART.md`
- FAQ: `wiki/docs/19_FAQ.md`

### Narzędzia online
- SSL Test: https://www.ssllabs.com/ssltest/
- DNS Check: https://dnschecker.org/
- HTTP Headers: https://securityheaders.com/

## 💡 Najczęściej używane kombinacje

### Pełny restart
```bash
docker compose down && docker compose up -d --build && docker compose logs -f
```

### Szybka diagnostyka
```bash
docker compose ps && curl http://localhost:8080/health && sudo nginx -t
```

### Zobacz wszystko
```bash
docker compose ps && docker stats --no-stream && df -h && free -h
```

---

**Zapisz ten plik w zakładkach! 📌**

