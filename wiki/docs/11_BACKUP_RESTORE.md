# Backup i Restore

Przewodnik po tworzeniu kopii zapasowych i przywracaniu danych.

## 💾 Strategia Backup

### Co należy backupować?

1. **Firestore Database** - Sprzęt, usterki, użytkownicy
2. **Google Cloud Storage** - Zdjęcia sprzętu i usterek
3. **Konfiguracja** - Pliki .env, Firebase config
4. **Kod aplikacji** - Repozytorium Git

---

## 🔄 Automatyczny Backup Firestore

### Konfiguracja w Google Cloud

```bash
# 1. Włącz Cloud Scheduler API
gcloud services enable cloudscheduler.googleapis.com

# 2. Utwórz bucket dla backupów
gsutil mb gs://twoj-projekt-backup

# 3. Utwórz scheduled job
gcloud firestore export gs://twoj-projekt-backup \
  --async \
  --project=twoj-projekt-id
```

### Harmonogram (przez Cloud Scheduler)

```yaml
# Codziennie o 2:00
schedule: "0 2 * * *"
target: firestore-export
bucket: gs://twoj-projekt-backup
```

---

## 📦 Ręczny Backup

### 1. Eksport Firestore

**Przez Console:**
1. Firestore → Import/Export
2. Export data → Select all
3. Choose bucket → Start export

**Przez gcloud:**
```bash
gcloud firestore export gs://twoj-bucket/backup-$(date +%Y%m%d)
```

### 2. Backup Cloud Storage

```bash
# Synchronizuj lokalnie
gsutil -m rsync -r gs://twoj-bucket ./local-backup

# Lub do innego bucketa
gsutil -m rsync -r gs://twoj-bucket gs://backup-bucket
```

### 3. Backup Konfiguracji

```bash
# Backup .env (zaszyfrowany!)
gpg -c .env -o env-backup.gpg

# Backup Firebase config
cp serviceAccountKey.json backup/
```

---

## 🔙 Restore (Przywracanie)

### Restore Firestore

```bash
# 1. Znajdź backup
gsutil ls gs://twoj-bucket/backup-*

# 2. Przywróć
gcloud firestore import gs://twoj-bucket/backup-20260101
```

**⚠️ UWAGA:**
- Restore nadpisuje istniejące dane
- Wykonaj przed restore'em nowy backup
- Testuj na środowisku testowym

### Restore Cloud Storage

```bash
# Z lokalnego backup
gsutil -m rsync -r ./local-backup gs://twoj-bucket

# Z backup bucket
gsutil -m rsync -r gs://backup-bucket gs://twoj-bucket
```

---

## 🔐 Bezpieczeństwo Backupów

**DO:**
- ✅ Szyfruj backupy (.env, credentials)
- ✅ Przechowuj w różnych lokalizacjach
- ✅ Testuj restore regularnie
- ✅ Ogranicz dostęp do backupów

**DON'T:**
- ❌ Nie commituj backupów do repo
- ❌ Nie przechowuj niezaszyfrowanych credentials
- ❌ Nie zapomnij o testowaniu restore

---

## 📋 Checklist Backup

### Codziennie (automatyczne):
- [ ] Firestore export
- [ ] Cloud Storage sync

### Co tydzień (manualne):
- [ ] Weryfikuj że backupy się tworzą
- [ ] Sprawdź dostępność backupów

### Co miesiąc (manualne):
- [ ] Test restore na środowisku testowym
- [ ] Dokumentuj procedurę
- [ ] Czyszczenie starych backupów (>90 dni)

---

**Ostatnia aktualizacja:** 2026-01-01  
**Wersja:** 1.0.0
