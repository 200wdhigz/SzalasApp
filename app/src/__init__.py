from flask import Flask, session
from firebase_admin import credentials, initialize_app, firestore, _apps
import os
import secrets

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


def create_app():
    template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates')
    app = Flask("SzalasApp", template_folder=template_dir)
    app.secret_key = os.getenv('SECRET_KEY')

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
            initialize_app(cred, {'projectId': GOOGLE_PROJECT_ID})
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

    @app.route('/health')
    def health_check():
        """Health check endpoint for Docker and load balancers."""
        try:
            firestore.client()
            return {'status': 'healthy', 'service': 'SzalasApp'}, 200
        except Exception as e:
            app.logger.error(f"Health check failed: {e}")
            return {'status': 'unhealthy', 'error': str(e)}, 503

    @app.route('/.well-known/<path:filename>')
    def well_known(filename):
        """Serves .well-known files."""
        return app.send_static_file(os.path.join('.well-known', filename))

    return app
