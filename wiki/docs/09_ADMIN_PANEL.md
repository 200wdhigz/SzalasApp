# Panel Administratora
**Wersja:** 1.0.0
**Ostatnia aktualizacja:** 2026-01-01  

---

- ❌ Nie usuwaj użytkowników bez sprawdzenia ich danych
- ❌ Nie ignoruj komunikatów synchronizacji
- ❌ Nie nadawaj admin wszystkim
- ❌ Nie usuwaj własnego konta admina
### DON'T:

- ✅ Używaj przycisku usuwania w aplikacji (nie Console)
- ✅ Weryfikuj hasła przed przekazaniem użytkownikom
- ✅ Dokumentuj zmiany w uwagach
- ✅ Rób backup przed masowymi zmianami
- ✅ Synchronizuj użytkowników regularnie
### DO:

## 💡 Najlepsze Praktyki

---

- Rezultat
- Kiedy
- Co
- Kto
Wszystkie akcje logowane:

### Audit Trail

```
    # Tylko admin
def admin_function():
@admin_required
```python

### Role-Based Access Control

```
<input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">
```html
Wszystkie akcje admina chronione tokenem CSRF:

### CSRF Protection

## 🛡️ Bezpieczeństwo

---

- Lista usterek (przyszłość)
- Lista sprzętu
**Dostępne z:**

- PDF - Raport PDF
- DOCX - Word raport
- XLSX - Excel
- CSV - Surowe dane
**Formaty:**

### 4. Eksport Danych

- Oczekuje → Odrzucona
- Oczekuje → W trakcie → Naprawiona
**Statusy:**

- Dodanie uwag administratora
- Zmiana statusu
- Karta usterki → Przycisk ✏️
**Edycja usterki:**

### 3. Zarządzanie Usterkami

- Import aktualizuje istniejące rekordy
- Usuwanie tylko przez Firebase Console (bezpieczeństwo)
**Uwagi:**

- Dodawanie zdjęć
- Wszystkie pola (oprócz ID)
- Karta sprzętu → Przycisk ✏️
**Edycja:**

- `/sprzet/import` - Masowy import CSV/XLSX
- `/sprzet/edit/new` - Ręczne dodanie
**Dodawanie:**

### 2. Zarządzanie Sprzętem

```
5. Pokazuje raport: "usunięto X, dodano Y"
4. Dodaje brakujące z Auth
3. Usuwa "martwe" wpisy z Firestore
2. System porównuje Firebase Auth ↔ Firestore
1. Kliknij "🔄 Synchronizuj"
```

#### Synchronizacja

```
6. Przekaż użytkownikowi
5. Skopiuj hasło jeśli email failed
   - Wyświetla hasło administratorowi
   - Wysyła email do użytkownika (jeśli SMTP)
   - Generuje silne hasło (16 znaków)
4. System:
3. Potwierdź
2. Kliknij 🔑 (klucz)
1. Znajdź użytkownika na liście
```

#### Reset Hasła

```
4. ✅ Użytkownik utworzony w Firebase Auth i Firestore
3. Kliknij "Utwórz Użytkownika"
   - [✓] Administrator (opcjonalnie)
   - Hasło (min. 6 znaków)
   - Email
2. Wypełnij:
1. Kliknij "+ Nowy Użytkownik"
```

#### Rejestracja Użytkownika

- 🔄 **Synchronizacja z Firebase Auth**
- 🗑️ **Usuwanie użytkowników** (trwałe)
- 🔑 **Reset haseł** (z email notification)
- ⏸️ **Wyłączanie/włączanie** kont
- ✏️ **Edycja użytkowników** (rola, status)
- ➕ **Rejestracja nowych użytkowników**
**Dostępne akcje:**

**Lokalizacja:** `/admin/users`

### 1. Zarządzanie Użytkownikami

## 📋 Funkcje Administratora

- Token CSRF aktywny
- Zalogowanie do systemu
- Konto z rolą administratora

## 🔑 Wymagania

Kompletny przewodnik po wszystkich funkcjach administracyjnych w SzalasApp.


