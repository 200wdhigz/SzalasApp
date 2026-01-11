﻿# Docker Deployment
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

## Obrazy Docker publikowane automatycznie (DockerHub)

Projekt publikuje obraz `filiprar/szalasapp` automatycznie przez GitHub Actions.

### Znaczenie tagów
- `edge` – **bieżący build po każdym merge/push do `master`**. Może zawierać nieprzetestowane poprawki.
- `sha-<commit>` – ten sam build co `edge`, ale przypięty do konkretnego commita (łatwy rollback).
- `vX.Y.Z` – **stabilna wersja** publikowana tylko wtedy, gdy w PR podniesiesz wersję w `app/pyproject.toml` i zostanie utworzony tag `vX.Y.Z`.
- `latest` – wskazuje na najnowszą opublikowaną wersję `vX.Y.Z`.

> Ważne: Jeśli nie zmienisz numeru `version` w `app/pyproject.toml`, to nie powstanie nowy tag `vX.Y.Z` ani `latest`.

## Jak wypuścić nową wersję (dla maintainerów)

### Opcja 1: GitHub UI (bez komend git)
1. Wejdź w repozytorium na GitHub.
2. Utwórz Pull Request (PR) z Twoimi zmianami.
3. W tym samym PR edytuj plik `app/pyproject.toml` i zmień:
   - `version = "X.Y.Z"` na nową wersję (np. `0.2.0`).
4. Zmerguj PR do `master`.
5. GitHub Actions automatycznie:
   - utworzy tag `vX.Y.Z` i GitHub Release,
   - opublikuje obraz na DockerHub z tagami `vX.Y.Z` oraz `latest`.

### Opcja 2: IDE (PyCharm/VS Code) bez ręcznego gita
- Zrób commit zmian w IDE.
- Otwórz PR z IDE.
- Zmień `app/pyproject.toml` (jak wyżej) i zmerguj PR.

## Jak zaktualizować wdrożenie na serwerze (Docker Compose)

Jeśli wdrożenie korzysta z obrazu z DockerHub (a nie buildowania lokalnie), aktualizacja zwykle wygląda tak:

1. W pliku `docker-compose.yml` ustaw obraz (przykład):
   - `image: filiprar/szalasapp:latest` (zawsze najnowsza stabilna)
   - albo `image: filiprar/szalasapp:vX.Y.Z` (konkretna wersja)

2. Na serwerze wykonaj aktualizację kontenera (Linux):
```bash
docker compose pull
docker compose up -d
```

Rollback:
- zmień tag na starszy `vX.Y.Z` albo konkretny `sha-...` i wykonaj `docker compose up -d`.

**Więcej:** Zobacz Dockerfile w głównym folderze projektu.
---
**Ostatnia aktualizacja:** 2026-01-01
