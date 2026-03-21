### Osiągnięcia — konfiguracja, warunki i przykłady

Ten dokument wyjaśnia dokładnie wszystkie pola dostępne podczas tworzenia i edycji definicji Osiągnięć oraz pokazuje, jak konfigurować warunki ich przyznawania — na bazie obecnych i przyszłych osiągnięć.

#### Kto ma dostęp
- Kwatermistrz lub Administrator:
  - włącza funkcję Osiągnięcia dla konkretnego użytkownika (flaga `features.achievements_enabled`),
  - może ręcznie przyznawać/odbierać odznaki użytkownikom (np. w uzasadnionych przypadkach).
- Tylko Administrator:
  - zarządza definicjami (lista, dodawanie, edycja, usuwanie).

Bez włączonej flagi u użytkownika żadne automatyczne przyznawanie nie zadziała.

---

### Pola definicji osiągnięcia (formularz Admin → Osiągnięcia)

- ID (slug)
  - Unikalny, techniczny identyfikator (np. `reporter-5`).
  - Używany w bazie i przy zapisie odznak u użytkownika.
  - Po utworzeniu nie podlega edycji (pole „tylko do odczytu” przy edycji).

- Nazwa
  - Tytuł wyświetlany w UI (np. „Reporter 5/5”).

- Opis
  - Krótki opis, kiedy odznaka jest przyznawana.

- Ikona
  - Najprościej: emoji (np. 🥉, ⚡, 🤝). Możesz też wpisać nazwę/skrót, jeśli w UI masz własne mapowanie.

- Kolejność
  - Liczba całkowita określająca kolejność wyświetlania (niższa = wcześniej).

- Włączone
  - Gdy odznaka jest wyłączona, nie będzie nigdy automatycznie przyznawana.

- Ukryte do zdobycia
  - Jeśli zaznaczone, użytkownik widzi, że istnieje ukryte osiągnięcie (ikona kłódki i tytuł „Ukryte osiągnięcie”),
    ale nazwa, opis i szczegóły są ukryte do chwili zdobycia.
  - W profilu użytkownika pasek postępu nie zdradza progu ani szczegółów (brak wartości liczbowych),
    aby nie ujawniać warunku przed zdobyciem.

- Warunek przyznania
  - Składa się z „Typu warunku” i (dla niektórych typów) dodatkowych parametrów.
  - Obsługiwane typy:
    1) Liczba zdarzeń (próg) — `event_count`
    2) Szybki zwrot (tego samego dnia) — `speedy_return`
    3) Pomocna dłoń (naprawa cudzej usterki) — `help_resolve`
    4) Liczba dodanych elementów (sprzęt) — `item_add_count`
    5) Liczba edycji elementów (sprzęt) — `item_edit_count`
    6) Liczba logów użytkownika (akcje w systemie) — `log_count`

---

### Jak działają typy warunków

#### 1) Liczba zdarzeń (próg) — `event_count`
- Przyznaje odznakę, gdy licznik zdarzeń dla użytkownika osiągnie co najmniej określony próg.
- Parametry w formularzu:
  - Zdarzenie (`event`):
    - „Zgłoszenie usterki” → `report_created` (liczone po `user_id` autora zgłoszenia),
    - „Dodanie wypożyczenia” → `loan_created` (liczone po e‑mailu w polu wypożyczenia `kontakt`, dopasowywanym do użytkownika).
  - Próg (`threshold`) — liczba całkowita ≥ 1.

Przykłady (stan na dziś):
- „Pierwsze Zgłoszenie” (`first_report`):
  - Typ: `event_count`
  - Zdarzenie: `report_created`
  - Próg: `1`

- „Reporter 5/5” (`five_reports`):
  - Typ: `event_count`
  - Zdarzenie: `report_created`
  - Próg: `5`

- „Aktywny Wypożyczający” (`ten_borrows`):
  - Typ: `event_count`
  - Zdarzenie: `loan_created`
  - Próg: `10`

Schemat zapisu w bazie (pole `condition` w definicji):
```json
{
  "type": "event_count",
  "event": "report_created" | "loan_created",
  "threshold": 5
}
```

Uwagi praktyczne:
- Zdarzenie `loan_created` zlicza wypożyczenia po adresie e‑mail z pola `kontakt`; dopasowanie do użytkownika odbywa się po e‑mailu. Upewnij się, że użytkownicy mają poprawne e‑maile.
- Odznaki są przyznawane idempotentnie (ta sama odznaka nie zostanie zapisana dwa razy).

#### 1a) Liczba dodanych elementów — `item_add_count`
- Przyznaje odznakę po osiągnięciu progu dodanych elementów w katalogu sprzętu przez użytkownika.
- Zliczanie odbywa się na podstawie dziennika aktywności (kolekcja `logs`): akcja `add`, `target_type='sprzet'` i `user_id` autora.
- Parametry:
  - Próg (`threshold`) — liczba całkowita ≥ 1 (wymagany).
  - Kategoria (`category`) — opcjonalna, zawęża liczenie do danej kategorii sprzętu (np. `namiot`, `przedmiot`, `zelastwo`, `kanadyjki`, `materace`, `magazyn`, `polka_skrzynia`). Pozostaw puste, aby zliczać we wszystkich kategoriach.

Schemat w bazie (pole `condition`):
```json
{ "type": "item_add_count", "threshold": 10, "category": "namiot" }
```

Przykład:
- „Kolekcjoner 10 (Namioty)” — `threshold=10`, `category=namiot`.

#### 1b) Liczba edycji elementów — `item_edit_count`
- Przyznaje odznakę po osiągnięciu progu edycji elementów sprzętu wykonanych przez użytkownika.
- Zliczanie na podstawie `logs`: akcja `edit`, `target_type='sprzet'`, `user_id` edytującego.
- Gdy ustawiono `category`, akceptowana jest zgodność kategorii sprzed lub po edycji (jeśli element zmienił kategorię, edycja liczy się dla obu).
- Parametry:
  - Próg (`threshold`) — liczba całkowita ≥ 1 (wymagany).
  - Kategoria (`category`) — opcjonalna; gdy puste, zliczane są edycje wszystkich kategorii.

Schemat w bazie:
```json
{ "type": "item_edit_count", "threshold": 5, "category": "przedmiot" }
```

Przykłady:
- „Redaktor 5 (Przedmioty)” — `threshold=5`, `category=przedmiot`.
- „Redaktor 20 (Wszystkie)” — `threshold=20`, bez kategorii.

#### 2) Szybki zwrot — `speedy_return`
- Przyznaje odznakę, jeśli zwrot wypożyczenia nastąpił tego samego dnia co wypożyczenie.
- Nie wymaga dodatkowych parametrów w formularzu.

Schemat w bazie:
```json
{ "type": "speedy_return" }
```

#### 3) Pomocna dłoń — `help_resolve`
- Przyznaje odznakę, gdy użytkownik oznaczy jako „naprawioną” usterkę, której nie jest autorem (cudza usterka).
- Nie wymaga dodatkowych parametrów w formularzu.

Schemat w bazie:
```json
{ "type": "help_resolve" }
```

---

### Przykłady konfiguracji krok po kroku

1) Dodanie „Reporter 5/5”
- Wejdź: Admin → Osiągnięcia (definicje) → „Dodaj”.
- Nazwa: „Reporter 5/5”
- ID: `five_reports` (lub pozostaw puste, by wygenerować ze słów nazwy — jeśli wspierane)
- Opis: „Użytkownik dodał 5 zgłoszeń.”
- Ikona: 🥉
- Kolejność: 2
- Włączone: zaznaczone
- Warunek:
  - Typ: „Liczba zdarzeń (próg)”
  - Zdarzenie: „Zgłoszenie usterki” (`report_created`)
  - Próg: `5`
- Zapisz.

2) Dodanie „Aktywny Wypożyczający (10)”
- Nazwa: „Aktywny Wypożyczający”
- ID: `ten_borrows`
- Opis: „Użytkownik wypożyczył sprzęt 10 razy.”
- Ikona: 📦
- Kolejność: 3
- Włączone: zaznaczone
- Warunek:
  - Typ: „Liczba zdarzeń (próg)”
  - Zdarzenie: „Dodanie wypożyczenia” (`loan_created`)
  - Próg: `10`
- Zapisz.

3) Dodanie „Szybki Zwrot”
- Nazwa: „Szybki Zwrot”
- ID: `speedy_return`
- Opis: „Użytkownik zwrócił sprzęt tego samego dnia.”
- Ikona: ⚡
- Kolejność: 4
- Włączone: zaznaczone
- Warunek:
  - Typ: „Szybki zwrot (tego samego dnia)” — bez dodatkowych parametrów.
- Zapisz.

4) Dodanie „Pomocna Dłoń”
- Nazwa: „Pomocna Dłoń”
- ID: `helping_hand`
- Opis: „Użytkownik pomógł rozwiązać zgłoszenie innej osoby.”
- Ikona: 🤝
- Kolejność: 5
- Włączone: zaznaczone
- Warunek:
  - Typ: „Pomocna dłoń (naprawa cudzej usterki)” — bez dodatkowych parametrów.
- Zapisz.

5) Dodanie „Kolekcjoner 10 (Namioty)”
- Nazwa: „Kolekcjoner 10 (Namioty)”
- ID: `collector-10-namioty`
- Opis: „Użytkownik dodał 10 elementów kategorii Namioty.”
- Ikona: 🧰
- Kolejność: 6
- Włączone: zaznaczone
- Warunek:
  - Typ: „Liczba dodanych elementów (sprzęt)”
  - Próg: `10`
  - Kategoria: `namiot`
- Zapisz.

6) Dodanie „Redaktor 5 (Przedmioty)”
- Nazwa: „Redaktor 5 (Przedmioty)”
- ID: `editor-5-przedmioty`
- Opis: „Użytkownik wykonał 5 edycji w kategorii Przedmioty.”
- Ikona: ✏️
- Kolejność: 7
- Włączone: zaznaczone
- Warunek:
  - Typ: „Liczba edycji elementów (sprzęt)”
  - Próg: `5`
  - Kategoria: `przedmiot`
- Zapisz.

---

### Wzorce dla przyszłych osiągnięć

- Nowy próg dla istniejącego zdarzenia
  - Przykład: „Reporter 20/20” → `event_count`, `event=report_created`, `threshold=20`.

- Różne poziomy tej samej odznaki
  - Utwórz kilka definicji z rosnącym progiem i spójnymi ID, np. `borrower-10`, `borrower-25`, `borrower-50`.

- Wyłączanie i zmiana parametrów
  - Możesz tymczasowo „Włączyć/Wyłączyć” definicję.
  - Zmiana progu działa natychmiast dla kolejnych przydziałów (wcześniej przyznane odznaki pozostają). 

- Nowe typy zdarzeń
  - Aktualnie obsługiwane są: `report_created`, `loan_created`, `speedy_return`, `help_resolve`, oraz liczniki `item_add_count` i `item_edit_count` (oparte o dziennik aktywności).
  - Jeśli w przyszłości pojawią się nowe hooki/zdarzenia, będą mogły zostać dopisane jako kolejne opcje w formularzu i w logice przyznawania.

#### Propozycje nowych, różnorodnych odznak (do rozważenia)

Poniżej lista inspiracji, które rozszerzają wachlarz zachowań. Część z nich wymagałaby nowych typów warunków i dodatkowych danych w logach — są więc oznaczone jako „do implementacji”.

- Kustosz Kategorii (unikalne kategorie dodanych/edytowanych elementów)
  - Typ (nowy): `distinct_item_categories_count` z parametrem `threshold`.
  - Przykład: próg 3 → „Dotknął co najmniej 3 różnych kategorii sprzętu”.

- Łowca Różnorodności (unikalne wypożyczone przedmioty)
  - Typ (nowy): `unique_items_borrowed_count` z `threshold`.
  - Przykład: próg 5 → „Wypożyczył 5 różnych egzemplarzy sprzętu”.

- Weekendowy Wojownik (aktywność w weekendy)
  - Typ (nowy): `weekend_activity_count` z `event` (np. `report_created` lub akcje na sprzęcie) i `threshold`.
  - Przykład: 3 działania w soboty/niedziele.

- Nocny Mark (aktywność nocna)
  - Typ (nowy): `night_activity_count` z parametrami `hour_from`, `hour_to` i `threshold`.
  - Przykład: 5 działań między 22:00 a 05:00.

- Dokumentalista (raporty z załącznikami)
  - Typ (nowy): `reports_with_attachments_count` z `threshold`.
  - Przykład: 3 zgłoszenia z co najmniej jednym zdjęciem.

- Bezbłędny Miesiąc (brak opóźnień)
  - Typ (nowy): `zero_overdue_months` z `threshold` (liczba miesięcy bez spóźnień).

- Maratończyk (seria dni z rzędu)
  - Typ (nowy): `activity_streak_days` z `threshold` (kolejne dni z dowolną aktywnością).

- Wzorcowy Profil (uzupełnione dane konta)
  - Typ (nowy, binarny): `profile_completed` — sprawdza kompletność profilu (np. imię, nazwisko, telefon, e‑mail).

Jeśli zechcesz któreś z powyższych wdrożyć: dodamy nowy `type` w logice przyznawania, pola w formularzu oraz szablony listy/wyświetlania. Dobrą praktyką jest zacząć od typów, które można policzyć na istniejących logach (np. `distinct_item_categories_count`).

---

### Dobre praktyki i ograniczenia

- Unikalność ID
  - Upewnij się, że każde ID jest unikalne i stabilne. Po utworzeniu ID nie można zmienić.

- Spójność adresów e‑mail (wypożyczenia)
  - Zdarzenia wypożyczeń (`loan_created`, `speedy_return`) mapowane są do użytkownika po e‑mailu w polu `kontakt`. 
  - Jeśli e‑mail się nie zgadza lub jest pusty, odznaka nie zostanie przyznana.

- Włączona funkcja po stronie użytkownika
  - Dla automatycznego przyznawania użytkownik musi mieć włączoną funkcję: `features.achievements_enabled = True` (ustawiane przez Administratora).

- Idempotencja
  - System upewnia się, że ta sama odznaka nie zostanie zapisana użytkownikowi wielokrotnie.

- Osiągnięcia ukryte (secret)
  - Planując „sekretne” odznaki, pamiętaj, by opis nie zdradzał mechaniki warunku w innych miejscach UI.
  - Możesz w każdej chwili odznaczyć „Ukryte do zdobycia”, aby je ujawnić.

---

### Pasek postępu i widok użytkownika

- Na profilu użytkownika każda aktywna definicja odznaki wyświetla pasek postępu.
  - Dla warunków progowych (`event_count`) postęp = aktualna liczba zdarzeń użytkownika, cel = próg (`threshold`).
  - Dla warunków binarnych (`speedy_return`, `help_resolve`) postęp jest 0/1 (przed/po zdobyciu).
- Gdy odznaka ma status „Ukryte do zdobycia” i nie została zdobyta:
  - pokazywana jest kłódka i tytuł „Ukryte osiągnięcie”,
  - opis i wartości liczbowe (np. 0/10) są ukryte,
  - pasek postępu nie ujawnia szczegółów (bez liczb).

Przykład interpretacji paska:
- „Reporter 5/5” z `threshold=5` — użytkownik ma 3 zgłoszenia → progress 3/5 → ~60%.
- „Szybki Zwrot” — użytkownik jeszcze nie miał takiej sytuacji → progress 0/1.
- „Pomocna Dłoń” (ukryte) — do czasu zdobycia widoczna tylko kłódka i pusty pasek.

---

### Kiedy poszczególne pola formularza są edytowalne (warunkowanie)

Formularz automatycznie włącza/wyłącza niektóre pola w zależności od wybranego „Typu warunku”:

- Typ: `event_count`
  - Edytowalne: „Zdarzenie”, „Próg”.
  - Zablokowane: „Kategoria sprzętu”.

- Typ: `item_add_count` oraz `item_edit_count`
  - Edytowalne: „Próg”, „Kategoria sprzętu (opcjonalnie)”.
  - Zablokowane: „Zdarzenie”.

- Typy binarne: `speedy_return`, `help_resolve`
  - Zablokowane: „Zdarzenie”, „Próg”, „Kategoria sprzętu” (nie są wymagane dla tych warunków).

Uwaga: Backend dodatkowo weryfikuje te zasady — nawet jeśli ktoś spróbuje wysłać niewłaściwe dane, zostaną one odrzucone lub zignorowane zgodnie z logiką walidacji w panelu Admin.

### FAQ (najczęstsze pytania)

Q: Odznaka nie została przyznana — co sprawdzić?
- Czy użytkownik ma włączoną funkcję Osiągnięcia?
- Czy definicja odznaki jest „Włączona”?
- Czy wybrany typ warunku i jego parametry są poprawne (np. właściwe zdarzenie i próg)?
- Dla wypożyczeń: czy adres e‑mail w polu `kontakt` dokładnie odpowiada e‑mailowi konta użytkownika?

Q: Czy mogę edytować ID odznaki?
- Nie. ID jest stałe po utworzeniu. Edytuj nazwę, opis, ikonę, próg, kolejność lub status „Włączone”.

Q: Czy wyłączenie odznaki usuwa ją użytkownikom?
- Nie. Wyłączenie blokuje tylko dalsze automatyczne przyznawanie. Istniejące odznaki pozostają.

---

### Lista przykładowych osiągnięć (obecnie w systemie)

| ID            | Nazwa                  | Opis                                                     | Ikona | Warunek                                     | Włączone | Kolejność |
|---------------|-------------------------|----------------------------------------------------------|:-----:|---------------------------------------------|:--------:|:---------:|
| first_report  | Pierwsze Zgłoszenie     | Użytkownik dodał swoje pierwsze zgłoszenie usterki.      |  🆕   | event_count(report_created, threshold=1)    |   TAK    |     1     |
| five_reports  | Reporter 5/5            | Użytkownik dodał 5 zgłoszeń.                             |  🥉   | event_count(report_created, threshold=5)    |   TAK    |     2     |
| ten_borrows   | Aktywny Wypożyczający   | Użytkownik wypożyczył sprzęt 10 razy.                    |  📦   | event_count(loan_created, threshold=10)     |   TAK    |     3     |
| speedy_return | Szybki Zwrot            | Użytkownik zwrócił sprzęt tego samego dnia.              |  ⚡   | speedy_return                               |   TAK    |     4     |
| helping_hand  | Pomocna Dłoń            | Użytkownik pomógł rozwiązać zgłoszenie innej osoby.      |  🤝   | help_resolve                                |   TAK    |     5     |
| first_item_add| Pierwszy Sprzęt         | Użytkownik dodał pierwszy element sprzętu do ewidencji.  |  🧰   | item_add_count(threshold=1)                  |   TAK    |     6     |
| item_add_10   | Magazynier 10/10        | Użytkownik dodał 10 elementów sprzętu.                   |  📦   | item_add_count(threshold=10)                 |   TAK    |     7     |
| item_edit_10  | Konserwator 10/10       | Użytkownik wykonał 10 edycji elementów sprzętu.          |  ✏️   | item_edit_count(threshold=10)                |   TAK    |     8     |
| logs_50       | Aktywny Pomocnik        | Użytkownik wykonał 50 akcji w systemie (logi).           |  📋   | log_count(threshold=50)                      |   TAK    |     9     |
| ten_reports   | Reporter 10/10          | Użytkownik dodał 10 zgłoszeń usterek.                    |  🥈   | event_count(report_created, threshold=10)    |   TAK    |    10     |

---

### Jak testować konfigurację

- Upewnij się, że testowy użytkownik ma włączoną funkcję Osiągnięcia (Kwatermistrz lub Administrator: Admin → Użytkownicy → Osiągnięcia użytkownika → przełącznik „Włącz osiągnięcia”).
- Wykonaj odpowiednie akcje (dodaj zgłoszenia, dodaj/zwóć wypożyczenie, oznacz cudzą usterkę jako „naprawiona”).
- Sprawdź w profilu użytkownika sekcję „Osiągnięcia”.
