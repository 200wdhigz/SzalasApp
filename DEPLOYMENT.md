# 🚀 Wdrożenie Produkcyjne - Szybki Start

## Cel

Wdrożenie aplikacji **SzalasApp** na serwerze produkcyjnym z:
- ✅ **Docker** i Docker Compose
- ✅ **HTTPS/SSL** (Let's Encrypt)
- ✅ **Nginx** jako reverse proxy
- ✅ Domena: `szalasapp.kawak.uk`

## 📚 Dokumentacja

### Wybierz swoją ścieżkę:

#### 🏃 Szybkie wdrożenie (15-30 minut)
**Dla tych, którzy chcą szybko uruchomić:**
- [**DEPLOYMENT_QUICKSTART.md**](DEPLOYMENT_QUICKSTART.md) - Uproszczona instrukcja

#### 📖 Pełny przewodnik (szczegółowy)
**Dla tych, którzy chcą zrozumieć każdy krok:**
- [**wiki/docs/26_DEPLOYMENT_PRODUCTION.md**](wiki/docs/26_DEPLOYMENT_PRODUCTION.md) - Kompletny poradnik

#### 📋 Cheatsheet
**Wszystkie przydatne komendy w jednym miejscu:**
- [**DEPLOYMENT_CHEATSHEET.md**](DEPLOYMENT_CHEATSHEET.md) - Szybkie odniesienie do komend

## 🛠️ Narzędzia pomocnicze

### Dla Linux (Ubuntu/Debian)
```bash
# Automatyczny setup serwera
./deploy-setup.sh
```

### Dla Windows
```powershell
# Wdrożenie z lokalnej maszyny na serwer
.\deploy-from-windows.ps1 -ServerIP YOUR_SERVER_IP -Domain szalasapp.kawak.uk
```

### Backup
```bash
# Wykonaj backup aplikacji
./backup.sh
```

## 📁 Pliki konfiguracyjne

- `nginx-config-example.conf` - Przykładowa konfiguracja Nginx z SSL
- `docker-compose.prod.yml` - Docker Compose dla produkcji
- `.env.example` - Template zmiennych środowiskowych

## ⚡ Minimalne wymagania

- **Serwer VPS:** 2GB RAM, 20GB dysk, Ubuntu 22.04
- **Domena:** Skonfigurowany rekord DNS A
- **Oprogramowanie:** Docker, Nginx, Certbot
- **Credentials:** Service Account JSON, OAuth keys

## 🎯 Szybkie kroki

1. **Przygotuj serwer VPS** (DigitalOcean, Linode, Hetzner, etc.)
2. **Skonfiguruj DNS** - dodaj rekord A dla `szalasapp.kawak.uk`
3. **Uruchom skrypt setup** lub postępuj według dokumentacji
4. **Skopiuj pliki** (.env, credentials)
5. **Uruchom Docker Compose**
6. **Uzyskaj certyfikat SSL** (Certbot)
7. **Gotowe!** 🎉

## 📞 Wsparcie

Masz problem? Sprawdź:
- [Troubleshooting](wiki/docs/26_DEPLOYMENT_PRODUCTION.md#troubleshooting) w pełnym poradniku
- [FAQ](wiki/docs/19_FAQ.md)
- [GitHub Issues](https://github.com/YOUR_REPO/SzalasApp/issues)

---

**Powodzenia z wdrożeniem! 🚀**

