# Rozwój Aplikacji
## 🛠️ Setup Deweloperskie
### 1. Clone i Setup
```bash
git clone https://github.com/200wdhigz/SzalasApp.git
cd SzalasApp
poetry install
poetry shell
```
### 2. Pre-commit Hooks (opcjonalnie)
```bash
pip install pre-commit
pre-commit install
```
## Struktura Kodu
```
src/
├── auth.py         # Uwierzytelnianie
├── oauth.py        # OAuth flows
├── admin.py        # Panel admina
├── views.py        # Główne views
├── db_*.py         # Database operations
└── *.py            # Utilities
```
## Coding Standards
- **PEP 8** - Style guide
- **Type hints** - Gdzie możliwe
- **Docstrings** - Dla funkcji publicznych
- **Comments** - Po polsku OK
## Testing
```bash
# Uruchom testy (gdy będą)
pytest
# Coverage
pytest --cov=src
```
---
**Ostatnia aktualizacja:** 2026-01-01
