# 📚 Indeks dokumentacji wdrożenia z Nginx Proxy Manager

## Dla kogo jest ta dokumentacja?

✅ **Masz już Nginx Proxy Manager** zainstalowany w osobnym docker-compose  
✅ Chcesz dodać **SzalasApp** jako kolejną aplikację  
✅ Potrzebujesz **HTTPS** (SSL) dla domeny `szalasapp.kawak.uk`

## 🚀 Szybki start (wybierz swój scenariusz)

### Scenariusz 1: "Chcę szybko wdrożyć, pokaż mi co robić"
👉 **Przejdź do:** [DEPLOYMENT_NPM_QUICKSTART.md](../DEPLOYMENT_NPM_QUICKSTART.md)
- Krok po kroku instrukcja
- Wszystkie komendy gotowe do skopiowania
- Szacowany czas: 30-45 minut

### Scenariusz 2: "Chcę mieć checklistę, żeby nic nie pominąć"
👉 **Przejdź do:** [DEPLOYMENT_NPM_CHECKLIST.md](../DEPLOYMENT_NPM_CHECKLIST.md)
- 20 sekcji z checkboxami
- Sprawdzisz czy wszystko jest gotowe
- Używaj równolegle z Quickstart

### Scenariusz 3: "Potrzebuję szczegółowej dokumentacji"
👉 **Przejdź do:** [26_DEPLOYMENT_PRODUCTION.md](26_DEPLOYMENT_PRODUCTION.md) - Sekcja "Wariant A"
- Pełna dokumentacja techniczna
- Wyjaśnienia jak wszystko działa
- Troubleshooting i zaawansowane opcje

### Scenariusz 4: "Już wdrożyłem, potrzebuję ściągawki"
👉 **Przejdź do:** [NPM_CHEATSHEET.md](../NPM_CHEATSHEET.md)
- Szybkie komendy
- Troubleshooting
- Monitorowanie i zarządzanie

## 📁 Struktura plików

```
SzalasApp/
├── DEPLOYMENT_NPM_QUICKSTART.md    ⭐ START TUTAJ
├── DEPLOYMENT_NPM_CHECKLIST.md     ✅ Lista kontrolna
├── NPM_CHEATSHEET.md               ⚡ Ściągawka
├── docker-compose.npm.yml          🐳 Gotowy Docker Compose
├── .env.npm.example                🔧 Przykładowy .env
├── nginx-proxy-manager-example.yml 📝 Przykład konfiguracji NPM
└── wiki/docs/
    └── 26_DEPLOYMENT_PRODUCTION.md 📚 Pełna dokumentacja
```

## 🎯 Kolejność czytania (zalecana)

### Przed wdrożeniem
1. **[DEPLOYMENT_NPM_QUICKSTART.md](../DEPLOYMENT_NPM_QUICKSTART.md)** - przeczytaj cały plik (10 min)
2. **[DEPLOYMENT_NPM_CHECKLIST.md](../DEPLOYMENT_NPM_CHECKLIST.md)** - sprawdź sekcje 1-6 "Przed wdrożeniem" (15 min)
3. **[.env.npm.example](../.env.npm.example)** - przygotuj swój plik .env (20 min)

### Podczas wdrożenia
4. **[DEPLOYMENT_NPM_QUICKSTART.md](../DEPLOYMENT_NPM_QUICKSTART.md)** - wykonaj kroki 1-10 (30-45 min)
5. **[DEPLOYMENT_NPM_CHECKLIST.md](../DEPLOYMENT_NPM_CHECKLIST.md)** - zaznaczaj wykonane kroki

### Po wdrożeniu
6. **[NPM_CHEATSHEET.md](../NPM_CHEATSHEET.md)** - zapisz w zakładkach do późniejszego użycia
7. **[26_DEPLOYMENT_PRODUCTION.md](26_DEPLOYMENT_PRODUCTION.md)** - przeczytaj sekcje "Monitorowanie" i "Backup"

## 🔧 Narzędzia pomocnicze

### Pliki konfiguracyjne

**docker-compose.npm.yml**
```bash
# Gotowy do użycia plik Docker Compose
docker compose -f docker-compose.npm.yml up -d --build
```

**.env.npm.example**
```bash
# Skopiuj i wypełnij
cp .env.npm.example .env
nano .env
```

**nginx-proxy-manager-example.yml**
```bash
# Przykład jak dodać NPM do wspólnej sieci
# Dostosuj do swojej konfiguracji NPM
```

## 🆘 Troubleshooting

### Problem: 502 Bad Gateway
👉 **[NPM_CHEATSHEET.md](../NPM_CHEATSHEET.md)** - Sekcja "502 Bad Gateway"  
👉 **[DEPLOYMENT_NPM_QUICKSTART.md](../DEPLOYMENT_NPM_QUICKSTART.md)** - Sekcja "Troubleshooting"

### Problem: SSL nie działa
👉 **[NPM_CHEATSHEET.md](../NPM_CHEATSHEET.md)** - Sekcja "SSL Certificate Error"  
👉 **[26_DEPLOYMENT_PRODUCTION.md](26_DEPLOYMENT_PRODUCTION.md)** - Sekcja "Troubleshooting dla NPM"

### Problem: OAuth redirect error
👉 **[NPM_CHEATSHEET.md](../NPM_CHEATSHEET.md)** - Sekcja "OAuth Redirect Error"  
👉 **[DEPLOYMENT_NPM_QUICKSTART.md](../DEPLOYMENT_NPM_QUICKSTART.md)** - Sekcja "Weryfikacja"

### Ogólne problemy
👉 **[wiki/docs/20_TROUBLESHOOTING.md](20_TROUBLESHOOTING.md)** - Kompletny przewodnik troubleshootingu

## 📊 Porównanie dokumentów

| Dokument | Długość | Cel | Dla kogo |
|----------|---------|-----|----------|
| **QUICKSTART** | 15 min | Szybkie wdrożenie | Wszyscy |
| **CHECKLIST** | 5 min | Weryfikacja | Wszyscy |
| **CHEATSHEET** | Referencyjna | Szybkie komendy | Po wdrożeniu |
| **PRODUCTION** | 45 min | Szczegółowa wiedza | Zaawansowani |
| **.env.example** | 10 min | Konfiguracja | Przed wdrożeniem |

## 🎓 Dodatkowe zasoby

### Oficjalna dokumentacja
- **Nginx Proxy Manager**: https://nginxproxymanager.com/
- **Docker**: https://docs.docker.com/
- **Let's Encrypt**: https://letsencrypt.org/docs/

### SzalasApp dokumentacja
- **[00_INDEX.md](00_INDEX.md)** - Pełny indeks dokumentacji
- **[03_OAUTH_SETUP.md](03_OAUTH_SETUP.md)** - Konfiguracja Google OAuth
- **[16_FIREBASE.md](16_FIREBASE.md)** - Konfiguracja Firebase
- **[13_DOCKER.md](13_DOCKER.md)** - Praca z Dockerem

## ✅ Quick Checklist (ultra krótka)

Przed rozpoczęciem upewnij się że masz:
- [ ] Serwer VPS z Ubuntu (min. 2GB RAM)
- [ ] Docker i Docker Compose zainstalowane
- [ ] Nginx Proxy Manager już działa
- [ ] Domena `szalasapp.kawak.uk` wskazuje na serwer
- [ ] Service Account JSON z Google Cloud
- [ ] Google OAuth credentials
- [ ] reCAPTCHA keys

## 🚦 Status wdrożenia

Gdzie jesteś w procesie?

### 🔴 Nie zacząłem
👉 Zacznij od [DEPLOYMENT_NPM_QUICKSTART.md](../DEPLOYMENT_NPM_QUICKSTART.md)

### 🟡 W trakcie wdrożenia
👉 Użyj [DEPLOYMENT_NPM_CHECKLIST.md](../DEPLOYMENT_NPM_CHECKLIST.md)  
👉 W razie problemów: [NPM_CHEATSHEET.md](../NPM_CHEATSHEET.md) - Troubleshooting

### 🟢 Wdrożone, działa
👉 Zapisz [NPM_CHEATSHEET.md](../NPM_CHEATSHEET.md) w zakładkach  
👉 Skonfiguruj monitoring (sekcja w 26_DEPLOYMENT_PRODUCTION.md)  
👉 Skonfiguruj backup (sekcja w 11_BACKUP_RESTORE.md)

## 💡 Wskazówki

**Dla początkujących:**
1. Czytaj dokumenty po kolei (Quickstart → Checklist → Cheatsheet)
2. Nie pomiń żadnego kroku
3. Testuj każdy krok zanim przejdziesz dalej

**Dla zaawansowanych:**
1. Możesz pominąć Quickstart i iść od razu do sekcji "Wariant A" w 26_DEPLOYMENT_PRODUCTION.md
2. Dostosuj docker-compose.npm.yml do swoich potrzeb
3. Dodaj custom konfigurację w NPM Advanced tab

## 🔗 Przydatne linki

### W projekcie
- [README.md](../README.md) - Główny readme projektu
- [00_INDEX.md](00_INDEX.md) - Pełny indeks dokumentacji
- [26_DEPLOYMENT_PRODUCTION.md](26_DEPLOYMENT_PRODUCTION.md) - Pełna dokumentacja wdrożenia

### Zewnętrzne
- [Nginx Proxy Manager Docs](https://nginxproxymanager.com/guide/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Let's Encrypt Rate Limits](https://letsencrypt.org/docs/rate-limits/)

## 📞 Wsparcie

Jeśli masz problem:
1. Sprawdź [NPM_CHEATSHEET.md](../NPM_CHEATSHEET.md) - Troubleshooting
2. Zobacz [20_TROUBLESHOOTING.md](20_TROUBLESHOOTING.md)
3. Zgłoś issue na GitHub

---

**Ostatnia aktualizacja:** 2026-01-02  
**Wersja:** 1.0  
**Status:** ✅ Kompletna dokumentacja dla Nginx Proxy Manager

Powodzenia z wdrożeniem! 🚀

