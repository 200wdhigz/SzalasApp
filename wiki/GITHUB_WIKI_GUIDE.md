# GitHub Wiki - Przewodnik Użytkowania

## 🎯 Cel

Ten dokument opisuje jak zarządzać dokumentacją projektu SzalasApp w GitHub Wiki.

## 📚 Struktura

### Pliki Specjalne

GitHub Wiki rozpoznaje specjalne pliki:

1. **`Home.md`** - Strona główna Wiki (zawsze pierwsza)
2. **`_Sidebar.md`** - Pasek boczny z nawigacją (widoczny na każdej stronie)
3. **`_Footer.md`** - Stopka (widoczna na każdej stronie)

### Nazewnictwo

- **GitHub Wiki** używa nazw plików jako tytuły stron
- Spacje są zastępowane myślnikami: `Quick Start` → `Quick-Start.md`
- Wielkość liter ma znaczenie
- Linki wewnętrzne: `[tekst](Nazwa-Strony)` (bez `.md`)

---

## 🚀 Setup - Pierwsze Uruchomienie

### Krok 1: Przygotowanie Plików

```bash
# Uruchom skrypt konwersji
python prepare_wiki.py
```

To utworzy folder `wiki_export/` z przygotowanymi plikami.

### Krok 2: Sklonuj Wiki

```bash
# Sklonuj wiki repozytorium (zastąp URL swoim)
git clone https://github.com/200wdhigz/SzalasApp.wiki.git
```

### Krok 3: Skopiuj Pliki

**Windows (PowerShell):**
```powershell
Copy-Item -Path wiki_export\* -Destination SzalasApp.wiki\ -Force
```

**Linux/Mac:**
```bash
cp wiki_export/* SzalasApp.wiki/
```

### Krok 4: Commituj i Wypchnij

```bash
cd SzalasApp.wiki

# Sprawdź zmiany
git status

# Dodaj wszystkie pliki
git add .

# Commituj
git commit -m "Initial documentation import

- 20 documentation files
- Complete project documentation
- Auto-generated from docs/ folder"

# Wypchnij do GitHub
git push origin master
```

### Krok 5: Weryfikacja

Odwiedź:
```
https://github.com/200wdhigz/SzalasApp/wiki
```

Powinieneś zobaczyć:
- ✅ Stronę główną (Home)
- ✅ Pasek boczny z nawigacją
- ✅ Wszystkie strony dostępne
- ✅ Działające linki

---

## 🔄 Aktualizacja Dokumentacji

### Metoda 1: Automatyczna (GitHub Actions)

**Została skonfigurowana!** 🎉

Po każdym pushu do `main` z zmianami w `docs/`:
1. GitHub Actions uruchamia workflow
2. Skrypt `prepare_wiki.py` konwertuje pliki
3. Zmiany są automatycznie pushowane do Wiki

**Nic nie musisz robić ręcznie!**

### Metoda 2: Ręczna

Jeśli chcesz zaktualizować ręcznie:

```bash
# 1. Zaktualizuj pliki w docs/
# (edytuj pliki w projekcie)

# 2. Przygotuj pliki dla Wiki
python prepare_wiki.py

# 3. Przejdź do folderu wiki
cd SzalasApp.wiki

# 4. Pobierz najnowsze zmiany
git pull

# 5. Skopiuj zaktualizowane pliki
# Windows:
Copy-Item -Path ..\wiki_export\* -Destination . -Force

# Linux/Mac:
cp ../wiki_export/* .

# 6. Sprawdź zmiany
git status
git diff

# 7. Commituj i wypchnij
git add .
git commit -m "Update documentation"
git push origin master
```

---

## 🎨 Dostosowywanie

### Sidebar (Pasek Boczny)

Edytuj w `prepare_wiki.py` funkcję `create_sidebar()`:

```python
def create_sidebar(wiki_dir: Path) -> None:
    sidebar_content = """## 📚 SzalasApp Wiki
    
### 🚀 Twoja Sekcja
* [Twoja Strona](Twoja-Strona)
* [Inna Strona](Inna-Strona)
"""
```

### Footer (Stopka)

Edytuj w `prepare_wiki.py` funkcję `create_footer()`:

```python
def create_footer(wiki_dir: Path) -> None:
    footer_content = """---
**Twoja stopka** | [Link](url)
"""
```

### Mapowanie Plików

Dodaj nowe pliki do `FILE_MAPPING` w `prepare_wiki.py`:

```python
FILE_MAPPING = {
    '00_INDEX.md': 'Home.md',
    'TWOJ_PLIK.md': 'Nazwa-W-Wiki.md',  # ← Dodaj tutaj
    # ...
}
```

---

## 🔧 Rozwiązywanie Problemów

### Problem: Linki nie działają

**Rozwiązanie:**
1. Sprawdź `FILE_MAPPING` w `prepare_wiki.py`
2. Upewnij się że wszystkie pliki są w mapowaniu
3. Uruchom ponownie `prepare_wiki.py`

### Problem: Zmiany nie pojawiają się na Wiki

**Rozwiązanie:**
1. Sprawdź czy commitowałeś i pushowałeś do `SzalasApp.wiki`
2. Odśwież stronę (Ctrl+F5)
3. Sprawdź GitHub Actions (zakładka Actions w repo)

### Problem: GitHub Actions nie działa

**Rozwiązanie:**
1. Sprawdź logi w zakładce Actions
2. Upewnij się że workflow jest włączony
3. Sprawdź uprawnienia: Settings → Actions → General
   - Workflow permissions: Read and write permissions

### Problem: Emoji nie wyświetlają się

**Rozwiązanie:**
GitHub Wiki wspiera emoji, ale niektóre mogą się nie wyświetlać.
Użyj standardowych emoji: 📚 🚀 ✅ ❌ ⚠️ 💡

---

## 📋 Workflow Deweloperski

### Typowy Dzień Pracy:

```
1. Edytujesz dokumentację w docs/
2. Commituj zmiany do main
3. Pushujesz do GitHub
4. GitHub Actions automatycznie aktualizuje Wiki
5. Po ~1 minucie sprawdzasz Wiki
```

### Tylko Lokalne Testowanie:

```bash
# 1. Edytuj docs/
# 2. Testuj lokalnie
python prepare_wiki.py

# 3. Sprawdź wygenerowane pliki
ls wiki_export/

# 4. Jeśli OK, commituj docs/
git add docs/
git commit -m "Update docs"
git push
```

---

## 📊 Statystyki

### Pliki w Wiki

- **20 plików dokumentacji**
- **1 Home (strona główna)**
- **1 Sidebar (nawigacja)**
- **1 Footer (stopka)**
- **Łącznie: 23 pliki**

### Automatyzacja

- ✅ Auto-update przy pushu do `main`
- ✅ Auto-konwersja linków
- ✅ Auto-generowanie sidebar/footer
- ✅ Ręczne uruchomienie (workflow_dispatch)

---

## 🎓 Best Practices

### DO:

- ✅ Edytuj dokumentację w `docs/` (nie bezpośrednio w Wiki)
- ✅ Używaj GitHub Actions do aktualizacji
- ✅ Testuj lokalnie przed pushem
- ✅ Commituj znaczące zmiany
- ✅ Używaj jasnych komunikatów commit

### DON'T:

- ❌ Nie edytuj bezpośrednio w Web UI Wiki (zmiany zostaną nadpisane)
- ❌ Nie commituj do Wiki ręcznie (użyj Actions)
- ❌ Nie usuwaj `_Sidebar.md` i `_Footer.md`
- ❌ Nie zmieniaj struktury bez aktualizacji skryptu

---

## 🔗 Linki

- **Dokumentacja GitHub Wiki:** https://docs.github.com/en/communities/documenting-your-project-with-wikis
- **Markdown Guide:** https://guides.github.com/features/mastering-markdown/
- **GitHub Actions:** https://docs.github.com/en/actions

---

## 📞 Wsparcie

Jeśli masz problemy:

1. Sprawdź logi GitHub Actions
2. Uruchom `prepare_wiki.py` lokalnie
3. Sprawdź czy wszystkie pliki w `docs/` są w `FILE_MAPPING`
4. Zgłoś issue na GitHub

---

**Ostatnia aktualizacja:** 2026-01-01  
**Wersja:** 1.0.0  
**Dokumentacja:** [docs/](../docs/)

