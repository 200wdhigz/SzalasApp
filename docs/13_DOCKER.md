# Docker Deployment
## 🐳 Uruchomienie przez Docker
```bash
# Build
docker build -t szalasapp .
# Run
docker run -d -p 5000:5000 --env-file .env szalasapp
```
## Docker Compose
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "5000:5000"
    env_file:
      - .env
    restart: unless-stopped
```
**Więcej:** Zobacz Dockerfile w głównym folderze projektu.
---
**Ostatnia aktualizacja:** 2026-01-01
