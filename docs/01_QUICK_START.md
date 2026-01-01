# Quick Start Guide - Nowe Funkcje

## 🚀 Szybki Start

### 1. Konfiguracja Email (Opcjonalna, ale zalecana)

Aby włączyć automatyczne wysyłanie haseł emailem przy resecie:

#### Dla Gmail (Najłatwiejsza opcja)

1. **Włącz uwierzytelnianie 2FA** w swoim koncie Gmail
2. **Wygeneruj hasło aplikacji**:
   - Przejdź do: https://myaccount.google.com/apppasswords
   - Wybierz "Poczta" i swoje urządzenie
   - Skopiuj 16-znakowe hasło

3. **Dodaj do pliku `.env`**:
   ```bash
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=twoj-email@gmail.com
   SMTP_PASSWORD=aaaa-bbbb-cccc-dddd  # Hasło aplikacji (16 znaków)
   FROM_EMAIL=twoj-email@gmail.com
   ```

#### Inne opcje SMTP

Sprawdź w `.env.example` dla Microsoft 365 i innych dostawców.

**Ważne:** Jeśli nie skonfigurujesz SMTP, wszystko będzie działać - hasło pojawi się administratorowi w przeglądarce do ręcznego przekazania użytkownikowi.

---

## 🔑 Nowe Funkcje dla Użytkowników

### Zmiana Hasła (bez pomocy admina!)

1. Zaloguj się do systemu
2. Kliknij **"Moje Konto"** w menu
3. Przewiń do sekcji **"Zmiana hasła"**
4. Wypełnij formularz:
   - Aktualne hasło
   - Nowe hasło (min. 6 znaków)
   - Potwierdź nowe hasło
5. Kliknij **"Zmień hasło"**

✅ **Gotowe!** Możesz teraz logować się nowym hasłem.

**Wskazówka:** Działa też dla kont z OAuth - możesz ustawić hasło, aby móc logować się zarówno przez Google/Microsoft, jak i hasłem.

---

### Zmiana Emaila (bez pomocy admina!)

1. Zaloguj się do systemu
2. Kliknij **"Moje Konto"** w menu
3. Przewiń do sekcji **"Zmiana adresu email"**
4. Wypełnij formularz:
   - Nowy adres email
   - Aktualne hasło (dla bezpieczeństwa)
5. Kliknij **"Zmień email"**

✅ **Gotowe!** Przy następnym logowaniu użyj nowego emaila.

---

## 👨‍💼 Nowe Funkcje dla Administratorów

### Reset Hasła z Powiadomieniem Email

1. Przejdź do **"Zarządzanie Użytkownikami"**
2. Znajdź użytkownika na liście
3. Kliknij ikonę klucza 🔑 **(Resetuj hasło)**
4. Potwierdź akcję

**Co się stanie:**

✅ **Jeśli SMTP jest skonfigurowany:**
- System generuje silne hasło (16 znaków)
- Email jest wysyłany do użytkownika automatycznie
- Widzisz komunikat: ✅ "Email wysłany pomyślnie"
- Hasło pojawia się na ekranie (jednorazowo) do skopiowania

⚠️ **Jeśli SMTP nie jest skonfigurowany:**
- System generuje silne hasło (16 znaków)
- Widzisz komunikat: ⚠️ "Email nie został wysłany"
- Hasło pojawia się na ekranie - skopiuj je i przekaż użytkownikowi

**Treść emaila:**
- Profesjonalny szablon HTML
- Wyraźnie wyświetlone hasło
- Link do logowania
- Zalecenie zmiany hasła

---

## 💡 Inteligentne Komunikaty przy Logowaniu

### Problem, który rozwiązujemy:

Użytkownik ma połączone konto Google, ale próbuje zalogować się hasłem → Frustracja!

### Rozwiązanie:

System automatycznie wykrywa sytuację i pokazuje pomocny komunikat:

❌ **Stary komunikat:**
> "Błąd logowania: Nieprawidłowe dane."

✅ **Nowy komunikat:**
> "To konto ma powiązane logowanie przez Google. Użyj odpowiedniego przycisku poniżej aby się zalogować."

**Obsługuje:**
- Konta z Google OAuth
- Konta z Microsoft OAuth
- Konta z oboma dostawcami
- Jasne wskazówki, która metoda logowania jest prawidłowa

---

## 📋 Checklist - Co Zrobić Po Aktualizacji

### Dla Administratora Systemu:

- [ ] **Skopiuj `.env.example` do `.env`** (jeśli jeszcze nie masz)
- [ ] **Opcjonalnie: Skonfiguruj SMTP** (patrz sekcja "Konfiguracja Email" powyżej)
- [ ] **Uruchom aplikację** i sprawdź, czy działa
- [ ] **Przetestuj reset hasła** na koncie testowym
- [ ] **Sprawdź, czy email dociera** (jeśli SMTP skonfigurowany)
- [ ] **Poinformuj użytkowników** o nowych funkcjach

### Dla Użytkowników:

- [ ] **Wypróbuj zmianę hasła** w "Moje Konto"
- [ ] **Zaktualizuj email** jeśli potrzeba
- [ ] **Zapamiętaj nową ścieżkę:** Moje Konto → Zmiana hasła/emaila

---

## 🔧 Rozwiązywanie Problemów

### Email się nie wysyła

**Sprawdź:**
1. Czy wszystkie zmienne SMTP są ustawione w `.env`?
2. Czy używasz hasła aplikacji (Gmail) zamiast zwykłego hasła?
3. Czy firewall nie blokuje portu 587?
4. Czy SMTP_HOST i SMTP_PORT są poprawne?

**Tymczasowe rozwiązanie:**
- System nadal działa - hasło zostanie wyświetlone administratorowi
- Admin może przekazać hasło użytkownikowi ręcznie (SMS, komunikator, itp.)

### Użytkownik nie może zmienić hasła

**Najczęstsze przyczyny:**
- ❌ Podaje nieprawidłowe obecne hasło
- ❌ Nowe hasło jest za krótkie (min. 6 znaków)
- ❌ Hasła się nie zgadzają (nowe ≠ potwierdzone)

**Rozwiązanie:** Sprawdź komunikat błędu - system dokładnie wskazuje problem.

### Użytkownik nie może zmienić emaila

**Najczęstsze przyczyny:**
- ❌ Podaje nieprawidłowe hasło
- ❌ Nowy email jest już zajęty przez inne konto

**Rozwiązanie:** Sprawdź komunikat błędu systemu.

---

## 📚 Więcej Informacji

- **README.md** - Pełna dokumentacja projektu
- **CHANGELOG_ACCOUNT_FEATURES.md** - Szczegółowy opis zmian
- **FEATURE_SUMMARY.md** - Przegląd wszystkich funkcji
- **OAUTH_SETUP.md** - Konfiguracja OAuth

---

## 🎉 Co Nowego?

| Funkcja | Dla Kogo | Status |
|---------|----------|--------|
| Zmiana hasła przez użytkownika | 👤 Użytkownik | ✅ Nowe |
| Zmiana emaila przez użytkownika | 👤 Użytkownik | ✅ Nowe |
| Email przy resecie hasła | 👨‍💼 Admin | ✅ Nowe |
| Inteligentne błędy logowania | 👤 Użytkownik | ✅ Nowe |
| Status wysyłki email dla admina | 👨‍💼 Admin | ✅ Nowe |

---

**Wersja:** 1.1.0  
**Data:** 2026-01-01  
**Pytania?** Sprawdź dokumentację lub skontaktuj się z zespołem rozwoju.

