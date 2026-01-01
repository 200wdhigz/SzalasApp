# Historia Zmian - Changelog

Pełna historia zmian i aktualizacji systemu SzalasApp.

## Wersja 1.1.1 (2026-01-01) 🎉

### 🆕 Nowe Funkcje

#### Samodzielne Zarządzanie Kontem
- ✅ Użytkownicy mogą zmieniać własne hasło bez admina
- ✅ Użytkownicy mogą zmieniać własny email bez admina
- ✅ Weryfikacja aktualnym hasłem dla bezpieczeństwa
- ✅ Formularze w sekcji "Moje Konto"

#### Email Notifications przy Resecie Hasła
- ✅ Automatyczne wysyłanie haseł emailem do użytkowników
- ✅ Professional HTML email template
- ✅ Status wysyłki dla administratora (sukces/błąd)
- ✅ Fallback do ręcznego przekazania jeśli email failed
- ✅ Konfiguracja SMTP (Gmail, Microsoft 365, inne)

#### Inteligentne Komunikaty Błędów
- ✅ Wykrywanie kont z OAuth przy próbie logowania hasłem
- ✅ Pomocne komunikaty: "To konto ma powiązane logowanie przez [Google/Microsoft]"
- ✅ Jasne wskazówki dla użytkowników

#### Synchronizacja Użytkowników
- ✅ Przycisk "Synchronizuj" w panelu zarządzania użytkownikami
- ✅ Automatyczna synchronizacja Firebase Auth ↔ Firestore
- ✅ Raport: "usunięto X, dodano Y użytkowników"
- ✅ Usuwanie "martwych" wpisów

#### Usuwanie Użytkowników z Aplikacji
- ✅ Przycisk 🗑️ dla każdego użytkownika
- ✅ Usuwanie z Firebase Auth i Firestore jednocześnie
- ✅ Potwierdzenie z wyświetleniem emaila użytkownika
- ✅ Nie wymaga synchronizacji później

### 📝 Zmiany

#### Backend
- `src/auth.py` - Enhanced login error handling z OAuth detection
- `src/oauth.py` - Dodano `change_password()` i `change_email()` routes
- `src/db_users.py` - Dodano `update_user_email()`, `delete_user()`, `sync_users_from_firebase_auth()`
- `src/admin.py` - Dodano `send_password_reset_email()`, routes `/users/sync` i `/users/<id>/delete`

#### Frontend
- `templates/account.html` - Dodano formularze zmiany hasła i emaila
- `templates/admin/users_list.html` - Dodano przycisk synchronizacji i usuwania, status emaila

#### Dokumentacja
- ✅ `CHANGELOG_ACCOUNT_FEATURES.md` - Szczegóły nowych funkcji kont
- ✅ `USER_SYNC_GUIDE.md` - Przewodnik synchronizacji
- ✅ `CHANGELOG_USER_SYNC.md` - Dokumentacja sync/delete
- ✅ `QUICK_START.md` - Szybki start dla użytkowników
- ✅ `.env.example` - Dodano konfigurację SMTP
- ✅ `README.md` - Zaktualizowano o nowe funkcje

### 🔒 Bezpieczeństwo

- ✅ CSRF protection na wszystkich nowych formularzach
- ✅ Weryfikacja hasła przy zmianie emaila/hasła
- ✅ STARTTLS dla połączeń SMTP
- ✅ Session-based password display (one-time view)
- ✅ Potwierdzenie przed usunięciem użytkownika

### 🐛 Poprawki

- ✅ Naprawiono problem z nieaktualizowaniem listy użytkowników po usunięciu w Console
- ✅ Poprawiono komunikaty błędów logowania
- ✅ Ulepszono feedback dla użytkownika

---

## Wersja 1.1.0 (2025-12-28)

### 🆕 Nowe Funkcje

#### Usprawniona Karta Usterki
- ✅ Layout podobny do karty sprzętu
- ✅ Dwukolumnowy widok (galeria + szczegóły)
- ✅ Lepsze wyświetlanie informacji
- ✅ Link do karty sprzętu

#### Oddzielny Widok Edycji Usterki
- ✅ Route `/usterka/edit/<id>` zamiast POST na `/usterka/<id>`
- ✅ Konsystentny z edycją sprzętu
- ✅ Przekierowanie do karty po edycji (nie do listy)

### 📝 Zmiany

- `src/views.py` - Rozdzielono `usterka_card` (view) i `usterka_edit` (edit)
- `templates/usterka_card.html` - Przeprojektowano layout
- Poprawiono redirect flow

---

## Wersja 1.0.0 (2025-12-15) 🎉

### 🆕 Pierwsze Wydanie

#### Podstawowe Funkcje
- ✅ System zarządzania sprzętem
- ✅ Katalog z galeriami zdjęć
- ✅ System zgłaszania usterek
- ✅ Filtrowanie i wyszukiwanie

#### Uwierzytelnianie
- ✅ Firebase Authentication
- ✅ Google OAuth
- ✅ Microsoft OAuth (tylko domeny ZHP)
- ✅ Linkowanie kont OAuth

#### Panel Administratora
- ✅ Zarządzanie użytkownikami
- ✅ Rejestracja nowych użytkowników
- ✅ Włączanie/wyłączanie kont
- ✅ Reset haseł
- ✅ Edycja ról

#### Zarządzanie Sprzętem
- ✅ Dodawanie ręczne
- ✅ Import CSV/XLSX
- ✅ Edycja wszystkich pól
- ✅ Upload zdjęć (max 5, każde ≤5MB)
- ✅ Kody QR dla sprzętu

#### System Usterek
- ✅ Publiczne zgłaszanie (z reCAPTCHA)
- ✅ Przypisanie do sprzętu
- ✅ Statusy (oczekuje/w trakcie/naprawiona/odrzucona)
- ✅ Uwagi administratora
- ✅ Galerie zdjęć usterek

#### Eksport Danych
- ✅ CSV
- ✅ XLSX (Excel)
- ✅ DOCX (Word)
- ✅ PDF

#### Bezpieczeństwo
- ✅ CSRF protection
- ✅ reCAPTCHA Enterprise
- ✅ Role-based access control
- ✅ OAuth state parameter

#### Dokumentacja
- ✅ README.md - Przegląd projektu
- ✅ ARCHITECTURE.md - Architektura systemu
- ✅ OAUTH_SETUP.md - Konfiguracja OAuth
- ✅ FEATURE_SUMMARY.md - Podsumowanie funkcji

---

## Planowane (Roadmap)

### Wersja 1.2.0 (Q1 2026)

#### Email Notifications
- 📧 Powiadomienia o nowych usterkach dla adminów
- 📧 Powiadomienia o zmianie statusu dla zgłaszających
- 📧 Przypomnienia o nierozwiązanych usterkach

#### Rozszerzone Filtry
- 🔍 Zaawansowane wyszukiwanie sprzętu
- 🔍 Filtr usterek po dacie
- 🔍 Eksport tylko filtrowanych danych

#### Ulepszenia UI
- 🎨 Ciemny motyw
- 🎨 Personalizacja kolorów
- 🎨 Dostępność (a11y improvements)

### Wersja 1.3.0 (Q2 2026)

#### System Wypożyczeń
- 📋 Rejestracja wypożyczeń sprzętu
- 📋 Historia wypożyczeń
- 📋 Przypomnienia o zwrocie
- 📋 Raportowanie (kto, co, kiedy)

#### Dashboard Analytics
- 📊 Statystyki sprzętu
- 📊 Statystyki usterek
- 📊 Wykresy i raporty
- 📊 Trendy i predykcje

### Wersja 2.0.0 (Q3 2026)

#### API RESTful
- 🔌 Publiczne API dla integracji
- 🔌 Dokumentacja OpenAPI/Swagger
- 🔌 Rate limiting
- 🔌 API keys

#### Aplikacja Mobilna
- 📱 React Native app
- 📱 Skanowanie QR
- 📱 Offline mode
- 📱 Push notifications

---

## Notatki Wydania

### Migracja z 1.0.0 → 1.1.1

**Wymagane kroki:**

1. **Aktualizacja .env**
   ```bash
   # Dodaj konfigurację SMTP (opcjonalnie)
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   FROM_EMAIL=noreply@yourapp.com
   ```

2. **Brak zmian w bazie danych** - Automatyczne

3. **Testowanie:**
   - Zmiana hasła przez użytkownika
   - Zmiana emaila przez użytkownika
   - Reset hasła przez admina (sprawdź email)
   - Synchronizacja użytkowników
   - Usuwanie użytkownika z aplikacji

4. **Informowanie użytkowników:**
   - Nowe możliwości zarządzania kontem
   - Instrukcja zmiany hasła/emaila
   - Kontakt z supportem przy problemach

### Breaking Changes

**1.1.1:**
- Brak breaking changes
- 100% backward compatible

**1.1.0:**
- Zmienione routy usterek (`/usterka/<id>` teraz tylko GET)
- Dodano `/usterka/edit/<id>` dla edycji
- Wpływa tylko na admins

---

## Znane Problemy

### Wersja 1.1.1

**Email Delivery:**
- SMTP Gmail może wymagać App Password
- Microsoft 365 może mieć ograniczenia per dzień
- Niektóre serwery SMTP mogą blokować Port 587

**Workaround:** Hasło zawsze wyświetlane administratorowi w przeglądarce

### Wersja 1.0.0

**Performance:**
- Duża liczba zdjęć (>100) może spowolnić loading
- Eksport dużych dataset (>1000) może zająć czas

**Workaround:** Paginacja planowana w 1.2.0

---

## Kontrybutorzy

Dziękujemy wszystkim, którzy przyczynili się do rozwoju SzalasApp!

- @admin - Core development
- @testers - Testing and feedback
- Community - Bug reports and suggestions

---

## Licencja

Ten projekt jest dostępny na licencji określonej w pliku LICENSE.

---

**Ostatnia aktualizacja:** 2026-01-01  
**Wersja dokumentu:** 1.1.0  
**Następna planowana wersja:** 1.2.0 (Q1 2026)

