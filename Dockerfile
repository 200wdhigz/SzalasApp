# Używamy lekkiego obrazu Python
FROM python:3.13.8-slim

# Ustawiamy katalog roboczy wewnątrz kontenera
WORKDIR /app

# Kopiujemy pliki potrzebne do instalacji zależności
COPY requirements.txt .

# Instalujemy zależności
RUN pip install -r requirements.txt

# Kopiujemy resztę kodu aplikacji do kontenera
# Pamiętaj: NIE KOPIUJEMY PLIKU .env (dlatego jest on na liście .dockerignore)
COPY . .

# W Cloud Run baza danych SQLite nie może być trwała!
# Dla prostoty: Używamy SQLite, a dane są ładowane przy starcie.
# W produkcyjnym środowisku powinieneś użyć Cloud SQL lub Firestore.
# Uruchomienie init_db.py przed uruchomieniem serwera Flask
RUN python init_db.py

# Ustawienie zmiennej środowiskowej dla portu. Cloud Run używa PORT.
ENV PORT 8080

# Używamy Gunicorn do obsługi aplikacji Flask w środowisku produkcyjnym
# (Gunicorn jest zawarty w requirements.txt)
# Uruchomienie aplikacji za pomocą Gunicorn na porcie Cloud Run
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
