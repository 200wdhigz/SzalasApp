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
        if not session.get('is_admin'):
            flash('Nie masz uprawnień do dostępu do tej strony.', 'danger')
            return redirect(url_for('views.sprzet_list'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        auth_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={GOOGLE_API_KEY}"

        try:
            response = requests.post(auth_url, json={
                'email': email,
                'password': password,
                'returnSecureToken': True
            })
            response.raise_for_status()
            id_token = response.json()['idToken']
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token['uid']
            
            # Sprawdzamy, czy użytkownik ma rolę admina i zapisujemy to w sesji
            is_admin = decoded_token.get('admin', False)
            
            # Sprawdź, czy użytkownik istnieje w Firestore, jeśli nie - utwórz
            user = get_user_by_uid(uid)
            if not user:
                # Utwórz dokument użytkownika w Firestore
                create_user(uid, email, is_admin=is_admin)
                user = get_user_by_uid(uid)
            
            # Sprawdź, czy konto jest aktywne
            if not user.get('active', True):
                flash('Twoje konto zostało wyłączone. Skontaktuj się z administratorem.', 'danger')
                return redirect(url_for('auth.login'))
            
            session['user_id'] = uid
            session['is_admin'] = is_admin
            session['user_name'] = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or email


            flash('Pomyślnie zalogowano!', 'success')
            return redirect(url_for('views.sprzet_list'))
        except requests.exceptions.HTTPError as e:
            # Check if user exists and has OAuth accounts linked
            from .db_users import get_user_by_email
            user = get_user_by_email(email)

            if user and (user.get('google_id') or user.get('microsoft_id')):
                oauth_methods = []
                if user.get('google_id'):
                    oauth_methods.append('Google')
                if user.get('microsoft_id'):
                    oauth_methods.append('Microsoft')

                flash(f'To konto ma powiązane logowanie przez {" i ".join(oauth_methods)}. '
                      f'Użyj odpowiedniego przycisku poniżej aby się zalogować.', 'warning')
            else:
                flash('Błąd logowania: Nieprawidłowy email lub hasło.', 'danger')
        except Exception as e:
            flash(f'Wystąpił błąd serwera: {e}', 'danger')
        return redirect(url_for('auth.login'))

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('is_admin', None) # Usuwamy flagę admina przy wylogowaniu
    flash('Wylogowano pomyślnie.', 'info')
    return redirect(url_for('views.sprzet_list'))
