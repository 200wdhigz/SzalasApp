# Przewodnik Synchronizacji Użytkowników

## Problem

Kiedy usuwasz użytkownika bezpośrednio w [Firebase Console](https://console.firebase.google.com/), lista użytkowników w aplikacji SzalasApp nie aktualizuje się automatycznie. Dzieje się tak, ponieważ aplikacja przechowuje dane użytkowników w dwóch miejscach:

1. **Firebase Authentication** - system uwierzytelniania (logowanie)
2. **Firestore Database** - baza danych użytkowników (dodatkowe informacje)

## Rozwiązanie 1: Synchronizacja (Zalecane)

### Kiedy używać?
- Gdy usunąłeś użytkownika(ów) w Firebase Console
- Gdy lista w aplikacji jest nieaktualna
- Gdy chcesz upewnić się, że obie bazy są zsynchronizowane

### Jak zsynchronizować?

1. Zaloguj się jako administrator
2. Przejdź do **Zarządzanie Użytkownikami**
3. Kliknij przycisk **"🔄 Synchronizuj"** w prawym górnym rogu
4. System automatycznie:
   - ✅ Usunie z Firestore użytkowników, którzy nie istnieją w Firebase Auth
   - ✅ Doda do Firestore użytkowników z Firebase Auth, których brakuje
5. Zobaczysz komunikat z liczbą usuniętych/dodanych użytkowników

### Przykład

```
✅ Synchronizacja zakończona: usunięto 3, dodano 0 użytkowników.
```

lub

```
ℹ️ Lista użytkowników jest już zsynchronizowana.
```

---

## Rozwiązanie 2: Usuwanie z Aplikacji (Najlepsze)

### Kiedy używać?
- Gdy chcesz usunąć użytkownika
- Gdy chcesz mieć pewność, że użytkownik jest usunięty z obu baz jednocześnie

### Jak usunąć użytkownika?

1. Zaloguj się jako administrator
2. Przejdź do **Zarządzanie Użytkownikami**
3. Znajdź użytkownika na liście
4. Kliknij przycisk **🗑️ (kosz)** po prawej stronie
5. Potwierdź usunięcie w oknie dialogowym
6. Użytkownik zostanie usunięty z:
   - ✅ Firebase Authentication
   - ✅ Firestore Database

**Korzyści:**
- Jedna operacja zamiast dwóch
- Brak potrzeby synchronizacji
- Natychmiastowe usunięcie z obu źródeł

---

## Porównanie Metod

| Metoda | Gdzie usuwasz | Wymaga synchronizacji | Usuwa z obydwu baz |
|--------|---------------|----------------------|-------------------|
| Firebase Console → Synchronizacja | Firebase Console | ✅ Tak | ✅ Tak (po synchronizacji) |
| Usuwanie z aplikacji | Panel aplikacji | ❌ Nie | ✅ Tak (natychmiast) |

---

## Często Zadawane Pytania

### Q: Co się stanie, jeśli nie zsynchronizuję po usunięciu w Firebase Console?

**A:** Użytkownik nadal będzie widoczny na liście w aplikacji, ale:
- Nie będzie mógł się zalogować (nie istnieje w Firebase Auth)
- Jego dane będą "martwe" w Firestore
- Może powodować zamieszanie

### Q: Czy synchronizacja usuwa dane użytkownika nieodwracalnie?

**A:** Tak. Synchronizacja usuwa dokumenty użytkownika z Firestore, ale:
- Dane użytkownika (sprzęt, usterki) pozostają nienaruszone
- Usuwane są tylko wpisy w kolekcji `users`
- Nie można ich odzyskać (chyba że masz backup)

### Q: Czy mogę cofnąć synchronizację?

**A:** Nie. Operacja synchronizacji jest nieodwracalna. Jeśli przypadkowo usuniesz użytkownika:
1. Możesz utworzyć go ponownie w Firebase Console
2. Po synchronizacji pojawi się w Firestore z domyślnymi danymi
3. Stare powiązania (OAuth, custom claims) zostaną utracone

### Q: Jak często powinienem synchronizować?

**A:** 
- **Automatycznie:** Nie musisz, jeśli usuwasz użytkowników tylko z aplikacji
- **Ręcznie:** Tylko gdy usuwasz użytkowników w Firebase Console
- **Prewencyjnie:** Możesz synchronizować raz w miesiącu dla pewności

### Q: Co się stanie z danymi użytkownika (sprzęt, usterki) po usunięciu?

**A:** Dane pozostają w systemie, ale:
- Pole `sprzet.created_by` lub `usterka.zgloszono_przez` może wskazywać nieistniejącego użytkownika
- Rozważ utworzenie użytkownika "System" lub "Usunięty użytkownik" przed usunięciem
- Lub zmień właściciela danych przed usunięciem użytkownika

---

## Najlepsze Praktyki

### ✅ DO:

1. **Zawsze używaj przycisku usuwania w aplikacji** zamiast Firebase Console
2. **Synchronizuj natychmiast** jeśli usunąłeś kogoś w Firebase Console
3. **Sprawdź dane użytkownika** przed usunięciem (czy ma przypisany sprzęt/usterki?)
4. **Informuj użytkowników** przed usunięciem ich konta
5. **Rób backup** przed masowym usuwaniem użytkowników

### ❌ DON'T:

1. ❌ Nie usuwaj użytkowników bezpośrednio z Firestore (tylko przez Firebase Auth)
2. ❌ Nie ignoruj komunikatów o synchronizacji
3. ❌ Nie usuwaj administratorów bez zastanowienia (możesz stracić dostęp)
4. ❌ Nie usuwaj własnego konta (wylogujesz się i nie wrócisz)

---

## Rozwiązywanie Problemów

### Problem: Przycisk "Synchronizuj" nie działa

**Rozwiązanie:**
1. Sprawdź czy jesteś zalogowany jako administrator
2. Sprawdź połączenie z internetem
3. Sprawdź logi aplikacji (konsola przeglądarki F12)
4. Sprawdź uprawnienia Firebase (czy admin ma dostęp do Firebase Auth API)

### Problem: Użytkownik nadal widoczny po synchronizacji

**Możliwe przyczyny:**
1. Użytkownik istnieje w Firebase Auth (nie został tam usunięty)
2. Błąd podczas synchronizacji (sprawdź komunikaty)
3. Cache przeglądarki (odśwież stronę Ctrl+F5)

**Rozwiązanie:**
1. Sprawdź Firebase Console czy użytkownik tam istnieje
2. Jeśli tak, usuń go tam i zsynchronizuj ponownie
3. Jeśli nie, użyj przycisku usuwania w aplikacji

### Problem: Synchronizacja usuwa zbyt wiele użytkowników

**To znaczy, że:**
- W Firebase Auth jest mniej użytkowników niż w Firestore
- Prawdopodobnie ktoś usunął użytkowników w Firebase Console

**Rozwiązanie:**
- To jest poprawne zachowanie
- Synchronizacja czyści "martwe" wpisy w Firestore
- Jeśli to błąd, przywróć użytkowników z backupu

---

## Automatyczna Synchronizacja (Przyszłość)

W przyszłych wersjach planujemy dodać:

- 🔄 **Automatyczną synchronizację** przy każdym logowaniu admina
- 📧 **Powiadomienia email** gdy wykryto rozbieżności
- 📊 **Dashboard** ze statystykami synchronizacji
- 🔍 **Logi audytu** kto i kiedy synchronizował
- ⏰ **Harmonogram** automatycznej synchronizacji (np. codziennie o 2:00)

---

## Podsumowanie

**Zalecana metoda usuwania użytkowników:**

```
1. Panel aplikacji → Zarządzanie Użytkownikami
2. Znajdź użytkownika
3. Kliknij 🗑️ (kosz)
4. Potwierdź
5. Gotowe! ✅
```

**Jeśli już usunąłeś w Firebase Console:**

```
1. Panel aplikacji → Zarządzanie Użytkownikami
2. Kliknij "🔄 Synchronizuj"
3. Poczekaj na potwierdzenie
4. Gotowe! ✅
```

---

**Pytania?** Sprawdź README.md lub skontaktuj się z zespołem rozwoju.

**Ostatnia aktualizacja:** 2026-01-01  
**Wersja:** 1.1.0

