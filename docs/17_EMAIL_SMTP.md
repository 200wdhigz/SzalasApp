# Email SMTP - Konfiguracja
## 📧 Setup Gmail
### 1. Włącz 2FA
https://myaccount.google.com/security
### 2. Wygeneruj App Password
https://myaccount.google.com/apppasswords
### 3. Konfiguracja .env
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=twoj-email@gmail.com
SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx  # App Password
FROM_EMAIL=twoj-email@gmail.com
```
## Setup Microsoft 365
```bash
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=email@twojafirma.com
SMTP_PASSWORD=twoje-haslo
FROM_EMAIL=email@twojafirma.com
```
## Testowanie
```python
# Test SMTP connection
python -c "
import smtplib
from email.mime.text import MIMEText
msg = MIMEText('Test')
msg['Subject'] = 'Test'
msg['From'] = 'from@example.com'
msg['To'] = 'to@example.com'
with smtplib.SMTP('smtp.gmail.com', 587) as server:
    server.starttls()
    server.login('user', 'password')
    server.send_message(msg)
    print('OK')
"
```
---
**Ostatnia aktualizacja:** 2026-01-01
