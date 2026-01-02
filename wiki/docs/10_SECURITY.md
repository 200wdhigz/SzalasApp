# Bezpieczeństwo
**Wersja:** 1.0.0
**Ostatnia aktualizacja:** 2026-01-01  

---

- [ ] Audyt użytkowników (co kwartał)
- [ ] Testuj restore (co miesiąc)
- [ ] Backup danych (codziennie auto)
- [ ] Sprawdzaj logi (co tydzień)
- [ ] Aktualizuj dependencies (co miesiąc)
### Regularnie:

- [ ] SMTP z TLS
- [ ] reCAPTCHA włączony
- [ ] Firebase rules skonfigurowane
- [ ] HTTPS włączony (produkcja)
- [ ] .env skonfigurowany (nie commitowany)
### Setup:

## 📋 Checklist Bezpieczeństwa

---

   - Jak zapobiec w przyszłości
   - Jak naprawiono
   - Co się stało
4. **Dokumentuj:**

   - Użytkowników (jeśli dotyczy)
   - Innych adminów
3. **Powiadom:**

   - GitHub Actions logs
   - Firestore audit trail
   - Logi dostępu
2. **Sprawdź:**

   - Firebase API keys
   - Credentials OAuth
   - Hasła adminów
1. **Zmień natychmiast:**

### Co robić?

## 🚨 Incydenty Bezpieczeństwa

---

- Lockfile commitowany (poetry.lock)
- Sprawdzaj CVE (pip-audit)
- Aktualizuj regularnie
✅ **Dependencies**

- Code review dla zmian w auth
- Używaj secrets w CI/CD
- Nigdy nie commituj .env
✅ **Kod**

### Dla Deweloperów:

- Zgłoś podejrzaną aktywność
- Nie udostępniaj swojego konta
- Wyloguj się po skończonej pracy
✅ **Sesje**

- Zmień jeśli podejrzewasz kompromis
- Używaj managera haseł
- Unikalne dla tej aplikacji
✅ **Hasła**

### Dla Użytkowników:

- Test restore co miesiąc
- Szyfrowane przechowywanie
- Regularne backupy Firestore
✅ **Backup**

- Aktualizuj hasła co 90 dni
- Dezaktywuj nieużywane konta
- Sprawdzaj logi co tydzień
✅ **Regularne audyty**

- Używaj app passwords dla SMTP
- Włącz uwierzytelnianie dwuskładnikowe
✅ **2FA dla Google/Microsoft**

- Cyfry i znaki specjalne
- Wielkie i małe litery
- Min. 12 znaków
✅ **Silne hasła**

### Dla Administratorów:

## 🛡️ Best Practices

---

- Nie przechowywane w kodzie
- Credentials w .env
- STARTTLS/TLS encryption
**SMTP/Email:**

- Automatyczne przekierowanie HTTP → HTTPS
- Certyfikat SSL/TLS
- Wymagane w produkcji
**HTTPS:**

### 6. Komunikacja

- Logowanie podejrzanych prób
- Score-based decision (0.0-1.0)
- reCAPTCHA v3 (invisible)
**Implementacja:**

- Brute force attacks
- Spamem usterek
- Botami
**Ochrona przed:**

### 5. reCAPTCHA Enterprise

```
// Tylko admini mogą pisać
// Tylko zalogowani mogą czytać
```javascript
**Firestore Rules:**

- Email SMTP: W zmiennych środowiskowych (.env)
- Tokeny OAuth: Encrypted w sesji
- Hasła: Nigdy nie przechowywane w plain text
**Dane wrażliwe:**

### 4. Ochrona Danych

- Timeout tokenu
- Weryfikacja przy każdym POST request
- Token generowany dla każdej sesji
**Walidacja po stronie serwera:**

```
<input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">
```html
**Wszystkie formularze chronione:**

### 3. CSRF Protection

```
@admin_required  # Wymaga roli admin
@login_required  # Wymaga zalogowania
```python
**Dekoratory:**

- Użytkownik - ograniczone uprawnienia
- Administrator - pełne uprawnienia
**Role-Based Access Control (RBAC):**

### 2. Autoryzacja

- Automatyczne odświeżanie tokenów
- Tokeny przechowywane bezpiecznie w sesji
- Autoryzacja przez zaufane dostawców (Google, Microsoft)
- State parameter (CSRF protection)
**OAuth 2.0:**

- Rate limiting dla prób logowania
- Automatyczne wygasanie sesji
- Tokeny sesji JWT
- Hasła hashowane przez Firebase (bcrypt + salt)
**Firebase Authentication:**

### 1. Uwierzytelnianie

## 🔒 Obszary Bezpieczeństwa

Przewodnik po zabezpieczeniach w SzalasApp.


