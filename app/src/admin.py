from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from firebase_admin import auth as firebase_auth
import secrets
import string
import os

from .auth import admin_required, quartermaster_required
from .db_firestore import (
    get_all_logs, add_log, restore_item, get_config, update_config
)
from .db_users import (
    get_all_users, get_user_by_uid, update_user,
    set_user_active_status, set_user_admin_status, create_user,
    delete_user, sync_users_from_firebase_auth
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
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        role = request.form.get('role', 'reporter')
        is_admin = role == 'admin'
        
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
            else:
                firebase_auth.set_custom_user_claims(fb_user.uid, {'admin': False})
            
            # Utwórz dokument użytkownika w Firestore
            create_user(fb_user.uid, email, is_admin=is_admin, role=role, active=True,
                       first_name=first_name or None, last_name=last_name or None)

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
        role = request.form.get('role', 'reporter')
        is_admin = role == 'admin'
        active = request.form.get('active') == 'on'
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        new_email = request.form.get('email', '').strip()

        if not new_email:
            flash('Email jest wymagany.', 'danger')
            return render_template('admin/user_edit.html', user=user)

        try:
            # Sprawdź czy email się zmienił
            if new_email != fb_user.email:
                # Sprawdź czy nowy email już istnieje
                try:
                    existing_user = firebase_auth.get_user_by_email(new_email)
                    if existing_user.uid != user_id:
                        flash(f'Email {new_email} jest już używany przez innego użytkownika.', 'danger')
                        return render_template('admin/user_edit.html', user=user)
                except firebase_auth.UserNotFoundError:
                    # Email nie istnieje - można go użyć
                    pass

                # Zaktualizuj email w Firebase Auth
                firebase_auth.update_user(user_id, email=new_email)

                # Zaktualizuj email w Firestore
                from .db_users import update_user_email
                update_user_email(user_id, new_email)

                flash(f'Email użytkownika został zmieniony na {new_email}.', 'success')

            # Aktualizuj pozostałe dane w Firestore
            update_user(user_id, is_admin=is_admin, role=role, active=active,
                       first_name=first_name or None, last_name=last_name or None)

            # Aktualizuj custom claims w Firebase Auth
            firebase_auth.set_custom_user_claims(user_id, {'admin': is_admin})
            
            flash(f'Użytkownik został zaktualizowany.', 'success')
            return redirect(url_for('admin.users_list'))
        
        except firebase_auth.EmailAlreadyExistsError:
            flash(f'Email {new_email} jest już używany przez innego użytkownika.', 'danger')
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
        user_email = user.get("email", "")

        # Wyślij email z nowym hasłem
        try:
            send_password_reset_email(user_email, new_password)
            email_sent = True
        except Exception as email_error:
            print(f'Error sending email: {email_error}')
            email_sent = False

        # Store password in session temporarily for display
        session['reset_password'] = new_password
        session['reset_password_email'] = user_email
        session['reset_password_email_sent'] = email_sent

        if email_sent:
            flash(f'Hasło użytkownika {user_email} zostało zresetowane. Nowe hasło zostało wysłane na email i zostanie wyświetlone na następnej stronie.', 'success')
        else:
            flash(f'Hasło użytkownika {user_email} zostało zresetowane, ale nie udało się wysłać emaila. Nowe hasło zostanie wyświetlone na następnej stronie.', 'warning')
    except Exception as e:
        flash(f'Wystąpił błąd podczas resetowania hasła: {str(e)}', 'danger')
    
    return redirect(url_for('admin.users_list'))


def send_password_reset_email(email, new_password):
    """Wysyła email z nowym hasłem do użytkownika."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    from_email = os.getenv('FROM_EMAIL', smtp_user)

    if not smtp_user or not smtp_password:
        raise Exception('SMTP credentials not configured')

    # Twórz wiadomość
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Twoje hasło zostało zresetowane - Panel Kwatermistrza'
    msg['From'] = from_email
    msg['To'] = email

    # Tekst wiadomości
    text = f"""
Witaj,

Twoje hasło do Panelu Kwatermistrza zostało zresetowane przez administratora.

Twoje nowe hasło: {new_password}

Zalecamy zmianę tego hasła po zalogowaniu w ustawieniach konta.

Aby się zalogować, odwiedź: {os.getenv('BASE_URL', 'http://localhost:5000')}/login

Pozdrawiamy,
Panel Kwatermistrza
"""

    html = f"""
<html>
<head></head>
<body>
    <h2>Twoje hasło zostało zresetowane</h2>
    <p>Witaj,</p>
    <p>Twoje hasło do <strong>Panelu Kwatermistrza</strong> zostało zresetowane przez administratora.</p>
    <div style="background-color: #f0f0f0; padding: 15px; margin: 20px 0; border-left: 4px solid #007bff;">
        <strong>Twoje nowe hasło:</strong><br>
        <code style="font-size: 16px; color: #d63384;">{new_password}</code>
    </div>
    <p><strong>Zalecamy zmianę tego hasła po zalogowaniu w ustawieniach konta.</strong></p>
    <p>Aby się zalogować, kliknij tutaj: <a href="{os.getenv('BASE_URL', 'http://localhost:5000')}/login">Zaloguj się</a></p>
    <hr>
    <p style="color: #666; font-size: 12px;">Pozdrawiamy,<br>Panel Kwatermistrza</p>
</body>
</html>
"""

    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    msg.attach(part1)
    msg.attach(part2)

    # Wyślij email
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)


@admin_bp.route('/users/sync', methods=['POST'])
@admin_required
def users_sync():
    """Synchronizuje użytkowników z Firebase Auth."""
    if not validate_csrf_token():
        return redirect(url_for('admin.users_list'))

    try:
        deleted_count, added_count = sync_users_from_firebase_auth()

        if deleted_count > 0 or added_count > 0:
            flash(f'Synchronizacja zakończona: usunięto {deleted_count}, dodano {added_count} użytkowników.', 'success')
        else:
            flash('Lista użytkowników jest już zsynchronizowana.', 'info')
    except Exception as e:
        flash(f'Wystąpił błąd podczas synchronizacji: {str(e)}', 'danger')

    return redirect(url_for('admin.users_list'))


@admin_bp.route('/users/<user_id>/delete', methods=['POST'])
@admin_required
def user_delete(user_id):
    """Usuwa użytkownika całkowicie (z Firebase Auth i Firestore)."""
    if not validate_csrf_token():
        return redirect(url_for('admin.users_list'))

    try:
        user = get_user_by_uid(user_id)
        user_email = user.get('email', 'Unknown') if user else 'Unknown'

        # Usuń z Firebase Auth
        firebase_auth.delete_user(user_id)

        # Usuń z Firestore
        delete_user(user_id)

        flash(f'Użytkownik {user_email} został całkowicie usunięty.', 'success')
    except Exception as e:
        flash(f'Wystąpił błąd podczas usuwania użytkownika: {str(e)}', 'danger')

    return redirect(url_for('admin.users_list'))

@admin_bp.route('/restore/<log_id>', methods=['POST'])
@quartermaster_required
def log_restore(log_id):
    """Przywraca stan obiektu z loga."""
    if not validate_csrf_token():
        return redirect(url_for('views.logs_list'))
    
    success, message = restore_item(log_id, session.get('user_id'))
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(request.referrer or url_for('views.logs_list'))


@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    """Zarządzanie ustawieniami aplikacji (np. PIN)."""
    if request.method == 'POST':
        pin = request.form.get('view_pin')
        auto_rotate = request.form.get('pin_auto_rotate') == 'on'
        
        # Opcjonalnie: walidacja tokena CSRF, jeśli admin go używa (widzę że admin.py go używa)
        if not validate_csrf_token():
             return redirect(url_for('admin.settings'))

        update_data = {'pin_auto_rotate': auto_rotate}
        if pin:
            if not pin.isdigit() or len(pin) != 6:
                flash('PIN musi składać się z 6 cyfr.', 'danger')
                return redirect(url_for('admin.settings'))
            update_data['view_pin'] = pin
            from .db_firestore import _warsaw_now
            update_data['pin_last_rotate'] = _warsaw_now()
        
        update_config(**update_data)
        flash('Ustawienia zostały zapisane.', 'success')
        return redirect(url_for('admin.settings'))
            
    config = get_config()
    return render_template('admin/settings.html', config=config)



