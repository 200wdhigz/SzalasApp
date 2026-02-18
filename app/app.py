from src import create_app
import os
from dotenv import load_dotenv

load_dotenv()

app = create_app()

DEBUG = os.getenv("DEBUG", False)
PORT = int(os.getenv('PORT', 80))
HOST = os.getenv('HOST', '0.0.0.0')

# Konfiguracja dla reverse proxy (Nginx Proxy Manager)
# Gdy aplikacja działa za reverse proxy z HTTPS, ustaw PREFERRED_URL_SCHEME=https
PREFERRED_URL_SCHEME = os.getenv('PREFERRED_URL_SCHEME', 'http')
app.config['PREFERRED_URL_SCHEME'] = PREFERRED_URL_SCHEME


if __name__ == '__main__':
    # Uruchomienie aplikacji w trybie debugowania
    print(f"🚀 Starting Szałas App")
    print(f"   Host: {HOST}")
    print(f"   Port: {PORT}")
    print(f"   Debug: {DEBUG}")
    print(f"   URL Scheme: {PREFERRED_URL_SCHEME}")
    if PREFERRED_URL_SCHEME == 'https':
        print(f"   ℹ️  App expects to run behind HTTPS reverse proxy (e.g., Nginx Proxy Manager)")

    app.run(debug=DEBUG, port=PORT, host=HOST)

