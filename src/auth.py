from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
import os
import requests
from firebase_admin import auth

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
            session['user_id'] = decoded_token['uid']
            
            # Sprawdzamy, czy użytkownik ma rolę admina i zapisujemy to w sesji
            session['is_admin'] = decoded_token.get('admin', False)

            flash('Pomyślnie zalogowano!', 'success')
            return redirect(url_for('views.index'))
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
    return redirect(url_for('views.index'))
