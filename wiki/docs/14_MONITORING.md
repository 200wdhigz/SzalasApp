# Monitoring i Logi
## 📊 Logi Aplikacji
```bash
# Uruchom z logami
python app.py
# Logi pokażą:
# - Requesty HTTP
# - Błędy Firebase
# - Operacje na bazie
```
## Monitorowanie Firebase
**Firebase Console:**
- Authentication → Users (aktywni użytkownicy)
- Firestore → Data (sprawdź dane)
- Storage → Files (użycie przestrzeni)
## Logi Produkcyjne
```bash
# Gunicorn z logami
gunicorn --access-logfile access.log --error-logfile error.log app:app
```
---
**Ostatnia aktualizacja:** 2026-01-01
