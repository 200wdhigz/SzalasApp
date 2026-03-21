# Rozwiązywanie Problemów

Przewodnik po typowych problemach i ich rozwiązaniach.

## 🔥 Problemy z Logowaniem

### Nie mogę się zalogować hasłem (mam OAuth)

**Objaw:** Komunikat "To konto ma powiązane logowanie przez Google/Microsoft"

**Rozwiązanie:**
1. Użyj przycisku OAuth na stronie logowania
2. LUB ustaw hasło w "Moje Konto" → "Zmiana hasła"

### Zapomniałem hasła

**Rozwiązanie:**
1. Skontaktuj się z administratorem
2. Admin zresetuje hasło przez panel zarządzania
3. Otrzymasz nowe hasło emailem (jeśli SMTP skonfigurowany)

### OAuth nie działa

**Sprawdź:**
- [ ] Credentials w .env są poprawne
- [ ] Redirect URI w Google/Azure zgadza się z BASE_URL
- [ ] Domena Microsoft jest w MICROSOFT_ALLOWED_DOMAINS

---

## 📦 Problemy ze Sprzętem

### Nie mogę dodać zdjęć

**Przyczyny:**
- Plik za duży (>5MB)
- Zły format (tylko obrazy)
- Brak uprawnień do Cloud Storage

**Rozwiązanie:**
1. Zmniejsz rozmiar zdjęcia
2. Konwertuj do JPG/PNG
3. Sprawdź uprawnienia Firebase Storage

### Import CSV nie działa

**Przyczyny:**
- Błędne kodowanie (nie UTF-8)
- Brak wymaganych kolumn (id, typ, lokalizacja)
- Niepoprawny format dat

**Rozwiązanie:**
1. Zapisz CSV z UTF-8 encoding
2. Sprawdź nagłówki kolumn
3. Format dat: YYYY-MM-DD

---

## 🔧 Problemy z Usterkami

### reCAPTCHA nie ładuje się

**Przyczyny:**
- Brak RECAPTCHA_SITE_KEY w .env
- Błędne Project ID
- Blokada przez AdBlock

**Rozwiązanie:**
1. Sprawdź .env
2. Wyłącz AdBlock na tej stronie
3. Sprawdź console przeglądarki (F12)

---

## 👥 Problemy z Użytkownikami

### Użytkownik widoczny po usunięciu w Firebase Console

**Rozwiązanie:**
1. Panel zarządzania użytkownikami
2. Kliknij "Synchronizuj"
3. Lista się zaktualizuje

### Email z hasłem nie przychodzi

**Sprawdź:**
- [ ] SMTP skonfigurowany w .env
- [ ] Folder SPAM
- [ ] Email użytkownika poprawny
- [ ] Logi aplikacji

**Rozwiązanie:**
- Admin widzi hasło w przeglądarce
- Przekaż ręcznie użytkownikowi

---

## 🐛 Błędy Aplikacji

### 500 Internal Server Error

**Sprawdź:**
1. Logi aplikacji (terminal)
2. Firebase credentials
3. Połączenie z Firestore

**Typowe przyczyny:**
- Błędny serviceAccountKey.json
- Brak połączenia z internetem
- Niepoprawne Firebase rules

### 403 Forbidden

**Przyczyna:** Brak uprawnień

**Rozwiązanie:**
1. Sprawdź czy jesteś zalogowany
2. Sprawdź czy masz rolę admin (dla funkcji admin)

### Aplikacja nie startuje

**Sprawdź:**
```bash
# Sprawdź logi
python app/app.py

# Najczęstsze błędy:
# - Brak zależności → pip install -r requirements.txt
# - Brak .env → cp .env.example .env
# - Port zajęty → zmień PORT w .env
```

---

## 📧 Problemy z Email

### SMTP authentication failed

**Przyczyny:**
- Błędne hasło
- Brak 2FA/App Password (Gmail)
- Zła konfiguracja SMTP_HOST/PORT

**Rozwiązanie Gmail:**
1. Włącz 2FA
2. Wygeneruj App Password
3. Użyj App Password w .env

---

## 🔍 Debug Mode

### Włącz szczegółowe logi

```python
# W app.py
app.config['DEBUG'] = True  # Tylko development!
```

### Sprawdź logi Firebase

```bash
# W terminalu gdzie uruchomiona aplikacja
# Logi pokażą błędy Firebase/Firestore
```

### Console przeglądarki

```
F12 → Console
# Sprawdź błędy JavaScript
```

---

## 📞 Gdzie Szukać Pomocy

1. **FAQ** - [19_FAQ.md](19_FAQ.md)
2. **Dokumentacja** - [README.md](README.md)
3. **GitHub Issues** - Zgłoś problem
4. **Logi** - Zawsze sprawdzaj logi jako pierwsze

---

**Ostatnia aktualizacja:** 2026-01-01  
**Wersja:** 1.0.0
