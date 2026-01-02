# 📚 Wiki & Dokumentacja

Ten folder zawiera całą dokumentację projektu SzalasApp oraz narzędzia do generowania GitHub Wiki.

---

## 📁 Struktura

```
wiki/
├── docs/               # Pliki źródłowe dokumentacji (Markdown)
│   ├── 00_INDEX.md
│   ├── 01_QUICK_START.md
│   ├── 02_ARCHITECTURE.md
│   ├── 03_OAUTH_SETUP.md
│   └── ... (25+ dokumentów)
│
├── export/            # Wygenerowane pliki wiki (generowane, git ignore)
│   └── (pliki .md dla GitHub Wiki)
│
├── prepare_wiki.py    # Skrypt generujący wiki
├── GITHUB_WIKI_GUIDE.md # Instrukcje publikacji
└── README.md          # Ten plik
```

---

## 🚀 Jak Używać

### 1. Edytuj Dokumentację

Wszystkie pliki źródłowe są w `docs/`:

```bash
cd wiki/docs
# Edytuj pliki .md
```

### 2. Generuj Wiki dla GitHub

```bash
cd wiki
python prepare_wiki.py
```

To utworzy pliki w `export/` gotowe do publikacji na GitHub Wiki.

### 3. Publikuj na GitHub Wiki

```bash
# Sklonuj wiki repo
git clone https://github.com/200wdhigz/SzalasApp.wiki.git

# Skopiuj wygenerowane pliki
cp export/* SzalasApp.wiki/

# Commit i push
cd SzalasApp.wiki
git add .
git commit -m "Update documentation"
git push origin master
```

Pełne instrukcje w: [GITHUB_WIKI_GUIDE.md](GITHUB_WIKI_GUIDE.md)

---

## 📝 Pliki Dokumentacji

### Główne Dokumenty

| Plik | Opis |
|------|------|
| `00_INDEX.md` | Indeks wszystkich dokumentów |
| `01_QUICK_START.md` | Szybki start |
| `02_ARCHITECTURE.md` | Architektura systemu |
| `03_OAUTH_SETUP.md` | Konfiguracja OAuth |
| `04_ACCOUNT_MANAGEMENT.md` | Zarządzanie kontami |
| `05_USER_SYNC.md` | Synchronizacja użytkowników |

### Funkcje

| Plik | Opis |
|------|------|
| `06_EQUIPMENT_MANAGEMENT.md` | Zarządzanie sprzętem |
| `07_MALFUNCTION_SYSTEM.md` | System usterek |
| `08_DATA_EXPORT.md` | Eksport danych |
| `09_ADMIN_PANEL.md` | Panel administratora |

### Bezpieczeństwo & Konfiguracja

| Plik | Opis |
|------|------|
| `10_SECURITY.md` | Bezpieczeństwo |
| `15_RECAPTCHA.md` | reCAPTCHA |
| `16_FIREBASE.md` | Firebase |
| `17_EMAIL_SMTP.md` | Email/SMTP |

### Deployment

| Plik | Opis |
|------|------|
| `12_INSTALLATION.md` | Instalacja |
| `13_DOCKER.md` | Docker |
| `11_BACKUP_RESTORE.md` | Backup i restore |
| `14_MONITORING.md` | Monitoring |

### Dla Deweloperów

| Plik | Opis |
|------|------|
| `21_DEVELOPMENT.md` | Development |
| `22_TESTING.md` | Testing |
| `23_CONTRIBUTING.md` | Contributing |
| `24_DEPENDENCIES.md` | Dependencies |

### Inne

| Plik | Opis |
|------|------|
| `18_CHANGELOG.md` | Changelog |
| `19_FAQ.md` | FAQ |
| `20_TROUBLESHOOTING.md` | Troubleshooting |
| `25_FEATURE_SUMMARY.md` | Feature summary |

---

## 🔧 Skrypt prepare_wiki.py

### Co robi?

1. Czyta pliki z `docs/`
2. Przetwarza linki i referencje
3. Dodaje nawigację
4. Generuje pliki gotowe dla GitHub Wiki do `export/`

### Użycie

```bash
cd wiki
python prepare_wiki.py
```

### Wymagania

- Python 3.8+
- Standardowa biblioteka (brak dodatkowych pakietów)

---

## 📖 Konwencje Pisania

### Nazewnictwo Plików

- Format: `XX_NAZWA.md`
- XX = numer (00-99)
- NAZWA = wielkie litery z underscore
- Przykład: `01_QUICK_START.md`

### Linki Wewnętrzne

```markdown
# W docs/ (przed generowaniem):
[Zobacz OAuth Setup](03_OAUTH_SETUP.md)

# W export/ (po wygenerowaniu):
[Zobacz OAuth Setup](OAuth-Setup)
```

### Obrazy

```markdown
# Relatywne do docs/
![Diagram](../assets/diagram.png)

# Po wygenerowaniu linki będą dostosowane
```

### Nagłówki

```markdown
# Główny Tytuł (H1) - jeden na dokument

## Sekcja (H2)

### Podsekcja (H3)

#### Szczegół (H4)
```

---

## 🔄 Workflow Aktualizacji

1. **Edytuj** pliki w `docs/`
2. **Generuj** wiki: `python prepare_wiki.py`
3. **Sprawdź** pliki w `export/`
4. **Publikuj** na GitHub Wiki

---

## ⚠️ Ważne Uwagi

- **NIE edytuj** plików w `export/` - są generowane automatycznie
- **Commituj** tylko pliki w `docs/`
- `export/` jest w `.gitignore`
- Zawsze uruchamiaj `prepare_wiki.py` z folderu `wiki/`

---

## 🆘 Problemy?

### "Module not found"

```bash
# Upewnij się że jesteś w wiki/
cd wiki
python prepare_wiki.py
```

### "File not found"

```bash
# Sprawdź strukturę
ls docs/  # Powinny być pliki .md
```

### "Git push rejected"

```bash
# Upewnij się że masz dostęp do wiki
# Wiki musi być włączone w ustawieniach repo
```

---

## 📞 Wsparcie

- [GITHUB_WIKI_GUIDE.md](GITHUB_WIKI_GUIDE.md) - Szczegółowe instrukcje
- [docs/20_TROUBLESHOOTING.md](docs/20_TROUBLESHOOTING.md) - Troubleshooting
- [docs/19_FAQ.md](docs/19_FAQ.md) - FAQ

---

**Struktura:** wiki/ jako centralne miejsce dla całej dokumentacji  
**Generator:** prepare_wiki.py dla GitHub Wiki  
**Status:** ✅ Gotowe do użycia

