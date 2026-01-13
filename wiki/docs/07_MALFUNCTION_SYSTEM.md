# System Usterek

Kompletny przewodnik po systemie zgłaszania i śledzenia usterek w SzalasApp.

## 📋 Spis Treści

1. [Przegląd Systemu](#przegląd-systemu)
2. [Zgłaszanie Usterek](#zgłaszanie-usterek)
3. [Lista Usterek](#lista-usterek)
4. [Karta Usterki](#karta-usterki)
5. [Zarządzanie Usterkami (Admin)](#zarządzanie-usterkami-admin)
6. [Statusy Usterek](#statusy-usterek)
7. [Workflow](#workflow)
8. [Najlepsze Praktyki](#najlepsze-praktyki)

---

## Przegląd Systemu

System usterek umożliwia:
- 🔧 **Zgłaszanie** - Każdy może zgłosić problem
- 📸 **Dokumentowanie** - Zdjęcia uszkodzeń
- 📊 **Śledzenie** - Status każdej usterki
- 🔗 **Powiązanie** - Automatyczne łączenie ze sprzętem
- 🛡️ **Ochrona** - reCAPTCHA przeciw spamowi

### Pola Usterki

- **ID** - Automatycznie generowane
- **Sprzęt ID** - Powiązany sprzęt
- **Opis** - Szczegóły problemu
- **Zgłoszono przez** - Imię zgłaszającego (opcjonalne)
- **Data zgłoszenia** - Automatyczna
- **Status** - oczekuje / w trakcie / naprawiona / odrzucona
- **Uwagi admina** - Notatki administratora
- **Zdjęcia** - Lista URL do zdjęć

---

## Zgłaszanie Usterek

### Metoda 1: Z Karty Sprzętu

**Najłatwiejsza metoda!**

1. Otwórz kartę sprzętu (skanuj QR lub znajdź w liście)
2. Przewiń do sekcji "Zgłoś Nową Usterkę"
3. Wypełnij formularz
4. Rozwiąż reCAPTCHA
5. Kliknij "Zgłoś Usterkę"

**Formularz:**
```
┌─────────────────────────────────────────┐
│ Zgłoś Nową Usterkę dla NAMIOT_01        │
├─────────────────────────────────────────┤
│ Opis Usterki (obowiązkowo):             │
│ [____________________________________]  │
│ [____________________________________]  │
│                                         │
│ Zgłoszono przez (opcjonalnie):          │
│ [Jan Kowalski___________________]       │
│                                         │
│ Zdjęcia (opcjonalnie, max 5):           │
│ [Wybierz pliki...]                      │
│                                         │
│ [✓] Nie jestem robotem                  │
│                                         │
│ [Zgłoś Usterkę]                         │
└─────────────────────────────────────────┘
```

### Metoda 2: Z Listy Usterek (Przyszłość)

Planowane: Przycisk "Nowa Usterka" z wyborem sprzętu z listy.

### Walidacja

**Wymagane:**
- ✅ Opis usterki (min. 10 znaków)
- ✅ reCAPTCHA rozwiązana

**Opcjonalne:**
- Zgłoszono przez (domyślnie "Anonim")
- Zdjęcia (max 5, każde ≤5MB)

### Ochrona przed Spamem

**reCAPTCHA Enterprise:**
- Weryfikacja czy to człowiek
- Ocena ryzyka (score 0.0-1.0)
- Blokowanie podejrzanych zgłoszeń
- Transparentny dla użytkownika

**Limity:**
- Max 5 zdjęć per zgłoszenie
- Każde zdjęcie ≤5MB
- Tylko obrazy (JPG, PNG, GIF, WebP)

---

## Lista Usterek

### Dostęp
**URL:** `/usterki`

### Widok Listy

**Tabela z kolumnami:**
- **Sprzęt** - ID i typ sprzętu (link)
- **Opis** - Krótki opis (max 100 znaków)
- **Status** - Badge kolorowy
- **Zgłoszono przez** - Imię osoby
- **Data** - Data zgłoszenia
- **Akcje** - Link do szczegółów

```
┌──────────────┬────────────────────┬──────────┬────────────┬────────────┬────────┐
│ Sprzęt       │ Opis               │ Status   │ Przez      │ Data       │ Akcje  │
├──────────────┼────────────────────┼──────────┼────────────┼────────────┼────────┤
│ NAMIOT_01    │ Dziura przy wejściu│ Oczekuje │ Jan K.     │ 2026-01-01 │ Detalе │
│ (Namiot)     │                    │          │            │            │        │
├──────────────┼────────────────────┼──────────┼────────────┼────────────┼────────┤
│ PLANDEKA_02  │ Brak śledzi        │ W trakcie│ Anna W.    │ 2026-01-02 │ Detale │
│ (Plandeka)   │                    │          │            │            │        │
└──────────────┴────────────────────┴──────────┴────────────┴────────────┴────────┘
```

### Filtrowanie

**Dostępne filtry:**
- **Status** - oczekuje / w trakcie / naprawiona / odrzucona
- **Magazyn** - Lokalizacja sprzętu
- **ID Sprzętu** - Wybór konkretnego sprzętu
- **Szukaj** - Wyszukiwanie w opisie

**Przykład:**
```
Status: [Oczekuje]  Magazyn: [Magazyn główny]  Sprzęt: [Wszystkie]
                                                        [Filtruj]
```

### Sortowanie

- Data zgłoszenia (najnowsze/najstarsze)
- Status
- ID sprzętu
- Zgłaszający

---

## Karta Usterki

### Dostęp
**URL:** `/usterka/<usterka_id>`

### Layout Karty

```
┌─────────────────────────────────────────────────────────┐
│ Karta Usterki: NAMIOT_01 - ID: abc123                   │
├──────────────────┬──────────────────────────────────────┤
│                  │                                      │
│   GALERIA ZDJĘĆ │  SZCZEGÓŁY ZGŁOSZENIA                 │
│                  │                                      │
│   [Karuzela]     │  • ID Usterki: abc123                │
│                  │  • Powiązany Sprzęt: NAMIOT_01       │
│   [Miniatury]    │  • Status: Oczekuje                  │
│                  │  • Data: 2026-01-01                  │
│                  │  • Przez: Jan Kowalski               │
│                  │                                      │
│                  │  OPIS PROBLEMU                       │
│                  │  [Pełny tekst opisu...]              │
│                  │                                      │
│                  │  UWAGI ADMINA (jeśli są)             │
│                  │  [Notatki administratora...]         │
└──────────────────┴──────────────────────────────────────┘
```

### Informacje Widoczne

**Dla wszystkich:**
- ✅ ID usterki
- ✅ Powiązany sprzęt (link do karty)
- ✅ Status (badge)
- ✅ Data zgłoszenia
- ✅ Zgłaszający
- ✅ Pełny opis
- ✅ Galeria zdjęć
- ✅ Uwagi admina (jeśli są)

**Dla adminów:**
- ✏️ Przycisk "Edytuj" (prawy górny róg)

---

## Zarządzanie Usterkami (Admin)

### Edycja Usterki

**Dostęp:** Karta usterki → Przycisk ✏️

**Co można zmieniać:**

#### 1. Status

**Dropdown z opcjami:**
- **Oczekuje na akceptację** - Domyślny dla nowych
- **W trakcie naprawy** - Praca w toku
- **Naprawiona** - Ukończone
- **Odrzucona** - Błędne/duplikat/nieuzasadnione

#### 2. Uwagi Administratora

**Pole tekstowe:**
- Notatki o naprawie
- Użyte części
- Czas naprawy
- Koszty (jeśli są)
- Powód odrzucenia (jeśli odrzucona)

**Przykład uwag:**
```
Naprawiono 2026-01-05.
Użyto: zestaw naprawczy, taśma wzmacniająca
Czas pracy: 2h
Koszt: 50zł
Sprzęt gotowy do użycia.
```

### Workflow Admina

```
1. Nowe zgłoszenie → Status: "Oczekuje"
   ↓
2. Admin sprawdza → Zmienia na "W trakcie"
   ↓
3. Naprawa wykonana → Zmienia na "Naprawiona"
   ↓
4. Dodaje uwagi (co zrobiono)
   ↓
5. Zapisuje
```

**Alternatywnie:**
```
1. Nowe zgłoszenie → Status: "Oczekuje"
   ↓
2. Admin sprawdza → Błędne/duplikat
   ↓
3. Zmienia na "Odrzucona"
   ↓
4. Dodaje powód w uwagach
   ↓
5. Zapisuje
```

---

## Statusy Usterek

### Badge Kolorowy

Każdy status ma unikalny kolor dla łatwej identyfikacji:

| Status | Badge | Kolor | Znaczenie |
|--------|-------|-------|-----------|
| Oczekuje | `bg-warning text-dark` | 🟡 Żółty | Nowe zgłoszenie |
| W trakcie | `bg-info text-dark` | 🔵 Niebieski | Naprawa w toku |
| Naprawiona | `bg-success` | 🟢 Zielony | Ukończone |
| Odrzucona | `bg-danger` | 🔴 Czerwony | Nieuzasadnione |

### Kiedy Używać?

**Oczekuje:**
- Świeżo zgłoszone
- Czeka na weryfikację admina
- Nie rozpoczęto prac

**W trakcie:**
- Admin potwierdził problem
- Praca nad naprawą rozpoczęta
- Może trwać kilka dni

**Naprawiona:**
- Naprawa ukończona
- Sprzęt sprawdzony
- Gotowy do użycia

**Odrzucona:**
- Błędne zgłoszenie
- Duplikat innej usterki
- Nie wymaga naprawy
- Spam

---

## Workflow

### Scenariusz 1: Standardowa Naprawa

```
DZIEŃ 1 - Zgłoszenie
┌─────────────────────────────────────────┐
│ 1. Użytkownik znajduje dziurę w namiocie│
│ 2. Skanuje QR kod na namiocie           │
│ 3. Wypełnia formularz zgłoszenia        │
│ 4. Dodaje 2 zdjęcia uszkodzenia         │
│ 5. Wysyła zgłoszenie                    │
│    Status: OCZEKUJE                     │
└─────────────────────────────────────────┘

DZIEŃ 2 - Weryfikacja
┌─────────────────────────────────────────┐
│ 1. Admin dostaje powiadomienie          │
│ 2. Sprawdza zgłoszenie                  │
│ 3. Potwierdza problem                   │
│ 4. Zmienia status na W TRAKCIE          │
│ 5. Dodaje uwagę: "Zamówiono zestaw"     │
└─────────────────────────────────────────┘

DZIEŃ 7 - Naprawa
┌─────────────────────────────────────────┐
│ 1. Zestaw naprawczy dostarczony         │
│ 2. Admin naprawia dziurę                │
│ 3. Zmienia status na NAPRAWIONA         │
│ 4. Dodaje uwagi o naprawie              │
│ 5. Użytkownik może sprawdzić status     │
└─────────────────────────────────────────┘
```

### Scenariusz 2: Odrzucenie

```
DZIEŃ 1 - Zgłoszenie
┌─────────────────────────────────────────┐
│ Użytkownik zgłasza: "Brak śledzi"       │
│ Status: OCZEKUJE                        │
└─────────────────────────────────────────┘

DZIEŃ 1 - Weryfikacja
┌─────────────────────────────────────────┐
│ Admin sprawdza:                         │
│ • Śledzie istnieją, są w zestawie       │
│ • Użytkownik ich nie znalazł            │
│                                         │
│ Admin:                                  │
│ • Zmienia na ODRZUCONA                  │
│ • Dodaje uwagę: "Śledzie są w kieszeni" │
└─────────────────────────────────────────┘
```

---

## Najlepsze Praktyki

### Dla Użytkowników

**✅ Dobre zgłoszenie:**
```
Opis: "Dziura w materiale namiotu przy głównym wejściu, 
       ok. 15cm średnicy. Prawdopodobnie powstała podczas 
       rozkładania na obozie letnim."

Zdjęcia: 3 (ogólny widok, zbliżenie dziury, lokalizacja)
Zgłoszono przez: "Jan Kowalski, patrol Orły"
```

**❌ Słabe zgłoszenie:**
```
Opis: "namiot zepsuty"
Zdjęcia: 0
Zgłoszono przez: ""
```

**Wskazówki:**
1. **Bądź szczegółowy** - Im więcej info, tym lepiej
2. **Dodaj zdjęcia** - Obraz wart więcej niż słowa
3. **Podaj kontakt** - Na wypadek pytań
4. **Lokalizacja problemu** - Gdzie dokładnie?
5. **Jak powstało** - Pomaga zapobiegać

### Dla Adminów

**Szybka weryfikacja:**
1. Sprawdź czy to nowe zgłoszenie (czy nie duplikat)
2. Oceń pilność (krytyczne vs. można poczekać)
3. Ustaw priorytet
4. Zmień status na "W trakcie" jeśli rozpoczynasz
5. Aktualizuj uwagi regularnie

**Dokumentacja naprawy:**
```
✅ Data naprawy: 2026-01-05
✅ Wykonał: Jan Kowalski
✅ Użyte materiały: Zestaw naprawczy Tent Repair Kit
✅ Czas pracy: 2 godziny
✅ Koszt: 50zł (materiały) + 0zł (praca wolontariat)
✅ Notatki: Naprawa trwała, sprzęt przetestowany
✅ Status sprzętu zaktualizowany: dobry → bardzo dobry
```

**Odrzucanie:**
- Zawsze dodaj powód w uwagach
- Bądź miły i pomocny
- Może zasugeruj rozwiązanie
- Jeśli duplikat, podlinkuj oryginał (ID)

---

## FAQ

### Q: Czy mogę edytować swoje zgłoszenie?
**A:** Nie. Po wysłaniu tylko admin może edytować. Zgłoś nowe lub poproś admina.

### Q: Jak długo czeka na odpowiedź?
**A:** Zależy od admina. Zwykle 1-3 dni robocze. Pilne sprawy możesz zgłosić bezpośrednio.

### Q: Mogę zgłosić wiele usterek dla jednego sprzętu?
**A:** Tak! Każdy problem = osobne zgłoszenie. Łatwiej zarządzać.

### Q: Co jeśli nie wiem ID sprzętu?
**A:** Zeskanuj QR na sprzęcie lub znajdź w liście sprzętu.

### Q: Czy dostanę powiadomienie gdy naprawi?
**A:** Obecnie nie. Sprawdź status na karcie usterki. Planujemy powiadomienia email.

### Q: Limit zgłoszeń?
**A:** Brak limitu. reCAPTCHA chroni przed spamem, ale prawdziwi użytkownicy mogą zgłaszać dowolnie.

---

## Integracje

### Z Kartą Sprzętu

- Lista usterek na karcie sprzętu
- Link do zgłoszenia nowej z karty
- Licznik usterek

### Z Listą Sprzętu

- Filtr "pokaż tylko ze usterkami"
- Wskaźnik ilości usterek na karcie

### Z Eksportami

- Eksport zawiera liczbę usterek
- Możliwy osobny eksport usterek (przyszłość)

---

**Ostatnia aktualizacja:** 2026-01-01  
**Wersja:** 1.0.0

**Następny dokument:** [Eksport Danych](08_DATA_EXPORT.md)

