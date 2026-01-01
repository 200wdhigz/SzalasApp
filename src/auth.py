from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
import os
import requests
from firebase_admin import auth

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
        api_key = os.getenv('FIREBASE_API_KEY')
        auth_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"

        try:
            response = requests.post(auth_url, json={
                'email': email,
                'password': password,
                'returnSecureToken': True
            })
            response.raise_for_status()
            print(response.json())
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
            print(f"User {decoded_token['email']} is admin: {session['is_admin']}")

            flash('Pomyślnie zalogowano!', 'success')
            return redirect(url_for('views.sprzet_list'))
        except requests.exceptions.HTTPError:
            flash('Błąd logowania: Nieprawidłowe dane.', 'danger')
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
