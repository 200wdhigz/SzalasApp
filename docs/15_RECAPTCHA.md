# reCAPTCHA Enterprise
## 🛡️ Konfiguracja
### 1. Utwórz projekt reCAPTCHA
1. https://cloud.google.com/recaptcha-enterprise
2. Create key → wybierz projekt
3. Typ: Website
4. Domena: localhost (dev) + twoja-domena.com (prod)
### 2. Konfiguracja .env
```bash
RECAPTCHA_SITE_KEY=6Lxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
RECAPTCHA_PROJECT_ID=twoj-project-id
```
## Zastosowanie
**Chroni:**
- Formularz zgłaszania usterek
- Przed botami i spamem
**Score:**
- 0.0-1.0 (im wyższy tym bardziej człowiek)
- Threshold: 0.5
---
**Ostatnia aktualizacja:** 2026-01-01
