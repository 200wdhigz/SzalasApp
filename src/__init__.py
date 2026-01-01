from flask import Flask, session
from firebase_admin import credentials, initialize_app, firestore, _apps
import os
import secrets


def generate_csrf_token():
    """Generuje token CSRF dla sesji."""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']


def get_firestore_client():
    """Zwraca klienta Firestore."""
    return firestore.client()


def create_app():
    template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates')
    app = Flask("SzalasApp", template_folder=template_dir)
    app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key_change_me')

    @app.context_processor
    def inject_vars():
        return dict(
            RECAPTCHA_KEY=os.getenv('RECAPTCHA_SITE_KEY'),
            is_debug=app.debug,
            IS_LOGGED_IN=('user_id' in session),
            IS_ADMIN=('user_id' in session and session.get('is_admin')),
            csrf_token=generate_csrf_token
        )

    if not _apps:
        try:
            cred = credentials.ApplicationDefault()
            initialize_app(cred, {'projectId': os.getenv('FIREBASE_PROJECT_ID')})
        except Exception as e:
            print(f"Firebase initialization warning: {e}")

    from .views import views_bp
    from .auth import auth_bp
    from .oauth import oauth_bp
    from .admin import admin_bp
    app.register_blueprint(views_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(oauth_bp)
    app.register_blueprint(admin_bp)

    return app
