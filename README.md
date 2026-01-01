# SzalasApp - System Zarządzania Sprzętem

System do zarządzania sprzętem szczepu z funkcją zgłaszania usterek i logowania przez OAuth.

## Funkcje

- 📦 Katalog sprzętu z galeriami zdjęć
- 🔧 System zgłaszania i śledzenia usterek
- 🔐 Uwierzytelnianie przez Firebase, Google OAuth i Microsoft OAuth (ZHP)
- 👥 Panel zarządzania użytkownikami dla administratorów
- 🔗 Linkowanie kont OAuth z istniejącymi kontami
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

### Logowanie przez OAuth

Po powiązaniu konta, użytkownicy mogą:
- Logować się bezpośrednio przez Google lub Microsoft na stronie logowania
- Konta Microsoft są ograniczone do domen: `zhp.net.pl` i `zhp.pl`

### Zarządzanie użytkownikami (Admin)

Administratorzy mogą:
- **Włączać/wyłączać** konta użytkowników
- **Resetować hasła** (generowane automatycznie)
- **Przyznawać uprawnienia** administratora
- **Edytować** dane użytkowników

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

## Licencja

[Dodaj informacje o licencji]
