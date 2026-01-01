﻿# 📋 GitHub Wiki - Quick Start Checklist

## ✅ Przed Rozpoczęciem

- [x] Dokumentacja w `docs/` jest kompletna
- [x] `prepare_wiki.py` utworzony
- [x] `.github/workflows/update-wiki.yml` utworzony
- [x] `GITHUB_WIKI_GUIDE.md` utworzony
- [x] Lokalne testy zakończone sukcesem

## 🚀 Pierwsze Uruchomienie (15 minut)

### Krok 1: Konfiguracja GitHub (5 min)

```
□ Przejdź do Settings → Actions → General
□ Ustaw "Workflow permissions" na "Read and write permissions"
□ Kliknij Save
```

**URL:** https://github.com/200wdhigz/SzalasApp/settings/actions

### Krok 2: Sklonuj Wiki (2 min)

```bash
# W terminalu (poza projektem):
git clone https://github.com/200wdhigz/SzalasApp.wiki.git
```

**Rezultat:** Folder `SzalasApp.wiki/` utworzony

### Krok 3: Skopiuj Pliki (3 min)

**Windows PowerShell:**
```powershell
Copy-Item -Path C:\Users\uzyt\PycharmProjects\SzalasApp\wiki_export\* -Destination SzalasApp.wiki\ -Force
```

**Linux/Mac:**
```bash
cp ../SzalasApp/wiki_export/* SzalasApp.wiki/
```

**Sprawdź:**
```bash
cd SzalasApp.wiki
ls -l  # Powinno być 23 pliki .md
```

### Krok 4: Commituj i Push (5 min)

```bash
cd SzalasApp.wiki

# Sprawdź co zostało dodane
git status

# Dodaj wszystkie pliki
git add .

# Commituj
git commit -m "Initial documentation import

- 21 documentation files
- Complete project documentation  
- Auto-generated from docs/ folder
- Includes sidebar and footer
- Version: 1.1.1"

# Wypchnij
git push origin master
```

**Możliwe problemy:**
- Jeśli Wiki nie istnieje na GitHub, utworzy się automatycznie
- Przy pierwszym pushu może pojawić się pytanie o credentials

### Krok 5: Weryfikacja (WAŻNE!)

**Sprawdź na GitHub:**
```
https://github.com/200wdhigz/SzalasApp/wiki
```

**Co powinieneś zobaczyć:**
- ✅ Strona główna (Home) z pełnym spisem treści
- ✅ Pasek boczny (_Sidebar) z nawigacją
- ✅ Stopka (_Footer) na dole
- ✅ 21 stron dokumentacji
- ✅ Działające linki między stronami

**Testuj:**
- Kliknij kilka linków w sidebar
- Sprawdź czy linki między stronami działają
- Otwórz na telefonie (responsywność)

---

## 🔄 Test Automatyzacji (10 minut)

### Test 1: Ręczne Uruchomienie

```
□ Przejdź do: https://github.com/200wdhigz/SzalasApp/actions
□ Wybierz workflow "Update Wiki"
□ Kliknij "Run workflow"
□ Wybierz branch "main"
□ Kliknij "Run workflow"
□ Poczekaj ~1 minutę
□ Sprawdź czy zakończył się sukcesem (zielony checkmark)
```

### Test 2: Automatyczne Uruchomienie

```bash
# 1. Edytuj dowolny plik w docs/
echo "Test update" >> docs/19_FAQ.md

# 2. Commituj
git add docs/19_FAQ.md
git commit -m "test: Test auto-update Wiki"

# 3. Push
git push origin main

# 4. Sprawdź Actions
# https://github.com/200wdhigz/SzalasApp/actions
# Powinien pojawić się nowy workflow run

# 5. Po ~1 minucie sprawdź Wiki
# https://github.com/200wdhigz/SzalasApp/wiki
```

**Jeśli nie działa:**
- Sprawdź uprawnienia Actions (Krok 1)
- Sprawdź logi w Actions
- Zobacz `GITHUB_WIKI_GUIDE.md` sekcja Troubleshooting

---

## 📝 Codzienne Użycie

### Edycja Dokumentacji

```bash
# 1. Edytuj pliki w docs/
vim docs/19_FAQ.md

# 2. Commituj normalnie
git add docs/
git commit -m "docs: Update FAQ with new questions"

# 3. Push
git push origin main

# 4. Poczekaj ~1 minutę - Wiki zaktualizuje się automatycznie!
```

**Nie musisz:**
- ❌ Uruchamiać prepare_wiki.py ręcznie
- ❌ Pushować do Wiki ręcznie
- ❌ Martwić się o konwersję linków
- ❌ Pamiętać o sidebar/footer

**GitHub Actions zrobi to za Ciebie! 🎉**

---

## 🔧 Jeśli Coś Nie Działa

### Problem: GitHub Actions nie ma uprawnień

**Objawy:**
- Workflow kończy się błędem "Permission denied"
- Nie może pushować do Wiki

**Rozwiązanie:**
```
1. Settings → Actions → General
2. Workflow permissions → "Read and write permissions"
3. Save
4. Uruchom workflow ponownie
```

### Problem: Wiki nie aktualizuje się

**Sprawdź:**
1. Czy GitHub Actions się uruchomił? (zakładka Actions)
2. Czy zakończył się sukcesem? (zielony checkmark)
3. Czy zmiany były w docs/? (tylko docs/ triggeruje workflow)

**Debug:**
```bash
# Lokalnie przetestuj skrypt
python prepare_wiki.py

# Sprawdź czy generuje pliki
ls wiki_export/

# Sprawdź logi Actions na GitHub
```

### Problem: Linki nie działają

**Sprawdź:**
- Czy plik istnieje w FILE_MAPPING w prepare_wiki.py?
- Czy nazwa w linku pasuje do nazwy Wiki?
- Przykład: `[tekst](Quick-Start)` nie `[tekst](01_QUICK_START.md)`

**Napraw:**
1. Dodaj do FILE_MAPPING jeśli brakuje
2. Uruchom prepare_wiki.py ponownie
3. Commituj do Wiki

---

## 📊 Status Check

Po wykonaniu wszystkich kroków:

```
✅ Wiki istnieje na GitHub
✅ 23 pliki .md w Wiki
✅ Strona główna działa
✅ Sidebar jest widoczny
✅ Footer jest widoczny
✅ Linki między stronami działają
✅ GitHub Actions skonfigurowany
✅ Test ręczny przeszedł
✅ Test automatyczny przeszedł
✅ Dokumentacja jest aktualna
```

**Jeśli wszystko ✅ - GRATULACJE! 🎉**

Twoja dokumentacja jest teraz na GitHub Wiki i automatycznie się aktualizuje!

---

## 📚 Dodatkowe Materiały

- **Szczegóły:** `GITHUB_WIKI_GUIDE.md`
- **Podsumowanie:** `docs/WIKI_SETUP_SUMMARY.md`
- **Reorganizacja:** `docs/REORGANIZATION_SUMMARY.md`
- **Dependencies:** `docs/24_DEPENDENCIES.md`

---

## 🎯 Następne Akcje

1. **Udostępnij Wiki użytkownikom:**
   ```
   https://github.com/200wdhigz/SzalasApp/wiki
   ```

2. **Dodaj link do README:**
   - Już dodany! ✅

3. **Poinformuj zespół:**
   - Wiki jest automatycznie sync z docs/
   - Edytuj tylko w docs/, nie na Wiki
   - Zmiany pojawiają się w ~1 minutę

4. **Ciesz się automatyzacją! 🚀**

---

**Czas setup:** ~15 minut  
**Czas test:** ~10 minut  
**Łącznie:** ~25 minut

**ROI:** Nieograniczony! 🎉  
(Automatyczna dokumentacja na zawsze)

---

**Pytania?** Zobacz `GITHUB_WIKI_GUIDE.md`  
**Problemy?** Sprawdź GitHub Actions logs  
**Sukces?** 🎊 GRATULACJE! 🎊

