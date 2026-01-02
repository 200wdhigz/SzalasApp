# Dokumentacja SzalasApp

Witaj w dokumentacji systemu zarządzania sprzętem SzalasApp!

## 📚 Spis Treści

### Podstawy
1. [README.md](../README.md) - Główna dokumentacja projektu
2. [Szybki Start](01_QUICK_START.md) - Pierwsze kroki z aplikacją
3. [Architektura](02_ARCHITECTURE.md) - Struktura systemu

### Zarządzanie Użytkownikami
4. [OAuth Setup](03_OAUTH_SETUP.md) - Konfiguracja Google i Microsoft OAuth
5. [Zarządzanie Kontami](04_ACCOUNT_MANAGEMENT.md) - Funkcje dla użytkowników
6. [Synchronizacja Użytkowników](05_USER_SYNC.md) - Synchronizacja z Firebase

### Funkcje Systemu
7. [Zarządzanie Sprzętem](06_EQUIPMENT_MANAGEMENT.md) - Katalog i edycja sprzętu
8. [System Usterek](07_MALFUNCTION_SYSTEM.md) - Zgłaszanie i śledzenie usterek
9. [Eksport Danych](08_DATA_EXPORT.md) - CSV, XLSX, DOCX, PDF

### Administracja
10. [Panel Administratora](09_ADMIN_PANEL.md) - Wszystkie funkcje admina
11. [Bezpieczeństwo](10_SECURITY.md) - Zabezpieczenia i najlepsze praktyki
12. [Backup i Restore](11_BACKUP_RESTORE.md) - Kopie zapasowe danych

### Deployment
13. [Instalacja i Konfiguracja](12_INSTALLATION.md) - Szczegółowa instalacja
14. [Docker Deployment](13_DOCKER.md) - Uruchomienie w kontenerze
15. [Monitoring i Logi](14_MONITORING.md) - Śledzenie błędów

### API i Integracje
16. [reCAPTCHA](15_RECAPTCHA.md) - Ochrona przed botami
17. [Firebase](16_FIREBASE.md) - Konfiguracja Firebase
18. [Email SMTP](17_EMAIL_SMTP.md) - Konfiguracja powiadomień email

### Rozszerzenia
19. [Changelog](18_CHANGELOG.md) - Historia zmian
20. [FAQ](19_FAQ.md) - Najczęściej zadawane pytania
21. [Rozwiązywanie Problemów](20_TROUBLESHOOTING.md) - Typowe problemy

### Dla Deweloperów
22. [Rozwój Aplikacji](21_DEVELOPMENT.md) - Środowisko deweloperskie
23. [Testy](22_TESTING.md) - Strategia testowania
24. [Contributing](23_CONTRIBUTING.md) - Jak kontrybuować
25. [Zarządzanie Zależnościami](24_DEPENDENCIES.md) - Poetry i pip
26. [Podsumowanie Funkcji](25_FEATURE_SUMMARY.md) - Wszystkie funkcje

---

### Najczęściej Używane
- [Instalacja krok po kroku](12_INSTALLATION.md)
- [Konfiguracja OAuth](03_OAUTH_SETUP.md)
- [Zarządzanie użytkownikami](09_ADMIN_PANEL.md)
- [FAQ](19_FAQ.md)

### Dla Administratorów
- [Panel Administratora](09_ADMIN_PANEL.md)
- [Bezpieczeństwo](10_SECURITY.md)
- [Backup](11_BACKUP_RESTORE.md)
- [Monitoring](14_MONITORING.md)

### Dla Użytkowników
- [Szybki Start](01_QUICK_START.md)
- [Zarządzanie Kontem](04_ACCOUNT_MANAGEMENT.md)
- [Zgłaszanie Usterek](07_MALFUNCTION_SYSTEM.md)

### Dla Deweloperów
- [Architektura](02_ARCHITECTURE.md)
- [Rozwój](21_DEVELOPMENT.md)
- [Testy](22_TESTING.md)

## 📖 Jak Czytać Dokumentację

### Jesteś Nowym Użytkownikiem?
Zacznij od:
1. [README.md](../README.md) - Przegląd projektu
2. [Szybki Start](01_QUICK_START.md) - Pierwsze kroki
3. [Zarządzanie Kontami](04_ACCOUNT_MANAGEMENT.md) - Twoje konto

### Jesteś Administratorem?
Przeczytaj:
1. [Instalacja](12_INSTALLATION.md) - Setup środowiska
2. [OAuth Setup](03_OAUTH_SETUP.md) - Konfiguracja logowania
3. [Panel Administratora](09_ADMIN_PANEL.md) - Wszystkie funkcje
4. [Bezpieczeństwo](10_SECURITY.md) - Zabezpieczenia

### Jesteś Deweloperem?
Zobacz:
1. [Architektura](02_ARCHITECTURE.md) - Struktura systemu
2. [Rozwój](21_DEVELOPMENT.md) - Setup deweloperski
3. [Contributing](23_CONTRIBUTING.md) - Zasady kontrybuowania

## 🆕 Co Nowego?

### Wersja 1.1.1 (2026-01-01)
- ✅ Synchronizacja użytkowników z Firebase Auth
- ✅ Usuwanie użytkowników z aplikacji
- ✅ Samodzielna zmiana hasła/emaila
- ✅ Email notifications przy resecie hasła
- ✅ Inteligentne komunikaty błędów logowania

Zobacz pełny [Changelog](18_CHANGELOG.md)

## 📞 Wsparcie

### Masz Problem?
1. Sprawdź [FAQ](19_FAQ.md)
2. Zobacz [Rozwiązywanie Problemów](20_TROUBLESHOOTING.md)
3. Przejrzyj logi aplikacji

### Znalazłeś Bug?
1. Sprawdź czy już zgłoszony w Issues
2. Zgłoś nowy issue z opisem
3. Dołącz logi i kroki reprodukcji

### Masz Pomysł?
1. Sprawdź roadmap projektu
2. Otwórz discussion z propozycją
3. Czytaj [Contributing](23_CONTRIBUTING.md)

## 🔗 Zewnętrzne Zasoby

- [Firebase Documentation](https://firebase.google.com/docs)
- [Google OAuth Guide](https://developers.google.com/identity/protocols/oauth2)
- [Microsoft OAuth Guide](https://docs.microsoft.com/en-us/azure/active-directory/develop/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Bootstrap 5 Docs](https://getbootstrap.com/docs/5.0/)

## 📝 Notacja

W dokumentacji używamy następujących oznaczeń:

- ✅ - Zaimplementowane
- ⚠️ - Wymaga uwagi
- ❌ - Nie zalecane
- 💡 - Wskazówka
- 🔒 - Związane z bezpieczeństwem
- 📧 - Wymaga konfiguracji SMTP
- 🔑 - Wymaga uprawnień admina
- 🆕 - Nowa funkcja

## 📄 Licencja

Ten projekt i jego dokumentacja są dostępne na licencji określonej w pliku LICENSE.

---

**Ostatnia aktualizacja:** 2026-01-01  
**Wersja dokumentacji:** 1.1.0  
**Wersja aplikacji:** 1.1.1

