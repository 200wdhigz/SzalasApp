import firebase_admin
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
import os
import requests
from firebase_admin import auth, credentials

# Utworzenie Blueprint dla logiki uwierzytelniania
auth_bp = Blueprint('auth', __name__, url_prefix='/')

def initialize_firebase(app):
    """Inicjuje Firebase Admin SDK. Wywołaj w kontekście aplikacji."""
    if not firebase_admin._apps:
        try:
            # Użyj context managera, aby rozwiązać problem z ładowaniem klucza
            with app.app_context():
                cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT_KEY)
                firebase_admin.initialize_app(cred)
                print("Firebase Admin SDK zainicjowany pomyślnie.")
        except FileNotFoundError:
            print("!!! BŁĄD: Nie znaleziono pliku serviceAccountKey.json. !!!")
        except ValueError:
            pass # Już zainicjowany


def login_required(f):
    """Dekorator do sprawdzania, czy użytkownik jest zalogowany."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Musisz się zalogować, aby uzyskać dostęp.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)

    return decorated_function


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        api_key = os.getenv('FIREBASE_API_KEY')
        auth_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"

        try:
            response = requests.post(auth_url, json={
                'email': email,
                'password': password,
                'returnSecureToken': True
            })
            response.raise_for_status()

            data = response.json()
            id_token = data['idToken']

            # Weryfikacja tokena po stronie serwera jest kluczowa dla bezpieczeństwa
            decoded_token = auth.verify_id_token(id_token)
            session['user_id'] = decoded_token['uid']
            flash('Pomyślnie zalogowano!', 'success')
            return redirect(url_for('views.index'))

        except requests.exceptions.HTTPError:
            error_message = response.json().get('error', {}).get('message', 'Nieznany błąd logowania.')
            # Używamy Bootstrapowych klas dla komunikatów flash (danger)
            flash(f'Błąd logowania: {error_message}', 'danger')
        except Exception as e:
            flash(f'Wystąpił nieoczekiwany błąd serwera: {e}', 'danger')

        return redirect(url_for('auth.login'))

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Wylogowano pomyślnie.', 'info')  # Używamy info (niebieski)
    return redirect(url_for('views.index'))
