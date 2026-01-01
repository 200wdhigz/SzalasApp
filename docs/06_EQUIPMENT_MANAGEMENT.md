# Zarządzanie Sprzętem

Kompletny przewodnik po systemie zarządzania sprzętem w SzalasApp.

## 📋 Spis Treści

1. [Przegląd Systemu](#przegląd-systemu)
2. [Lista Sprzętu](#lista-sprzętu)
3. [Karta Sprzętu](#karta-sprzętu)
4. [Dodawanie Sprzętu](#dodawanie-sprzętu)
5. [Edycja Sprzętu](#edycja-sprzętu)
6. [Import Sprzętu](#import-sprzętu)
7. [Galerie Zdjęć](#galerie-zdjęć)
8. [Kody QR](#kody-qr)
9. [Eksport Danych](#eksport-danych)
10. [Najlepsze Praktyki](#najlepsze-praktyki)

---

## Przegląd Systemu

System zarządzania sprzętem pozwala na:
- 📦 **Katalogowanie** - Pełna baza sprzętu z szczegółami
- 📸 **Galerie zdjęć** - Wielozdjęciowe galerie dla każdego przedmiotu
- 🔍 **Filtrowanie** - Zaawansowane wyszukiwanie i sortowanie
- 📊 **Eksport** - CSV, XLSX, DOCX, PDF
- 🔗 **QR kody** - Szybki dostęp do kart sprzętu
- 🔧 **Usterki** - Śledzenie zgłoszonych problemów

### Pola Sprzętu

Każdy przedmiot w systemie ma następujące pola:

#### Podstawowe Informacje
- **ID** - Unikalny identyfikator (np. "namiot_01", "plandeka_blue_02")
- **Typ** - Kategoria sprzętu (namiot, plandeka, itp.)
- **Stan ogólny** - bardzo dobry / dobry / średni / DO KONSERWACJI
- **Lokalizacja** - Gdzie znajduje się sprzęt (magazyn główny, szatnia, itp.)
- **Przeznaczenie** - Do czego służy

#### Szczegóły Techniczne
- **Wodoszczelność** - Stopień ochrony przed wodą
- **Kolor dachu** - Dla identyfikacji
- **Kolor boków** - Dla identyfikacji
- **Znak szczególny** - Unikalne cechy
- **Ilość zapałek** - Liczba elementów mocujących

#### Historia
- **Zakup** - Data i miejsce zakupu
- **Przejęcie** - Skąd przejęto
- **Czy wraca** - Informacja o zwrocie
- **Historia** - Długi opis historii przedmiotu
- **Uwagi konserwacyjne** - Notatki o konserwacji

#### Media
- **Zdjęcia** - Lista URL do zdjęć w Google Cloud Storage

---

## Lista Sprzętu

### Dostęp
**URL:** `/sprzet` lub przycisk "Lista Sprzętu" w menu

### Funkcje Listy

#### 1. Widok Kartkowy
```
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  Zdjęcie    │ │  Zdjęcie    │ │  Zdjęcie    │
│             │ │             │ │             │
│ NAMIOT_01   │ │ NAMIOT_02   │ │ PLANDEKA_01 │
│ Bardzo dobry│ │ Dobry       │ │ Średni      │
└─────────────┘ └─────────────┘ └─────────────┘
```

Każda karta pokazuje:
- Główne zdjęcie (lub placeholder)
- ID sprzętu
- Typ
- Stan ogólny (z kolorowym badge)
- Lokalizację
- Link "Zobacz szczegóły"

#### 2. Filtrowanie

**Filtry dostępne:**
- **Typ sprzętu** - Dropdown z unikalnymi typami
- **Stan ogólny** - Dropdown ze stanami
- **Lokalizacja** - Dropdown z magazynami
- **Szukaj** - Pole tekstowe (szuka w ID, typie, lokalizacji)

**Przykład użycia:**
```
Typ: [Namiot]  Stan: [Dobry]  Lokalizacja: [Wszystkie]  🔍 [Szukaj: patrol]
                                                            [Filtruj]
```

#### 3. Sortowanie

Dostępne opcje:
- ID (rosnąco/malejąco)
- Typ (A-Z / Z-A)
- Stan ogólny
- Lokalizacja
- Data dodania

#### 4. Eksport

Przyciski eksportu:
- 📄 **CSV** - Dane surowe do analizy
- 📊 **XLSX** - Arkusz kalkulacyjny Excel
- 📝 **DOCX** - Dokument Word ze szczegółami
- 📕 **PDF** - Raport PDF do druku

---

## Karta Sprzętu

### Dostęp
**URL:** `/sprzet/<sprzet_id>` (np. `/sprzet/namiot_01`)

### Layout Karty

```
┌─────────────────────────────────────────────────────────┐
│ Karta Sprzętu: NAMIOT_01 - NAMIOT                       │
├──────────────────┬──────────────────────────────────────┤
│                  │                                       │
│   GALERIA ZDJĘĆ │  DANE TECHNICZNE I HISTORIA          │
│                  │                                       │
│   [Karuzela]     │  [Tabele z danymi]                   │
│                  │                                       │
│   [Miniatury]    │  [Zgłoszone usterki]                 │
│                  │                                       │
├──────────────────┴──────────────────────────────────────┤
│  ZGŁOŚ NOWĄ USTERKĘ                                      │
│  [Formularz]                                             │
└─────────────────────────────────────────────────────────┘
```

### Galeria Zdjęć

**Funkcje:**
- 🖼️ **Karuzela** - Przewijanie zdjęć
- 🔍 **Lightbox** - Kliknięcie otwiera pełny widok
- 📸 **Miniatury** - Szybka nawigacja
- ⚙️ **Proporcje 4:3** - Spójny wygląd

**Obsługa:**
- Strzałki do przewijania
- Kliknięcie miniatury zmienia główne zdjęcie
- Kliknięcie głównego zdjęcia otwiera modal

### Dane Techniczne

**Trzy kolumny:**

**Kolumna 1: Informacje Podstawowe**
- ID Sprzętu
- Typ Sprzętu
- Stan Ogólny (z kolorowym badge)
- Obecna Lokalizacja
- Przeznaczenie

**Kolumna 2: Szczegóły Techniczne**
- Wodoszczelność
- Kolor Dachu
- Kolor Boków
- Znak Szczególny
- Ilość Zapałek

**Kolumna 3: Historia i Konserwacja**
- Zakup
- Przejęty
- Wymaga Powrotu
- Historia (skrócona + pełna)
- Uwagi Konserwacyjne (skrócone + pełne)

### Kod QR

**Przycisk:** 🔗 QR (w prawym górnym rogu)

**Funkcje:**
- Generuje QR kod do karty sprzętu
- Link do zewnętrznej strony lub aplikacji
- Możliwość pobrania PNG
- Bezpośrednie otwarcie linku

**Zastosowanie:**
- Naklejki na sprzęcie
- Szybki dostęp w magazynie
- Inwentaryzacja

### Zgłoszone Usterki

**Sekcja pokazuje:**
- Liczbę usterek
- Listę wszystkich usterek dla tego sprzętu
- Status każdej usterki (badge kolorowy)
- Link do szczegółów usterki

---

## Dodawanie Sprzętu

### Metoda 1: Ręczne Dodanie (Admin)

**Kroki:**
1. Przejdź do `/sprzet/edit/new`
2. Wypełnij formularz
3. (Opcjonalnie) Dodaj zdjęcia
4. Zapisz

**Wymagane pola:**
- ID
- Typ
- Lokalizacja

### Metoda 2: Import CSV/XLSX (Admin)

Zobacz sekcję [Import Sprzętu](#import-sprzętu)

---

## Edycja Sprzętu

### Dostęp
🔑 **Wymagane:** Uprawnienia administratora

**Gdzie:** Karta sprzętu → Przycisk ✏️ "Edytuj"

### Co Można Edytować?

**Wszystkie pola:**
- ✅ Informacje podstawowe
- ✅ Szczegóły techniczne
- ✅ Historia i uwagi
- ❌ ID (niemodyfikowalne po utworzeniu)

**Zdjęcia:**
- ➕ Dodawanie nowych
- ❌ Usuwanie (trzeba zrobić ręcznie w Firebase Console)

### Formularz Edycji

```html
┌─────────────────────────────────────┐
│ Edycja Sprzętu: NAMIOT_01          │
├─────────────────────────────────────┤
│ ID: namiot_01 [tylko odczyt]       │
│ Typ: [_____________]                │
│ Stan: [Dropdown]                    │
│ Lokalizacja: [_____________]        │
│ ...                                 │
│ [Anuluj]  [Zapisz Zmiany]         │
└─────────────────────────────────────┘
```

---

## Import Sprzętu

### Dostęp
🔑 **Wymagane:** Uprawnienia administratora

**URL:** `/sprzet/import`

### Obsługiwane Formaty

- **CSV** - Kodowanie UTF-8
- **XLSX** - Excel 2007+

### Wymagane Kolumny

**Obowiązkowe:**
- `id` - Unikalny identyfikator
- `typ` - Typ sprzętu
- `lokalizacja` - Gdzie się znajduje

**Opcjonalne (wszystkie inne pola):**
- `stan_ogolny`
- `przeznaczenie`
- `wodoszczelnosc`
- `kolor_dachu`
- `kolor_bokow`
- `znak_szczegolny`
- `zapalki`
- `zakup`
- `przejecie`
- `czyWraca`
- `historia`
- `uwagi`

### Przykład CSV

```csv
id,typ,stan_ogolny,lokalizacja,przeznaczenie
namiot_01,Namiot,bardzo dobry,Magazyn główny,Biwaki
plandeka_blue_01,Plandeka,dobry,Magazyn główny,Osłona od deszczu
latarnia_01,Latarnia,średni,Szatnia,Oświetlenie
```

### Proces Importu

**Kroki:**
1. Przygotuj plik CSV/XLSX
2. Przejdź do `/sprzet/import`
3. Wybierz plik
4. Kliknij "Importuj"
5. System:
   - Waliduje dane
   - Pokazuje podgląd
   - Tworzy/aktualizuje rekordy
6. Otrzymujesz raport:
   ```
   ✅ Pomyślnie zaimportowano/zaktualizowano 15 pozycji.
   ```

### Aktualizacja vs. Tworzenie

**Logika:**
- Jeśli ID istnieje → **Aktualizacja** istniejącego rekordu
- Jeśli ID nowe → **Utworzenie** nowego rekordu

**Przykład:**
```
Importujesz plik z:
- namiot_01 (istnieje) → Zaktualizuje dane
- namiot_05 (nowy) → Utworzy nowy rekord
```

### Obsługa Błędów

**Typowe problemy:**

**1. Brak wymaganych kolumn**
```
❌ Plik musi zawierać kolumny: id, typ, lokalizacja
```

**2. Pusteavalues w wymaganych polach**
```
❌ Wiersz 3: Brak wartości w kolumnie 'id'
```

**3. Błąd formatu pliku**
```
❌ Nie można odczytać pliku. Upewnij się, że to poprawny CSV/XLSX.
```

---

## Galerie Zdjęć

### Upload Zdjęć

**Gdzie:**
- Podczas tworzenia sprzętu
- Podczas edycji sprzętu
- Przy zgłaszaniu usterki

**Ograniczenia:**
- Maksymalnie 5 zdjęć na raz
- Każde zdjęcie ≤ 5MB
- Tylko pliki obrazów (JPG, PNG, GIF, etc.)

### Przechowywanie

**Lokalizacja:** Google Cloud Storage

**Struktura:**
```
szalas-app.appspot.com/
  sprzet/
    namiot_01/
      photo1.jpg
      photo2.jpg
    plandeka_01/
      photo1.jpg
  usterki/
    usterka_id_123/
      photo1.jpg
```

### Wyświetlanie

**Karuzela:**
- Proporcje 4:3
- Object-fit: cover (kadrowanie)
- Nawigacja strzałkami
- Wskaźniki ilości zdjęć

**Miniatury:**
- 100x65px
- Scroll horyzontalny
- Aktywna ma border niebieski

**Lightbox (modal):**
- Pełnoekranowy widok
- Nawigacja między zdjęciami
- Zamknięcie przyciskiem X lub Esc

---

## Kody QR

### Generowanie

**Lokalizacja:** Karta sprzętu → Przycisk "QR"

**Modal pokazuje:**
- Wygenerowany kod QR
- Link docelowy
- Przyciski akcji:
  - **Otwórz stronę** - Nowa karta
  - **Pobierz QR** - PNG do druku
  - **Zamknij**

### Konfiguracja

**Link docelowy:**
```
https://200wdhigz.github.io/sprzet/{sprzet_id}
```

Lub dla developmentu:
```
https://200wdhigz.github.io/sprzet/{sprzet_id}?dev
```

### Zastosowania

**1. Fizyczne naklejki**
```
Wydrukuj QR → Nalip na sprzęt → Skanuj smartfonem → Instant karta sprzętu
```

**2. Inwentaryzacja**
```
Skanuj QR → Sprawdź stan → Zgłoś usterkę (jeśli trzeba)
```

**3. Wypożyczenia**
```
Skanuj QR → Zapisz ID → Zwróć później
```

---

## Eksport Danych

### Typy Eksportu

#### 1. CSV (Comma-Separated Values)

**Zastosowanie:**
- Import do Excel/Google Sheets
- Analiza danych
- Przetwarzanie skryptami

**Zawartość:**
- Wszystkie pola sprzętu
- Kodowanie UTF-8
- Separator: przecinek

**Przykład:**
```csv
id,typ,stan_ogolny,lokalizacja
namiot_01,Namiot,bardzo dobry,Magazyn główny
```

#### 2. XLSX (Microsoft Excel)

**Zastosowanie:**
- Edycja w Excel
- Filtrowanie i sortowanie
- Generowanie wykresów

**Zawartość:**
- Formatowane nagłówki (pogrubione)
- Szerokości kolumn auto-fit
- Wszystkie dane

#### 3. DOCX (Microsoft Word)

**Zastosowanie:**
- Raporty
- Dokumentacja
- Drukowanie

**Zawartość:**
- Tytuł raportu
- Lista sprzętu z detalami
- Formatowanie (nagłówki, sekcje)
- Informacje o stanie dla każdego elementu

**Format:**
```
RAPORT SPRZĘTU
Data: 2026-01-01

=== NAMIOT_01 ===
Typ: Namiot
Stan: bardzo dobry
Lokalizacja: Magazyn główny
[szczegóły...]

=== NAMIOT_02 ===
...
```

#### 4. PDF (Portable Document Format)

**Zastosowanie:**
- Raportowanie
- Archiwizacja
- Dystrybucja (niemodyfikowalne)

**Zawartość:**
- Profesjonalny layout
- Tabela ze wszystkimi danymi
- Header z datą generacji
- Paginacja

---

## Najlepsze Praktyki

### Nazewnictwo ID

✅ **Dobre przykłady:**
```
namiot_patrol_01
plandeka_blue_02
latarnia_solar_03
```

❌ **Złe przykłady:**
```
n1 (za krótkie)
Namiot 01 (spacje)
namiot#01 (znaki specjalne)
```

**Zasady:**
- Małe litery
- Podkreślniki zamiast spacji
- Numeracja z zerami (01, 02, nie 1, 2)
- Opis + identyfikator

### Aktualizacja Danych

**Jak często?**
- ✅ Po każdym użyciu sprzętu
- ✅ Po naprawach/konserwacji
- ✅ Przy zmianie lokalizacji
- ✅ Minimum raz na kwartał (audyt)

**Co sprawdzać?**
- Stan ogólny
- Lokalizacja
- Uwagi konserwacyjne
- Czy wszystkie usterki zamknięte?

### Zdjęcia

**Rób zdjęcia:**
- 📸 Z różnych kątów
- 📸 Znaki szczególne
- 📸 Uszkodzenia
- 📸 Etykiety/numery

**Nie rób zdjęć:**
- ❌ Rozmazanych
- ❌ Za ciemnych
- ❌ Z osobami (RODO)
- ❌ Zbyt ciężkich (>5MB)

### Konserwacja

**Regularnie:**
1. Sprawdź stan sprzętu
2. Zaktualizuj pole "stan_ogolny"
3. Dodaj uwagi konserwacyjne
4. Jeśli trzeba, zgłoś usterkę

**Przed sezonem:**
1. Pełny audyt wszystkich pozycji
2. Naprawa usterek
3. Uzupełnienie braków
4. Aktualizacja dokumentacji

---

## Przykładowe Scenariusze

### Scenariusz 1: Dodanie Nowego Sprzętu

```
1. Admin → "Lista Sprzętu" → "Dodaj Sprzęt"
2. Wypełnia formularz:
   - ID: namiot_green_05
   - Typ: Namiot
   - Stan: bardzo dobry
   - Lokalizacja: Magazyn główny
   - [inne pola...]
3. Dodaje 3 zdjęcia
4. "Zapisz"
5. ✅ Sprzęt utworzony
6. Generuje QR kod
7. Drukuje i nakle na namiot
```

### Scenariusz 2: Zgłoszenie Usterki

```
1. Użytkownik → Skanuje QR na sprzęcie
2. Otwiera się karta sprzętu
3. Przewija do "Zgłoś Nową Usterkę"
4. Wypełnia:
   - Opis: "Dziura w materiale przy wejściu"
   - Zgłoszono przez: "Jan Kowalski"
   - Dodaje 2 zdjęcia uszkodzenia
5. Rozwiązuje reCAPTCHA
6. "Zgłoś Usterkę"
7. ✅ Usterka zapisana
8. Admin dostaje powiadomienie
```

### Scenariusz 3: Masowy Import

```
1. Admin przygotowuje Excel:
   - 20 nowych namiotów
   - 15 plandek
   - 10 latanek
2. Zapisuje jako CSV (UTF-8)
3. Przechodzi do /sprzet/import
4. Wybiera plik
5. System pokazuje podgląd
6. "Importuj"
7. ✅ 45 pozycji dodanych
8. Admin weryfikuje losowe pozycje
```

### Scenariusz 4: Inwentaryzacja

```
1. Admin → Eksport do XLSX
2. Drukuje listę
3. Idzie do magazynu
4. Skanuje QR każdego sprzętu
5. Weryfikuje stan na miejscu
6. Zaktualizuje stany w systemie
7. Zgłasza nowe usterki
8. Generuje raport PDF
```

---

## FAQ

### Q: Czy mogę zmienić ID sprzętu?
**A:** Nie. ID jest niezmienne po utworzeniu. Musisz usunąć i utworzyć ponownie.

### Q: Jak usunąć sprzęt?
**A:** Obecnie tylko przez Firebase Console. Planujemy dodać funkcję w aplikacji.

### Q: Limit zdjęć na sprzęt?
**A:** Brak limitu, ale upload max 5 na raz. Każde ≤5MB.

### Q: Czy mogę eksportować tylko filtrowane dane?
**A:** Obecnie eksport pobiera wszystko. Filtry działają tylko w widoku.

### Q: Co się stanie z usterkami po usunięciu sprzętu?
**A:** Pozostają w systemie z ID sprzętu. Rozważ archiwizację zamiast usuwania.

---

**Ostatnia aktualizacja:** 2026-01-01  
**Wersja:** 1.0.0

**Następny dokument:** [System Usterek](07_MALFUNCTION_SYSTEM.md)

