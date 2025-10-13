from flask import Flask
import sqlite3
from firebase_admin import credentials, initialize_app, firestore
import os


def get_firestore_client():
    """Zwraca klienta Firestore. Zakłada, że aplikacja Firebase jest już zainicjalizowana."""
    # W Cloud Run/środowisku, gdzie inicjalizacja działa poprawnie, zwróci klienta.
    return firestore.client()


def get_db_connection():
    """Funkcja łącząca się z bazą danych."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Zwraca wiersze jako słowniki
    return conn


def create_app():
    template_folder_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates')

    app = Flask(__name__, template_folder=template_folder_path)
    app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key_change_me')

    @app.context_processor
    def inject_global_vars():
        """Udostepnia zmienne środowiskowe we wszystkich szablonach Jinja."""
        return dict(
            # Przekazujemy klucz reCAPTCHA (wartość z .env)
            RECAPTCHA_KEY=os.getenv('RECAPTCHA_SITE_KEY'),
            # Jeśli potrzebujesz innych zmiennych globalnych, dodaj je tutaj
            # np. IS_LOGGED_IN=('user_id' in session)
        )

    # Inicjalizacja Firebase Admin SDK (dla weryfikacji tokenów)
    try:
        # Próba użycia domyślnych poświadczeń GCP (Cloud Run)
        cred = credentials.ApplicationDefault()
        initialize_app(cred, {
            'projectId': os.getenv('FIREBASE_PROJECT_ID'),
        })
    except Exception as e:
        print(f"Ostrzeżenie: Nie można zainicjalizować Firebase Admin SDK z ApplicationDefault. Błąd: {e}")

    # Importowanie i rejestracja Blueprintów (naszych modułów)
    from .views import views_bp
    from .auth import auth_bp

    app.register_blueprint(views_bp)
    app.register_blueprint(auth_bp)

    return app
