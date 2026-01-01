# Skrypty Pomocnicze

Folder zawiera skrypty pomocnicze do zarządzania systemem SzalasApp.

## 📜 Dostępne Skrypty

### 1. `import_data.py`

**Cel:** Import danych sprzętu z pliku CSV/XLSX do Firestore.

**Użycie:**
```bash
python scripts/import_data.py
```

**Co robi:**
- Importuje dane sprzętu z pliku CSV lub XLSX
- Waliduje dane przed importem
- Tworzy nowe rekordy lub aktualizuje istniejące
- Wyświetla raport importu

**Wymagania:**
- Plik `.env` z konfiguracją Firebase
- Plik danych w formacie CSV/XLSX

---

### 2. `set_admin_claim.py`

**Cel:** Nadawanie uprawnień administratora użytkownikom Firebase.

**Użycie:**
```bash
python scripts/set_admin_claim.py
```

**Co robi:**
- Ustawia custom claim `admin: true` dla użytkownika
- Pozwala użytkownikowi na dostęp do panelu administratora
- Wymaga interakcji (podanie UID użytkownika)

**Wymagania:**
- Plik `.env` z konfiguracją Firebase
- Firebase Admin SDK credentials
- UID użytkownika do nadania uprawnień

**Przykład:**
```bash
python scripts/set_admin_claim.py
# Wprowadź UID użytkownika: abc123xyz456
# ✅ Użytkownik abc123xyz456 otrzymał uprawnienia administratora
```

---

### 3. `upload_photos.py`

**Cel:** Upload zdjęć sprzętu do Google Cloud Storage.

**Użycie:**
```bash
python scripts/upload_photos.py
```

**Co robi:**
- Uploaduje zdjęcia do Google Cloud Storage
- Organizuje zdjęcia w foldery według ID sprzętu
- Zwraca URL do uploadowanych zdjęć
- Opcjonalnie aktualizuje rekordy w Firestore

**Wymagania:**
- Plik `.env` z konfiguracją Firebase
- Google Cloud Storage bucket skonfigurowany
- Zdjęcia do uploadu

**Struktura folderów:**
```
bucket/
  sprzet/
    namiot_01/
      photo1.jpg
      photo2.jpg
  usterki/
    usterka_id_123/
      photo1.jpg
```

---

## 🔧 Konfiguracja

Wszystkie skrypty wymagają pliku `.env` w głównym folderze projektu:

```bash
# Firebase Configuration
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_API_KEY=your-api-key
SECRET_KEY=your-secret-key

# Google Cloud Storage
GCS_BUCKET_NAME=your-bucket-name
```

---

## 🚀 Szybki Start

### Setup środowiska:

```bash
# 1. Aktywuj wirtualne środowisko
# Windows:
.venv\Scripts\activate

# Linux/Mac:
source .venv/bin/activate

# 2. Zainstaluj zależności
pip install -r requirements.txt

# 3. Skonfiguruj .env
cp .env.example .env
# Edytuj .env i uzupełnij dane
```

### Uruchomienie skryptu:

```bash
# Z głównego folderu projektu:
python scripts/nazwa_skryptu.py
```

---

## 📚 Dokumentacja

Szczegółowa dokumentacja dostępna w:
- [docs/06_EQUIPMENT_MANAGEMENT.md](../docs/06_EQUIPMENT_MANAGEMENT.md) - Import sprzętu
- [docs/09_ADMIN_PANEL.md](../docs/09_ADMIN_PANEL.md) - Zarządzanie użytkownikami
- [docs/README.md](../docs/README.md) - Pełna dokumentacja

---

## ⚠️ Uwagi

- **Backup:** Zawsze rób backup danych przed masowym importem
- **Testowanie:** Przetestuj skrypty na testowym środowisku
- **Uprawnienia:** Niektóre skrypty wymagają uprawnień administratora
- **Logs:** Sprawdzaj logi w przypadku błędów

---

## 🐛 Troubleshooting

### Błąd: "Firebase credentials not found"
**Rozwiązanie:** Sprawdź plik `.env` i upewnij się, że `FIREBASE_PROJECT_ID` jest ustawione.

### Błąd: "Permission denied"
**Rozwiązanie:** Sprawdź uprawnienia Firebase Admin SDK i Google Cloud Storage.

### Błąd: "Module not found"
**Rozwiązanie:** Zainstaluj zależności: `pip install -r requirements.txt`

---

**Ostatnia aktualizacja:** 2026-01-01  
**Wersja:** 1.0.0

