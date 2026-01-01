# python
# file: src/admin.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from firebase_admin import auth as firebase_auth
import secrets
import string

from .auth import admin_required
from .db_users import (
    get_all_users, get_user_by_uid, update_user,
    set_user_active_status, set_user_admin_status, create_user
)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def validate_csrf_token():
    """Waliduje token CSRF z formularza."""
    token = request.form.get('_csrf_token')
    if not token or token != session.get('_csrf_token'):
        flash('Błąd weryfikacji CSRF. Odśwież stronę i spróbuj ponownie.', 'danger')
        return False
    return True


# =======================================================================
#                       USER MANAGEMENT
# =======================================================================

@admin_bp.route('/users')
@admin_required
def users_list():
    """Wyświetla listę wszystkich użytkowników."""
    users = get_all_users()
    
    # Pobierz dodatkowe dane z Firebase Auth dla każdego użytkownika
    for user in users:
        try:
            fb_user = firebase_auth.get_user(user['id'])
            user['firebase_email'] = fb_user.email
            user['firebase_display_name'] = fb_user.display_name
            user['firebase_disabled'] = fb_user.disabled
        except Exception:
            user['firebase_email'] = user.get('email', 'N/A')
            user['firebase_display_name'] = None
            user['firebase_disabled'] = False
    
    return render_template('admin/users_list.html', users=users)


@admin_bp.route('/users/new', methods=['GET', 'POST'])
@admin_required
def user_new():
    """Rejestruje nowego użytkownika."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        is_admin = request.form.get('is_admin') == 'on'
        
        if not email or not password:
            flash('Email i hasło są wymagane.', 'danger')
            return render_template('admin/user_new.html')
        
        try:
            # Utwórz użytkownika w Firebase Auth
            fb_user = firebase_auth.create_user(
                email=email,
                password=password,
                disabled=False
            )
            
            # Ustaw custom claims dla admina
            if is_admin:
                firebase_auth.set_custom_user_claims(fb_user.uid, {'admin': True})
            
            # Utwórz dokument użytkownika w Firestore
            create_user(fb_user.uid, email, is_admin=is_admin, active=True)
            
            flash(f'Użytkownik {email} został pomyślnie utworzony.', 'success')
            return redirect(url_for('admin.users_list'))
        
        except firebase_auth.EmailAlreadyExistsError:
            flash('Użytkownik z tym adresem email już istnieje.', 'danger')
        except Exception as e:
            flash(f'Wystąpił błąd podczas tworzenia użytkownika: {str(e)}', 'danger')
        
        return render_template('admin/user_new.html')
    
    return render_template('admin/user_new.html')


@admin_bp.route('/users/<user_id>/edit', methods=['GET', 'POST'])
@admin_required
def user_edit(user_id):
    """Edytuje użytkownika."""
    user = get_user_by_uid(user_id)
    
    if not user:
        flash('Nie znaleziono użytkownika.', 'danger')
        return redirect(url_for('admin.users_list'))
    
    # Pobierz dane z Firebase Auth
    try:
        fb_user = firebase_auth.get_user(user_id)
        user['firebase_email'] = fb_user.email
        user['firebase_disabled'] = fb_user.disabled
    except Exception:
        flash('Nie można pobrać danych użytkownika z Firebase Auth.', 'danger')
        return redirect(url_for('admin.users_list'))
    
    if request.method == 'POST':
        is_admin = request.form.get('is_admin') == 'on'
        active = request.form.get('active') == 'on'
        
        try:
            # Aktualizuj Firestore
            update_user(user_id, is_admin=is_admin, active=active)
            
            # Aktualizuj custom claims w Firebase Auth
            firebase_auth.set_custom_user_claims(user_id, {'admin': is_admin})
            
            flash(f'Użytkownik {user["email"]} został zaktualizowany.', 'success')
            return redirect(url_for('admin.users_list'))
        
        except Exception as e:
            flash(f'Wystąpił błąd podczas aktualizacji użytkownika: {str(e)}', 'danger')
    
    return render_template('admin/user_edit.html', user=user)


@admin_bp.route('/users/<user_id>/disable', methods=['POST'])
@admin_required
def user_disable(user_id):
    """Wyłącza konto użytkownika."""
    if not validate_csrf_token():
        return redirect(url_for('admin.users_list'))
    
    try:
        # Wyłącz w Firebase Auth
        firebase_auth.update_user(user_id, disabled=True)
        
        # Wyłącz w Firestore
        set_user_active_status(user_id, False)
        
        flash('Konto użytkownika zostało wyłączone.', 'success')
    except Exception as e:
        flash(f'Wystąpił błąd podczas wyłączania konta: {str(e)}', 'danger')
    
    return redirect(url_for('admin.users_list'))


@admin_bp.route('/users/<user_id>/enable', methods=['POST'])
@admin_required
def user_enable(user_id):
    """Włącza konto użytkownika."""
    if not validate_csrf_token():
        return redirect(url_for('admin.users_list'))
    
    try:
        # Włącz w Firebase Auth
        firebase_auth.update_user(user_id, disabled=False)
        
        # Włącz w Firestore
        set_user_active_status(user_id, True)
        
        flash('Konto użytkownika zostało włączone.', 'success')
    except Exception as e:
        flash(f'Wystąpił błąd podczas włączania konta: {str(e)}', 'danger')
    
    return redirect(url_for('admin.users_list'))


@admin_bp.route('/users/<user_id>/reset-password', methods=['POST'])
@admin_required
def user_reset_password(user_id):
    """Resetuje hasło użytkownika."""
    if not validate_csrf_token():
        return redirect(url_for('admin.users_list'))
    
    try:
        # Generuj nowe losowe hasło z większą złożonością
        alphabet = string.ascii_letters + string.digits + '!@#$%^&*'
        new_password = ''.join(secrets.choice(alphabet) for _ in range(16))
        
        # Zaktualizuj hasło w Firebase Auth
        firebase_auth.update_user(user_id, password=new_password)
        
        user = get_user_by_uid(user_id)
        # Store password in session temporarily for display on next page
        session['reset_password'] = new_password
        session['reset_password_email'] = user.get("email", "")
        flash(f'Hasło użytkownika {user.get("email", "")} zostało zresetowane. Nowe hasło zostanie wyświetlone na następnej stronie.', 'success')
    except Exception as e:
        flash(f'Wystąpił błąd podczas resetowania hasła: {str(e)}', 'danger')
    
    return redirect(url_for('admin.users_list'))
