# SzalasApp - System Zarządzania Sprzętem

System do zarządzania sprzętem szczepu z funkcją zgłaszania usterek i logowania przez OAuth.

## Struktura Projektu

```
SzalasApp/
├── app/                    # Aplikacja Python
│   ├── src/               # Kod źródłowy
│   ├── templates/         # Szablony Jinja2
│   ├── static/           # Pliki statyczne (CSS, JS, images)
│   ├── scripts/          # Skrypty utility
│   ├── app.py            # Entry point
│   ├── pyproject.toml    # Poetry dependencies
│   ├── poetry.lock       # Locked versions
│   └── requirements.txt  # Eksport dla pip
│
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose setup
├── .env.example          # Template zmiennych środowiskowych
├── .gitignore            # Git ignore rules
│
├── Makefile             # Convenience commands
├── setup.ps1            # Setup script (Windows)
├── setup.sh             # Setup script (Linux/macOS)
│
├── credentials/         # Service account JSON (NIE commitować!)
│   └── service-account.json
│
├── wiki/               # Dokumentacja i Wiki
│   ├── docs/          # Pliki źródłowe dokumentacji
│   ├── export/        # Wygenerowane pliki wiki (generowane)
│   ├── prepare_wiki.py # Skrypt generujący wiki
│   └── GITHUB_WIKI_GUIDE.md
│   ├── auth.py             # Uwierzytelnianie (Firebase, OAuth)
│   ├── oauth.py            # OAuth (Google, Microsoft)
│   ├── admin.py            # Panel administratora
│   ├── views.py            # Widoki główne (sprzęt, usterki)
│   ├── db_firestore.py     # Operacje Firestore (sprzęt, usterki)
│   ├── db_users.py         # Operacje Firestore (użytkownicy)
│   ├── gcs_utils.py        # Google Cloud Storage
│   ├── exports.py          # Eksport danych (CSV, XLSX, DOCX, PDF)
│   └── recaptcha.py        # reCAPTCHA Enterprise
│
├── templates/              # Szablony Jinja2
│   ├── base.html
│   ├── login.html
│   ├── account.html
│   ├── sprzet_list.html
│   ├── sprzet_card.html
│   ├── sprzet_edit.html
│   ├── sprzet_import.html
│   ├── usterki_list.html
│   ├── usterka_card.html
│   ├── usterka_edit.html
│   └── admin/              # Szablony administratora
│       ├── users_list.html
│       ├── user_new.html
│       └── user_edit.html
│
├── static/                 # Pliki statyczne
│   └── assets/
│       ├── css/
│       ├── js/
│       └── img/
│
├── scripts/                # Skrypty pomocnicze
│   ├── README.md           # Dokumentacja skryptów
│   ├── import_data.py      # Import danych sprzętu
│   ├── set_admin_claim.py  # Nadawanie uprawnień admina
│   └── upload_photos.py    # Upload zdjęć do GCS
│
└── docs/                   # Dokumentacja projektu
    ├── README.md           # Index dokumentacji
    ├── 00_INDEX.md         # Kompletny przewodnik
    ├── 01_QUICK_START.md   # Szybki start
    ├── 02_ARCHITECTURE.md  # Architektura systemu
    ├── 03_OAUTH_SETUP.md   # Konfiguracja OAuth
    ├── 04-23_*.md          # Pozostała dokumentacja numerowana
    ├── 24_DEPENDENCIES.md  # Zarządzanie zależnościami
    ├── 25_FEATURE_SUMMARY.md # Podsumowanie funkcji
    └── ... inne pliki
```

---

## Dokumentacja

### 📚 Pełna Dokumentacja

Kompletna dokumentacja projektu znajduje się w folderze `docs/`:

**START TUTAJ:** [docs/README.md](docs/README.md) lub [docs/00_INDEX.md](docs/00_INDEX.md)

**GitHub Wiki:** [https://github.com/200wdhigz/SzalasApp/wiki](https://github.com/200wdhigz/SzalasApp/wiki)
- Dokumentacja jest automatycznie synchronizowana z `docs/`
- Zobacz [GITHUB_WIKI_GUIDE.md](GITHUB_WIKI_GUIDE.md) dla szczegółów

### 🚀 Szybkie Linki

**Dla Użytkowników:**
- [Szybki Start](docs/01_QUICK_START.md) - Pierwsze kroki
- [Zarządzanie Kontem](docs/04_ACCOUNT_MANAGEMENT.md) - Twoje konto
- [FAQ](docs/19_FAQ.md) - Odpowiedzi na pytania

**Dla Administratorów:**
- [OAuth Setup](docs/03_OAUTH_SETUP.md) - Konfiguracja Google/Microsoft
- [Synchronizacja Użytkowników](docs/05_USER_SYNC.md) - Sync z Firebase
- [Panel Administratora](docs/09_ADMIN_PANEL.md) - Wszystkie funkcje

**Wdrożenie Produkcyjne:** 🚀
- [**Wdrożenie z Docker i HTTPS**](wiki/docs/26_DEPLOYMENT_PRODUCTION.md) - Kompletny poradnik produkcyjny
- [**Szybki Start Wdrożenia**](DEPLOYMENT_QUICKSTART.md) - Skrócona instrukcja
- [Skrypt automatycznego setupu](deploy-setup.sh) - Dla serwerów Linux
- [Skrypt wdrożenia z Windows](deploy-from-windows.ps1) - Dla Windows PowerShell

**Funkcje Systemu:**
- [Zarządzanie Sprzętem](docs/06_EQUIPMENT_MANAGEMENT.md) - Kompletny przewodnik
- [System Usterek](docs/07_MALFUNCTION_SYSTEM.md) - Zgłaszanie i śledzenie
- [Historia Zmian](docs/18_CHANGELOG.md) - Changelog

**Dla Deweloperów:**
- [Architektura](docs/02_ARCHITECTURE.md) - Struktura systemu
- [Feature Summary](docs/25_FEATURE_SUMMARY.md) - Podsumowanie funkcji
- [Dependencies](docs/24_DEPENDENCIES.md) - Zarządzanie zależnościami

---

## Skrypty Pomocnicze

Folder `scripts/` zawiera narzędzia pomocnicze:

- **`import_data.py`** - Import sprzętu z CSV/XLSX do Firestore
- **`set_admin_claim.py`** - Nadawanie uprawnień administratora
- **`upload_photos.py`** - Upload zdjęć do Google Cloud Storage

**Dokumentacja:** [scripts/README.md](scripts/README.md)

**Użycie:**
```bash
python scripts/nazwa_skryptu.py
```

---

## Instalacja
- [Synchronizacja Użytkowników](docs/05_USER_SYNC.md) - Sync z Firebase
- [Panel Administratora](docs/09_ADMIN_PANEL.md) - Wszystkie funkcje

**Funkcje Systemu:**
- [Zarządzanie Sprzętem](docs/06_EQUIPMENT_MANAGEMENT.md) - Kompletny przewodnik
- [System Usterek](docs/07_MALFUNCTION_SYSTEM.md) - Zgłaszanie i śledzenie
- [Historia Zmian](docs/18_CHANGELOG.md) - Changelog

**Dla Deweloperów:**
- [Architektura](docs/02_ARCHITECTURE.md) - Struktura systemu
- [FEATURE_SUMMARY.md](FEATURE_SUMMARY.md) - Podsumowanie funkcji

---

## Funkcje

- 📦 Katalog sprzętu z galeriami zdjęć
- 🔧 System zgłaszania i śledzenia usterek
- 🔐 Uwierzytelnianie przez Firebase, Google OAuth i Microsoft OAuth (ZHP)
- 👥 Panel zarządzania użytkownikami dla administratorów
- 🔗 Linkowanie kont OAuth z istniejącymi kontami
- 🔑 **NOWE:** Samodzielna zmiana hasła i emaila przez użytkowników
- 📧 **NOWE:** Automatyczne wysyłanie haseł emailem przy resecie (przez admina)
- 💡 **NOWE:** Inteligentne komunikaty błędów przy logowaniu
- 📊 Eksport danych do CSV, XLSX, DOCX i PDF

## Konfiguracja OAuth

### 1. Google OAuth

1. Przejdź do [Google Cloud Console](https://console.cloud.google.com/)
2. Utwórz nowy projekt lub wybierz istniejący
3. Włącz **Google+ API** dla projektu
4. Przejdź do **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Wybierz typ aplikacji: **Web application**
6. Dodaj **Authorized redirect URIs**:
   - `http://localhost:5000/auth/google/callback` (dla rozwoju)
   - `https://yourdomain.com/auth/google/callback` (dla produkcji)
7. Skopiuj **Client ID** i **Client Secret** do `.env`:
   ```
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```

### 2. Microsoft OAuth (dla kont ZHP)

1. Przejdź do [Azure Portal](https://portal.azure.com/)
2. Wybierz **Azure Active Directory** → **App registrations** → **New registration**
3. Nazwij aplikację (np. "SzalasApp")
4. Wybierz **Supported account types**: 
   - "Accounts in any organizational directory" dla ogólnego dostępu
   - Lub konkretny tenant dla domeny ZHP
5. Dodaj **Redirect URI**:
   - Platforma: **Web**
   - URI: `http://localhost:5000/auth/microsoft/callback` (rozwój)
   - URI: `https://yourdomain.com/auth/microsoft/callback` (produkcja)
6. Po utworzeniu, przejdź do **Certificates & secrets** → **New client secret**
7. Skopiuj wartości do `.env`:
   ```
   MICROSOFT_CLIENT_ID=your-application-id
   MICROSOFT_CLIENT_SECRET=your-client-secret
   MICROSOFT_TENANT_ID=common
   ```
8. Przejdź do **API permissions** → **Add a permission** → **Microsoft Graph**:
   - Dodaj delegated permissions: `User.Read`, `email`, `openid`, `profile`

### 3. Konfiguracja środowiska

1. Skopiuj `.env.example` do `.env`:
   ```bash
   cp .env.example .env
   ```

2. Uzupełnij wszystkie wymagane zmienne środowiskowe

3. Ustaw `BASE_URL` na właściwą wartość dla Twojego środowiska

### 4. Konfiguracja Email (opcjonalna, dla powiadomień o resecie hasła)

Jeśli chcesz, aby system automatycznie wysyłał emaile z nowymi hasłami:

#### Opcja 1: Gmail

1. Włącz uwierzytelnianie dwuskładnikowe na koncie Gmail
2. Wygeneruj hasło aplikacji:
   - Przejdź do: https://myaccount.google.com/apppasswords
   - Wybierz "Poczta" i swoje urządzenie
   - Skopiuj wygenerowane hasło (16 znaków)
3. Uzupełnij w `.env`:
   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=twoj-email@gmail.com
   SMTP_PASSWORD=wygenerowane-haslo-aplikacji
   FROM_EMAIL=twoj-email@gmail.com
   ```

#### Opcja 2: Microsoft 365

```
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=twoj-email@twojadomena.com
SMTP_PASSWORD=twoje-haslo
FROM_EMAIL=twoj-email@twojadomena.com
```

#### Opcja 3: Inny dostawca SMTP

Skonsultuj dokumentację swojego dostawcy email i uzupełnij:
```
SMTP_HOST=mail.twojadomena.com
SMTP_PORT=587  # lub 465 dla SSL
SMTP_USER=twoj-email@twojadomena.com
SMTP_PASSWORD=twoje-haslo
FROM_EMAIL=noreply@twojadomena.com
```

**Uwaga:** Jeśli SMTP nie jest skonfigurowany, reset hasła przez admina nadal będzie działał - hasło zostanie wyświetlone administratorowi w przeglądarce do ręcznego przekazania użytkownikowi.

## Instalacja

### Przy użyciu Poetry

```bash
poetry install
poetry run python app.py
```

### Przy użyciu pip

```bash
pip install -r requirements.txt
python app.py
```

## Zarządzanie użytkownikami

### Role użytkowników

- **Administrator**: Pełne uprawnienia, zarządzanie użytkownikami, edycja sprzętu
- **Użytkownik**: Przeglądanie sprzętu, zgłaszanie usterek

### Rejestracja nowych użytkowników

Tylko administratorzy mogą rejestrować nowych użytkowników:

1. Zaloguj się jako administrator
2. Przejdź do **Zarządzanie Użytkownikami** w menu
3. Kliknij **Nowy Użytkownik**
4. Wypełnij formularz i wybierz rolę
5. Nowy użytkownik otrzyma dane logowania

### Linkowanie kont OAuth

Użytkownicy mogą powiązać swoje konto z dostawcami OAuth:

1. Zaloguj się do systemu
2. Przejdź do **Moje Konto**
3. Kliknij **Połącz** przy wybranym dostawcy (Google/Microsoft)
4. Autoryzuj aplikację u dostawcy
5. Konto zostanie powiązane

### Samodzielne zarządzanie kontem (NOWE)

Każdy użytkownik może samodzielnie zarządzać swoim kontem bez pomocy administratora:

#### Zmiana hasła

1. Przejdź do **Moje Konto**
2. Znajdź sekcję **Zmiana hasła**
3. Wprowadź aktualne hasło
4. Wprowadź nowe hasło (min. 6 znaków)
5. Potwierdź nowe hasło
6. Kliknij **Zmień hasło**

**Uwaga:** Użytkownicy z połączonymi kontami OAuth (Google/Microsoft) również mogą ustawić hasło, aby móc logować się zarówno przez OAuth, jak i hasłem.

#### Zmiana adresu email

1. Przejdź do **Moje Konto**
2. Znajdź sekcję **Zmiana adresu email**
3. Wprowadź nowy adres email
4. Potwierdź zmianę swoim aktualnym hasłem
5. Kliknij **Zmień email**

**Bezpieczeństwo:** Wszystkie zmiany wymagają potwierdzenia aktualnym hasłem użytkownika.

### Logowanie przez OAuth

Po powiązaniu konta, użytkownicy mogą:
- Logować się bezpośrednio przez Google lub Microsoft na stronie logowania
- Konta Microsoft są ograniczone do domen: `zhp.net.pl` i `zhp.pl`

#### Inteligentne komunikaty błędów (NOWE)

System automatycznie wykrywa sytuacje, gdy użytkownik próbuje zalogować się hasłem, ale ma powiązane konto OAuth:

**Przykład:**
- Użytkownik ma połączone konto Google
- Próbuje zalogować się emailem i hasłem
- System pokazuje: *"To konto ma powiązane logowanie przez Google. Użyj odpowiedniego przycisku poniżej aby się zalogować."*

**Korzyści:**
- Zmniejszenie frustracji użytkowników
- Jasne wskazówki dotyczące prawidłowej metody logowania
- Mniej zgłoszeń do wsparcia technicznego

### Zarządzanie użytkownikami (Admin)

Administratorzy mogą:
- **Włączać/wyłączać** konta użytkowników
- **Resetować hasła** (generowane automatycznie i wysyłane emailem)
- **Przyznawać uprawnienia** administratora
- **Edytować** dane użytkowników
- **Usuwać użytkowników** całkowicie (z Firebase Auth i Firestore)
- **Synchronizować listę** z Firebase Auth

#### Synchronizacja użytkowników (NOWE)

Jeśli usuniesz użytkownika bezpośrednio w [Firebase Console](https://console.firebase.google.com/), lista w aplikacji nie zaktualizuje się automatycznie. Użyj przycisku **"Synchronizuj"** w panelu zarządzania użytkownikami, aby:

- Usunąć z Firestore użytkowników, którzy nie istnieją już w Firebase Auth
- Dodać do Firestore użytkowników, którzy istnieją w Firebase Auth, ale nie w Firestore

**Alternatywnie:** Możesz usuwać użytkowników bezpośrednio z panelu aplikacji za pomocą przycisku <i class="bi bi-trash"></i> (kosz). To usunie użytkownika zarówno z Firebase Auth, jak i Firestore jednocześnie.

#### Reset hasła przez administratora (NOWE - z powiadomieniem email)

Kiedy administrator resetuje hasło użytkownika:
1. System generuje silne, losowe hasło (16 znaków)
2. Hasło jest automatycznie wysyłane na email użytkownika (jeśli SMTP jest skonfigurowany)
3. Hasło jest wyświetlane administratorowi z informacją o statusie wysyłki:
   - ✅ **Zielony**: Email wysłany pomyślnie
   - ⚠️ **Żółty**: Email nie został wysłany, wymagana ręczna komunikacja
4. Administrator może skopiować hasło, jeśli email się nie powiódł

**Format emaila:**
- Profesjonalny szablon HTML
- Wyraźnie wyświetlone hasło
- Link do logowania
- Zalecenie zmiany hasła po pierwszym logowaniu

## Struktura projektu

```
SzalasApp/
├── src/
│   ├── __init__.py          # Inicjalizacja aplikacji Flask
│   ├── auth.py              # Uwierzytelnianie Firebase
│   ├── oauth.py             # OAuth flows i account management
│   ├── admin.py             # Panel administracyjny
│   ├── views.py             # Główne widoki aplikacji
│   ├── db_firestore.py      # Operacje na bazie danych
│   ├── db_users.py          # Zarządzanie użytkownikami
│   └── ...
├── templates/
│   ├── base.html
│   ├── login.html           # Strona logowania z OAuth
│   ├── account.html         # Panel użytkownika
│   ├── admin/
│   │   ├── users_list.html  # Lista użytkowników
│   │   ├── user_new.html    # Rejestracja nowego użytkownika
│   │   └── user_edit.html   # Edycja użytkownika
│   └── ...
├── .env.example             # Przykładowa konfiguracja
├── requirements.txt
└── app.py
```

## Bezpieczeństwo

- OAuth flows używają state parameter do ochrony przed CSRF
- Tokeny OAuth są bezpiecznie przechowywane
- Hasła są zarządzane przez Firebase Authentication
- Konta Microsoft są ograniczone do domen ZHP
- Wyłączone konta nie mogą się logować
- **Samodzielne zmiany hasła/emaila wymagają weryfikacji aktualnym hasłem**
- **CSRF protection na wszystkich formularzach**
- **Email z hasłem wysyłany tylko na zarejestrowany adres użytkownika**
- **Hasła resetowane przez admina są wyświetlane jednorazowo**

## Licencja

[Dodaj informacje o licencji]
