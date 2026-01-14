from flask import Flask, session
from firebase_admin import credentials, initialize_app, firestore, _apps
import os
import secrets

# Load .env (development/local) early so the app behaves the same under gunicorn and flask.
# Prefer app/.env if present, otherwise fall back to repo-root .env.
try:
    from dotenv import load_dotenv

    here = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.dirname(here)  # .../app
    repo_root = os.path.dirname(app_dir)

    # 1) app/.env
    load_dotenv(os.path.join(app_dir, '.env'), override=False)
    # 2) repo root .env
    load_dotenv(os.path.join(repo_root, '.env'), override=False)
except Exception:
    # dotenv is optional in production; ignore if missing
    pass

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_PROJECT_ID = os.getenv('GOOGLE_PROJECT_ID')
GOOGLE_CLOUD_STORAGE_BUCKET_NAME = os.getenv('GOOGLE_CLOUD_STORAGE_BUCKET_NAME')


def generate_csrf_token():
    """Generuje token CSRF dla sesji."""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']


def get_firestore_client():
    """Zwraca klienta Firestore."""
    return firestore.client()


def _init_firebase_admin():
    """Inicjalizuje Firebase Admin w sposób przyjazny dla localhost/Docker.

    Preferuje service account JSON (GOOGLE_APPLICATION_CREDENTIALS), bo ADC na
    środowiskach bez metadata server potrafi kończyć się długim timeoutem.
    """
    if _apps:
        return

    cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    try:
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            initialize_app(cred, {'projectId': GOOGLE_PROJECT_ID} if GOOGLE_PROJECT_ID else {})
            return

        # Fallback: Application Default Credentials
        cred = credentials.ApplicationDefault()
        initialize_app(cred, {'projectId': GOOGLE_PROJECT_ID} if GOOGLE_PROJECT_ID else {})
    except Exception as e:
        # Nie wywalamy aplikacji przy starcie, ale logujemy ostrzeżenie.
        print(f"Firebase initialization warning: {e}")


def _is_truthy(value: str | None) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def create_app():
    template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates')
    app = Flask("SzalasApp", template_folder=template_dir)
    app.secret_key = os.getenv('SECRET_KEY')

    @app.context_processor
    def inject_vars():
        user_role = session.get('user_role')
        return dict(
            is_debug=app.debug,
            IS_LOGGED_IN=('user_id' in session),
            IS_ADMIN=('user_id' in session and user_role == 'admin'),
            IS_QUARTERMASTER=('user_id' in session and user_role in ['quartermaster', 'admin']),
            USER_ROLE=user_role,
            csrf_token=generate_csrf_token
        )

    _init_firebase_admin()

    from .views import views_bp
    from .auth import auth_bp
    from .oauth import oauth_bp
    from .admin import admin_bp
    app.register_blueprint(views_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(oauth_bp)
    app.register_blueprint(admin_bp)

    @app.route('/health')
    def health_check():
        """Health check endpoint.

        Domyślnie jest to **liveness** (czy aplikacja działa) i zwraca 200 nawet
        bez połączenia do Firestore (np. lokalnie / w CI bez credentials).

        Jeśli chcesz wymusić sprawdzenie zależności (readiness), ustaw:
        HEALTHCHECK_STRICT=true
        """
        strict = _is_truthy(os.getenv("HEALTHCHECK_STRICT"))
        try:
            if strict:
                if not _apps:
                    raise RuntimeError("Firebase Admin not initialized")
                firestore.client()
            return {
                'status': 'healthy',
                'service': 'SzalasApp',
                'firebase_initialized': bool(_apps),
                'strict': strict,
            }, 200
        except Exception as e:
            app.logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'service': 'SzalasApp',
                'firebase_initialized': bool(_apps),
                'strict': strict,
                'error': str(e)
            }, 503

    @app.route('/.well-known/<path:filename>')
    def well_known(filename):
        """Serves .well-known files."""
        return app.send_static_file(os.path.join('.well-known', filename))

    return app
