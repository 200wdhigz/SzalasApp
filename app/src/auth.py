from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
import requests
from firebase_admin import auth

from . import GOOGLE_API_KEY
from .db_users import get_user_by_uid, create_user

auth_bp = Blueprint('auth', __name__, url_prefix='/')

def login_required(f):
    """Dekorator do sprawdzania, czy użytkownik jest zalogowany."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Musisz się zalogować, aby uzyskać dostęp.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
def admin_required(f):
    """Dekorator do sprawdzania, czy użytkownik jest zalogowany i czy jest administratorem."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Musisz się zalogować, aby uzyskać dostęp.', 'danger')
            return redirect(url_for('auth.login'))
        if session.get('user_role') != 'admin':
            flash('Nie masz uprawnień administratora.', 'danger')
            return redirect(url_for('views.sprzet_list'))
        return f(*args, **kwargs)
    return decorated_function

def quartermaster_required(f):
    """Dekorator do sprawdzania, czy użytkownik jest zalogowany i czy jest kwatermistrzem lub adminem."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Musisz się zalogować, aby uzyskać dostęp.', 'danger')
            return redirect(url_for('auth.login'))
        if session.get('user_role') not in ['quartermaster', 'admin']:
            flash('Ta strona wymaga uprawnień kwatermistrza.', 'danger')
            return redirect(url_for('views.sprzet_list'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not GOOGLE_API_KEY:
            flash('Brakuje konfiguracji GOOGLE_API_KEY. Skontaktuj się z administratorem.', 'danger')
            return redirect(url_for('auth.login'))

        auth_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={GOOGLE_API_KEY}"

        try:
            response = requests.post(auth_url, json={
                'email': email,
                'password': password,
                'returnSecureToken': True
            }, timeout=15)
            response.raise_for_status()

            id_token = response.json()['idToken']
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token['uid']

            # NOTE: Firebase custom claims are top-level keys of decoded_token.
            # Previously we used 'admin', but our user documents store 'is_admin'.
            # Keep session consistent with Firestore field: is_admin.
            is_admin = bool(decoded_token.get('admin', False))

            # Sprawdź, czy użytkownik istnieje w Firestore, jeżeli nie - utwórz
            user = get_user_by_uid(uid)
            if not user:
                create_user(uid, email, is_admin=is_admin)
                user = get_user_by_uid(uid)

            # Jeśli użytkownik jest wyłączony w Firestore
            if not user.get('active', True):
                flash('Twoje konto zostało wyłączone. Skontaktuj się z administratorem.', 'danger')
                return redirect(url_for('auth.login'))

            # Jeśli użytkownik jest wyłączony w Firebase Auth (np. disabled=True)
            try:
                record = auth.get_user(uid)
                if getattr(record, 'disabled', False):
                    flash('Twoje konto zostało wyłączone. Skontaktuj się z administratorem.', 'danger')
                    return redirect(url_for('auth.login'))
            except Exception:
                # nie blokujemy logowania jeśli nie uda się pobrać user record
                pass

            session['user_id'] = uid
            session['is_admin'] = bool(user.get('is_admin', is_admin))
            session['user_role'] = user.get('role', 'admin' if session['is_admin'] else 'reporter')
            session['user_name'] = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or email

            flash('Pomyślnie zalogowano!', 'success')
            return redirect(url_for('views.sprzet_list'))

        except requests.exceptions.HTTPError:
            # Błąd 400/401 z Identity Toolkit — najczęściej złe hasło lub email.
            # Dodatkowo możemy podpowiedzieć, jeśli konto jest OAuth-only.
            from .db_users import get_user_by_email
            user = get_user_by_email(email)

            if user and (user.get('google_id') or user.get('microsoft_id')):
                oauth_methods = []
                if user.get('google_id'):
                    oauth_methods.append('Google')
                if user.get('microsoft_id'):
                    oauth_methods.append('Microsoft')

                flash(
                    f'To konto ma powiązane logowanie przez {" i ".join(oauth_methods)}. '
                    f'Użyj odpowiedniego przycisku poniżej aby się zalogować.',
                    'warning'
                )
            else:
                flash('Błąd logowania: Nieprawidłowy email lub hasło.', 'danger')

        except requests.exceptions.Timeout:
            flash('Błąd logowania: timeout połączenia z usługą logowania. Spróbuj ponownie.', 'danger')
        except Exception as e:
            flash(f'Wystąpił błąd serwera: {e}', 'danger')

        return redirect(url_for('auth.login'))

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('is_admin', None)
    session.pop('user_role', None)
    session.pop('user_name', None)
    flash('Wylogowano pomyślnie.', 'info')
    return redirect(url_for('views.sprzet_list'))
