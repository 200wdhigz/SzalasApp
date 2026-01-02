# Zarządzanie Zależnościami - Dependency Management

## 📦 Pliki Konfiguracyjne

Projekt SzalasApp używa **Poetry** jako głównego narzędzia do zarządzania zależnościami, ale zachowuje kompatybilność z pip poprzez `requirements.txt`.

### Struktura Plików

```
SzalasApp/
├── pyproject.toml      # Poetry - definicja projektu i zależności
├── poetry.lock         # Poetry - zamrożone wersje zależności
├── poetry.toml         # Poetry - konfiguracja lokalna
└── requirements.txt    # pip - eksport dla kompatybilności
```

---

## 🔧 Poetry (Preferowane)

### `pyproject.toml`
**Cel:** Główny plik konfiguracji projektu zgodny ze standardem PEP 518.

**Zawiera:**
- Metadata projektu (nazwa, wersja, autorzy)
- Zależności produkcyjne
- Zależności deweloperskie (dev-dependencies)
- Konfiguracja build system

**Przykład:**
```toml
[tool.poetry.dependencies]
python = "^3.12"
flask = "^3.1.2"
firebase-admin = "^7.1.0"
```

**Zarządzanie:**
```bash
# Dodaj zależność
poetry add package-name

# Dodaj zależność deweloperską
poetry add --group dev package-name

# Zaktualizuj zależności
poetry update

# Zainstaluj wszystkie zależności
poetry install
```

### `poetry.lock`
**Cel:** Zamrożone dokładne wersje wszystkich zależności i ich zależności.

**Dlaczego istnieje:**
- Zapewnia powtarzalność buildów
- Wszyscy developerzy mają identyczne wersje
- Eliminuje "works on my machine"

**⚠️ WAŻNE:**
- **NIE EDYTUJ RĘCZNIE** - generowany automatycznie
- **ZAWSZE COMMITUJ** do repozytorium
- Aktualizuj przez: `poetry update` lub `poetry lock`

### `poetry.toml`
**Cel:** Lokalna konfiguracja Poetry dla tego projektu.

**Zawiera:**
```toml
[virtualenvs]
in-project = true  # Tworzy .venv w folderze projektu
```

**Korzyści:**
- Virtual env w folderze projektu (`.venv/`)
- IDE łatwiej wykrywa środowisko
- Łatwe czyszczenie (usuń `.venv/`)

---

## 📄 pip (Kompatybilność)

### `requirements.txt`
**Cel:** Eksport zależności dla narzędzi używających pip.

**Kiedy używać:**
- Deployment na serwerze bez Poetry
- Docker build
- CI/CD pipelines z pip
- Zespoły preferujące pip

**Generowanie:**
```bash
# Z Poetry do requirements.txt
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

**Instalacja:**
```bash
# Z requirements.txt
pip install -r requirements.txt
```

---

## 🤔 Który Plik Jest Potrzebny?

### ✅ WSZYSTKIE są potrzebne

| Plik | Potrzebny? | Dlaczego? |
|------|------------|-----------|
| `pyproject.toml` | ✅ TAK | Definicja projektu, źródło prawdy dla zależności |
| `poetry.lock` | ✅ TAK | Zamrożone wersje, powtarzalność buildów |
| `poetry.toml` | ✅ TAK | Konfiguracja Poetry (venv w projekcie) |
| `requirements.txt` | ✅ TAK | Kompatybilność z pip, Docker, CI/CD |

### 🔄 Hierarchia Prawdy

```
pyproject.toml (źródło prawdy)
       ↓
poetry.lock (wygenerowany)
       ↓
requirements.txt (eksport)
```

---

## 📋 Workflow Deweloperski

### Nowy Developer Setup

**Opcja 1: Poetry (zalecane)**
```bash
# 1. Zainstaluj Poetry
curl -sSL https://install.python-poetry.org | python3 -

# 2. Zainstaluj zależności
poetry install

# 3. Aktywuj virtual env
poetry shell
```

**Opcja 2: pip**
```bash
# 1. Utwórz virtual env
python -m venv .venv

# 2. Aktywuj
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 3. Zainstaluj zależności
pip install -r requirements.txt
```

### Dodawanie Nowej Zależności

```bash
# 1. Dodaj przez Poetry
poetry add nazwa-pakietu

# 2. Eksportuj do requirements.txt
poetry export -f requirements.txt --output requirements.txt --without-hashes

# 3. Commituj oba pliki
git add pyproject.toml poetry.lock requirements.txt
git commit -m "Add nazwa-pakietu dependency"
```

### Aktualizacja Zależności

```bash
# 1. Zaktualizuj przez Poetry
poetry update

# 2. Eksportuj do requirements.txt
poetry export -f requirements.txt --output requirements.txt --without-hashes

# 3. Commituj zmiany
git add poetry.lock requirements.txt
git commit -m "Update dependencies"
```

---

## 🐳 Docker

W Dockerfile używamy `requirements.txt` dla prostoty:

```dockerfile
# Kopiuj requirements.txt
COPY requirements.txt .

# Instaluj zależności
RUN pip install --no-cache-dir -r requirements.txt
```

**Dlaczego nie Poetry w Docker?**
- Prostsze i szybsze buildy
- Mniejszy obraz (nie trzeba instalować Poetry)
- requirements.txt wystarczy dla produkcji

---

## 🔒 Bezpieczeństwo

### Sprawdzanie Podatności

**Poetry:**
```bash
poetry show --tree
poetry show --outdated
```

**pip:**
```bash
pip list --outdated
pip-audit  # Wymaga: pip install pip-audit
```

### Aktualizacje Bezpieczeństwa

```bash
# Zaktualizuj konkretny pakiet
poetry update nazwa-pakietu

# Zaktualizuj wszystkie
poetry update

# Eksportuj
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

---

## 📊 Porównanie

| Funkcja | Poetry | pip + requirements.txt |
|---------|--------|------------------------|
| Zarządzanie zależnościami | ✅ Zaawansowane | ⚠️ Podstawowe |
| Lock file | ✅ poetry.lock | ❌ Brak |
| Dev dependencies | ✅ Oddzielne grupy | ❌ Jeden plik |
| Budowanie pakietów | ✅ Built-in | ❌ setup.py |
| Virtual env | ✅ Automatyczne | ⚠️ Manualne |
| Prędkość instalacji | ⚠️ Wolniejsze | ✅ Szybsze |
| Kompatybilność | ⚠️ Nowsze | ✅ Uniwersalne |

---

## 🎯 Rekomendacje

### Dla Developerów
✅ Używaj **Poetry** do codziennej pracy:
- `poetry add` zamiast `pip install`
- `poetry shell` zamiast manual activation
- `poetry update` do aktualizacji

### Dla Deploymentu
✅ Używaj **requirements.txt**:
- Docker builds
- Cloud platforms (Heroku, Google App Engine)
- CI/CD pipelines

### Dla Maintainerów
✅ Utrzymuj **OBA** zsynchronizowane:
- Edytuj `pyproject.toml`
- Generuj `requirements.txt`
- Commituj oba

---

## 🚫 Czego NIE Robić

❌ **NIE edytuj `poetry.lock` ręcznie**
- Zawsze używaj `poetry lock` lub `poetry update`

❌ **NIE edytuj `requirements.txt` ręcznie** (jeśli używasz Poetry)
- Zawsze generuj: `poetry export`

❌ **NIE mixuj pip install z Poetry**
- Wybierz jedno narzędzie do zarządzania
- pip install nie aktualizuje poetry.lock

❌ **NIE ignoruj poetry.lock w .gitignore**
- Ten plik MUSI być w repozytorium

---

## 📚 Więcej Informacji

- [Poetry Documentation](https://python-poetry.org/docs/)
- [PEP 518 – pyproject.toml](https://www.python.org/dev/peps/pep-0518/)
- [pip Documentation](https://pip.pypa.io/en/stable/)

---

**Ostatnia aktualizacja:** 2026-01-01  
**Wersja:** 1.0.0

