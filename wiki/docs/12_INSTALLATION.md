# Instalacja i Konfiguracja

Szczegółowy przewodnik instalacji SzalasApp.

## 📋 Wymagania

### System
- **OS:** Windows, Linux, macOS
- **Python:** 3.12 lub nowszy
- **RAM:** Min. 2GB
- **Dysk:** Min. 500MB wolnego miejsca

### Konta i Usługi
- Konto Google Cloud (Firebase)
- (Opcjonalnie) Google OAuth credentials
- (Opcjonalnie) Microsoft Azure (dla OAuth)
- (Opcjonalnie) SMTP server dla emaili

---

## 🚀 Instalacja Krok Po Kroku

### 1. Klonowanie Repozytorium

```bash
git clone https://github.com/200wdhigz/SzalasApp.git
cd SzalasApp
```

### 2. Instalacja Zależności

**Opcja A: Poetry (zalecane)**
```bash
# Zainstaluj Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Zainstaluj zależności projektu
poetry install

# Aktywuj virtual environment
poetry shell
```

**Opcja B: pip**
```bash
# Utwórz virtual environment
python -m venv .venv

# Aktywuj (Windows)
.venv\Scripts\activate

# Aktywuj (Linux/Mac)
source .venv/bin/activate

# Zainstaluj zależności
pip install -r requirements.txt
```

### 3. Konfiguracja Firebase

1. **Utwórz projekt Firebase:**
   - https://console.firebase.google.com/
   - Kliknij "Add project"
   - Nazwij projekt (np. "szalas-app")
   - Wyłącz Google Analytics (opcjonalnie)

2. **Włącz Authentication:**
   - Authentication → Sign-in method
   - Włącz "Email/Password"
   - (Opcjonalnie) Włącz "Google" i "Microsoft"

3. **Utwórz Firestore Database:**
   - Firestore Database → Create database
   - Wybierz lokalizację (europe-central2)
   - Start in production mode

4. **Pobierz Service Account:**
   - Project settings → Service accounts
   - Generate new private key
   - Zapisz jako `serviceAccountKey.json` (NIE COMMITUJ!)

5. **Utwórz Cloud Storage Bucket:**
   - Storage → Get started
   - Start in production mode
   - Domyślny bucket utworzony

### 4. Konfiguracja Zmiennych Środowiskowych

```bash
# Skopiuj template
cp .env.example .env

# Edytuj .env
nano .env  # lub vim, code, notepad++
```

**Wypełnij:**
```bash
# Google
GOOGLE_PROJECT_ID=twoj-project-id
GOOGLE_API_KEY=twoj-api-key
SECRET_KEY=wygeneruj-losowy-32-znakowy-klucz

# OAuth (opcjonalnie)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
MICROSOFT_CLIENT_ID=...
MICROSOFT_CLIENT_SECRET=...

# Email (opcjonalnie)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=twoj-email@gmail.com
SMTP_PASSWORD=app-password
```

### 5. Pierwszy Uruchomienie

```bash
# Uruchom aplikację
python app/app.py

# Aplikacja dostępna na:
# http://localhost:5000
```

### 6. Utwórz Pierwszego Admina

```bash
# W osobnym terminalu
python app/scripts/set_admin_claim.py

# Podaj UID użytkownika (z Firebase Console)
```

---

## 🐳 Instalacja Docker

```bash
# Build
docker build -t szalasapp .

# Run
docker run -d \
  --name szalasapp \
  -p 5000:5000 \
  --env-file .env \
  szalasapp

# Sprawdź logi
docker logs szalasapp
```

---

## 🔧 Konfiguracja Produkcyjna

### 1. Gunicorn (zamiast Flask dev server)

```bash
# Zainstaluj
pip install gunicorn

# Uruchom
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 2. Nginx (reverse proxy)

```nginx
server {
    listen 80;
    server_name twoja-domena.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. SSL/HTTPS (Let's Encrypt)

```bash
# Certbot
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d twoja-domena.com
```

---

## 📊 Weryfikacja Instalacji

### Checklist:

- [ ] Aplikacja uruchamia się bez błędów
- [ ] Strona logowania widoczna
- [ ] Firebase połączony (sprawdź logi)
- [ ] Pierwszy admin utworzony
- [ ] OAuth działa (jeśli skonfigurowany)
- [ ] Upload zdjęć działa
- [ ] Eksport działa

---

**Ostatnia aktualizacja:** 2026-01-01  
**Wersja:** 1.0.0

