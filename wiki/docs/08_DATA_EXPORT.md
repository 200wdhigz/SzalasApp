# Eksport Danych

Kompletny przewodnik po eksportowaniu danych z SzalasApp.

## 📊 Dostępne Formaty

System SzalasApp obsługuje eksport danych w 4 formatach:

1. **CSV** - Comma-Separated Values (surowe dane)
2. **XLSX** - Microsoft Excel (arkusz kalkulacyjny)
3. **DOCX** - Microsoft Word (raport dokumentowy)
4. **PDF** - Portable Document Format (raport do druku)

---

## 📦 Eksport Listy Sprzętu

### Dostęp

**Lokalizacja:** Lista Sprzętu → Przyciski eksportu na górze strony

### Przyciski Eksportu

```
[📄 CSV] [📊 XLSX] [📝 DOCX] [📕 PDF]
```

### 1. Eksport CSV

**Zastosowanie:**
- Import do innych systemów
- Analiza danych w Excel/Google Sheets
- Przetwarzanie skryptami Python/R
- Backup danych

**Format:**
```csv
id,typ,stan_ogolny,lokalizacja,przeznaczenie,wodoszczelnosc,...
namiot_01,Namiot,bardzo dobry,Magazyn główny,Biwaki,3000mm,...
plandeka_01,Plandeka,dobry,Szatnia,Osłona,5000mm,...
```

**Cechy:**
- Kodowanie: UTF-8
- Separator: przecinek (,)
- Wszystkie kolumny ze sprzętu
- Brak formatowania
- Idealny do dalszej obróbki

**Pobieranie:**
```
Klik "CSV" → Plik zapisuje się jako: sprzet_export_YYYY-MM-DD.csv
```

### 2. Eksport XLSX

**Zastosowanie:**
- Edycja w Microsoft Excel
- Tworzenie wykresów i pivot tables
- Formatowanie danych
- Filtrowanie i sortowanie

**Format:**
- Nagłówki pogrubione
- Auto-fit szerokości kolumn
- Wszystkie dane sprzętu
- Jeden arkusz: "Sprzęt"

**Cechy:**
- Kompatybilny z Excel 2007+
- Można otwierać w LibreOffice/Google Sheets
- Zachowuje typy danych
- Obsługuje polskie znaki

**Pobieranie:**
```
Klik "XLSX" → Plik zapisuje się jako: sprzet_export_YYYY-MM-DD.xlsx
```

**Przykład użycia:**
1. Otwórz w Excel
2. Zastosuj AutoFilter
3. Sortuj po stanie
4. Twórz wykresy kondycji sprzętu

### 3. Eksport DOCX

**Zastosowanie:**
- Raporty dla zarządu
- Dokumentacja inwentaryzacji
- Drukowanie list
- Archiwizacja

**Format:**
```
RAPORT SPRZĘTU
Data generacji: 2026-01-01

=== NAMIOT_01 ===
Typ: Namiot
Stan: bardzo dobry
Lokalizacja: Magazyn główny
[pełne szczegóły...]

=== NAMIOT_02 ===
[...]
```

**Cechy:**
- Czytelne formatowanie
- Sekcje dla każdego sprzętu
- Nagłówki pogrubione
- Gotowe do druku

**Pobieranie:**
```
Klik "DOCX" → Plik zapisuje się jako: sprzet_raport_YYYY-MM-DD.docx
```

### 4. Eksport PDF

**Zastosowanie:**
- Oficjalne raporty
- Archiwizacja (format niemutowalny)
- Wysyłanie emailem
- Drukowanie

**Format:**
- Tabela ze wszystkimi danymi
- Header: Tytuł i data
- Footer: Paginacja
- Orientacja: Landscape (poziomo)

**Cechy:**
- Profesjonalny wygląd
- Gotowe do druku A4
- Automatyczna paginacja
- PDF/A dla archiwizacji

**Pobieranie:**
```
Klik "PDF" → Plik zapisuje się jako: sprzet_raport_YYYY-MM-DD.pdf
```

---

## 🔧 Eksport Listy Usterek

### Dostęp

**Lokalizacja:** Lista Usterek → Przyciski eksportu (planowane)

**Status:** 🚧 W przygotowaniu

**Planowane formaty:**
- CSV - Surowe dane usterek
- XLSX - Analiza w Excel
- PDF - Raport usterek

---

## 💾 Zawartość Eksportu

### Pola Sprzętu w Eksportach

**Wszystkie formaty zawierają:**

| Pole | Opis |
|------|------|
| id | Identyfikator sprzętu |
| typ | Rodzaj sprzętu |
| stan_ogolny | Ocena stanu |
| lokalizacja | Gdzie się znajduje |
| przeznaczenie | Do czego służy |
| wodoszczelnosc | Parametr wodoodporności |
| kolor_dachu | Identyfikacja |
| kolor_bokow | Identyfikacja |
| znak_szczegolny | Unikalne cechy |
| zapalki | Liczba elementów |
| zakup | Data i miejsce zakupu |
| przejecie | Skąd przejęto |
| czyWraca | Czy wymaga zwrotu |
| historia | Pełna historia |
| uwagi | Uwagi konserwacyjne |
| zdjecia | Liczba zdjęć |

### Dane Systemowe

**Dodatkowo:**
- Data eksportu
- Wersja aplikacji
- Liczba rekordów
- Użytkownik eksportujący (jeśli zalogowany)

---

## 🎯 Przykłady Użycia

### Scenariusz 1: Inwentaryzacja Roczna

```
1. Admin → Lista Sprzętu
2. Klik "PDF"
3. Drukuj raport
4. Idź do magazynu z wydrukowaną listą
5. Sprawdzaj fizycznie każdy element
6. Zaznaczaj co sprawdzone
7. Aktualizuj stany w systemie
8. Wygeneruj nowy PDF po aktualizacji
9. Archiwizuj oba (przed i po)
```

### Scenariusz 2: Analiza Kondycji Sprzętu

```
1. Admin → Lista Sprzętu
2. Klik "XLSX"
3. Otwórz w Excel
4. Zastosuj Pivot Table:
   - Wiersze: Stan ogólny
   - Wartości: Liczba
5. Utwórz wykres kołowy
6. Prezentuj zarządowi: 70% bardzo dobry, 25% dobry, 5% DO KONSERWACJI
```

### Scenariusz 3: Backup Danych

```
1. Co miesiąc:
2. Admin → Lista Sprzętu → CSV
3. Zapisz do folderu: Backups/YYYY/MM/
4. Nazwa: sprzet_backup_YYYY-MM-DD.csv
5. Upload do chmury (Google Drive/Dropbox)
6. Zachowuj historię 12 miesięcy
```

### Scenariusz 4: Import do Innego Systemu

```
1. Eksportuj CSV
2. Otwórz w edytorze (Notepad++/VSCode)
3. Sprawdź format kolumn
4. Mapuj kolumny do docelowego systemu
5. Importuj
```

---

## ⚙️ Konfiguracja Eksportu

### Zmienne Środowiskowe

Brak specjalnych zmiennych - eksport działa out-of-the-box.

### Limity

**Rozmiar danych:**
- CSV: Bez limitu (teoretycznie)
- XLSX: Do ~1 miliona wierszy
- DOCX: Do ~10,000 rekordów (wydajność)
- PDF: Do ~5,000 rekordów (wydajność)

**Timeout:**
- Eksport trwa max 30 sekund
- Dla większych dataset może być dłużej

### Optymalizacja

**Dla dużych zbiorów danych:**
1. Użyj CSV (najszybszy)
2. Filtruj przed eksportem (przyszła funkcja)
3. Eksportuj częściami

---

## 🔍 Filtrowany Eksport (Przyszłość)

**Planowane:**
- Eksport tylko filtrowanych wyników
- Wybór konkretnych kolumn
- Eksport zakresu dat
- Opcje sortowania

**Przykład:**
```
Filtr: Stan = "DO KONSERWACJI"
Eksport → Tylko sprzęt wymagający naprawy
```

---

## 🐛 Rozwiązywanie Problemów

### Problem: Plik nie pobiera się

**Rozwiązanie:**
1. Sprawdź blokadę pop-upów w przeglądarce
2. Sprawdź folder Pobrane
3. Spróbuj innej przeglądarki
4. Sprawdź dostęp do internetu

### Problem: Błędne kodowanie znaków (krzaczki)

**Rozwiązanie dla CSV:**
1. Otwórz w Notepad++
2. Zmień kodowanie na UTF-8
3. Zapisz
4. Otwórz ponownie w Excel:
   - Dane → Z tekstu → UTF-8

**Lub:**
1. Użyj XLSX zamiast CSV (nie ma problemów z kodowaniem)

### Problem: Excel pokazuje złe daty

**Rozwiązanie:**
1. W Excel: Dane → Tekst do kolumn
2. Wybierz format daty: YYYY-MM-DD
3. Zastosuj

### Problem: PDF się nie generuje

**Możliwe przyczyny:**
- Za dużo danych (>5000 rekordów)
- Problemy z czcionkami serwera

**Rozwiązanie:**
1. Użyj DOCX zamiast PDF
2. Konwertuj DOCX → PDF lokalnie
3. Lub podziel dane na mniejsze części

---

## 📊 Statystyki Eksportu

### Średni Czas Generacji

| Format | 100 rekordów | 1000 rekordów |
|--------|--------------|---------------|
| CSV | <1s | ~2s |
| XLSX | ~2s | ~5s |
| DOCX | ~3s | ~10s |
| PDF | ~5s | ~15s |

### Rozmiar Plików

| Format | 100 rekordów | 1000 rekordów |
|--------|--------------|---------------|
| CSV | ~50 KB | ~500 KB |
| XLSX | ~30 KB | ~200 KB |
| DOCX | ~100 KB | ~800 KB |
| PDF | ~200 KB | ~2 MB |

---

## 🎓 Best Practices

### DO:

- ✅ Eksportuj regularnie (backup)
- ✅ Nazywaj pliki z datą
- ✅ Archiwizuj stare eksporty
- ✅ Używaj CSV dla maksymalnej kompatybilności
- ✅ Używaj PDF dla oficjalnych raportów

### DON'T:

- ❌ Nie eksportuj zbyt często (obciąża serwer)
- ❌ Nie otwieraj CSV bezpośrednio w Excel (problemy z UTF-8)
- ❌ Nie udostępniaj plików publicznie (dane wrażliwe)
- ❌ Nie edytuj eksportowanych plików jako źródło prawdy

---

## 🔒 Bezpieczeństwo

### Eksportowane Dane

**Zawierają:**
- Informacje o sprzęcie (publiczne)
- Historię konserwacji (może być wrażliwe)
- Uwagi (mogą zawierać informacje wewnętrzne)

**Nie zawierają:**
- Danych osobowych użytkowników
- Haseł
- Tokenów OAuth
- Kluczy API

### Rekomendacje:

1. **Nie udostępniaj plików publicznie**
2. **Szyfruj przy wysyłaniu emailem**
3. **Przechowuj w bezpiecznej lokalizacji**
4. **Usuń stare backupy (po 1 roku)**
5. **Ogranicz dostęp** (tylko admin)

---

## 📚 Więcej Informacji

- [Zarządzanie Sprzętem](06_EQUIPMENT_MANAGEMENT.md) - Pełny przewodnik
- [Panel Administratora](09_ADMIN_PANEL.md) - Funkcje admina
- [FAQ](19_FAQ.md) - Pytania

---

**Ostatnia aktualizacja:** 2026-01-01  
**Wersja:** 1.0.0

