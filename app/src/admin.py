from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from urllib.parse import urlparse
from firebase_admin import auth as firebase_auth
import secrets
import string
import os
from datetime import datetime, timedelta
from time import perf_counter, time

from .auth import admin_required, quartermaster_required, rotate_pin_if_due
from .db_firestore import (
    get_all_logs, add_log, restore_item, get_config, update_config
)
from .db_firestore import get_list_setting, update_list_setting
from .db_users import (
    get_all_users, get_user_by_uid, update_user,
    set_user_active_status, set_user_admin_status, create_user,
    delete_user, sync_users_from_firebase_auth,
    set_user_feature_flag, get_user_achievements_map,
    add_user_achievement, remove_user_achievement,
)
from .db_firestore import (
    get_all_achievements, get_achievements_map,
    set_achievement_def, delete_item, COLLECTION_ACHIEVEMENTS
)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Prosty cache Firebase Auth users z TTL 60s
_firebase_auth_cache = {
    'users': {},  # uid -> (fb_user, timestamp)
    'ttl_seconds': 60
}


def _get_cached_firebase_users(uids):
    """Zwraca cached Firebase Auth users i listę UIDów do pobrania ze świeżością."""
    now = time()
    cached = {}
    to_fetch = []
    
    for uid in uids:
        entry = _firebase_auth_cache['users'].get(uid)
        if entry and (now - entry[1]) < _firebase_auth_cache['ttl_seconds']:
            cached[uid] = entry[0]
        else:
            to_fetch.append(uid)
    
    return cached, to_fetch


def _cache_firebase_users(fb_users_dict):
    """Przechowuje Firebase Auth users w cache z timestamp."""
    now = time()
    ttl = _firebase_auth_cache['ttl_seconds']
    users = _firebase_auth_cache['users']
    # Usuń wygasłe wpisy, aby cache nie rósł bez ograniczeń
    expired_keys = [uid for uid, (_, ts) in users.items() if (now - ts) >= ttl]
    for key in expired_keys:
        del users[key]
    for uid, fb_user in fb_users_dict.items():
        users[uid] = (fb_user, now)


def _chunked(items, size):
    """Zwraca kolejne porcje listy o maksymalnym rozmiarze `size`."""
    for idx in range(0, len(items), size):
        yield items[idx:idx + size]


def _enrich_users_with_firebase_auth(users):
    """Uzupełnia listę użytkowników danymi z Firebase Auth (batch zamiast N+1, z cache)."""
    uid_to_fb_user = {}
    lookup_failed = False
    uids = [user.get('id') for user in users if user.get('id')]
    
    # Sprawdź cache
    cached, to_fetch = _get_cached_firebase_users(uids)
    uid_to_fb_user.update(cached)
    
    # Jeśli coś do pobrania, pobierz z Firebase
    if to_fetch:
        for uid_chunk in _chunked(to_fetch, 100):
            try:
                identifiers = [firebase_auth.UidIdentifier(uid) for uid in uid_chunk]
                result = firebase_auth.get_users(identifiers)
                for fb_user in result.users:
                    uid_to_fb_user[fb_user.uid] = fb_user
                # Zaktualizuj cache
                _cache_firebase_users({u.uid: u for u in result.users})
            except Exception as exc:
                lookup_failed = True
                current_app.logger.warning(f"Firebase batch user lookup failed: {exc}")
                break

    for user in users:
        fb_user = uid_to_fb_user.get(user.get('id'))
        if fb_user:
            user['firebase_email'] = fb_user.email
            user['firebase_display_name'] = fb_user.display_name
            user['firebase_disabled'] = fb_user.disabled
            continue

        user['firebase_email'] = user.get('email', 'N/A')
        user['firebase_display_name'] = None
        user['firebase_disabled'] = False

    return lookup_failed


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
    start = perf_counter()
    users = get_all_users()
    after_firestore = perf_counter()
    lookup_failed = _enrich_users_with_firebase_auth(users)
    after_auth = perf_counter()

    cached_count = sum(1 for u in users if u.get('id') and u.get('id') in _firebase_auth_cache['users'])
    
    current_app.logger.info(
        "users_list timings: firestore=%.3fs auth=%.3fs total=%.3fs count=%s cached=%s auth_lookup_failed=%s",
        after_firestore - start,
        after_auth - after_firestore,
        after_auth - start,
        len(users),
        cached_count,
        lookup_failed,
    )

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
        achievements_enabled = request.form.get('achievements_enabled') == 'on'

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

            # Flaga eksperymentalna: osiągnięcia
            try:
                set_user_feature_flag(user_id, 'achievements_enabled', achievements_enabled)
                # Jeśli właśnie włączono osiągnięcia – retro‑aktywne przyznanie spełnionych odznak
                if achievements_enabled:
                    try:
                        from .achievements_service import maybe_award_all_for_user
                        maybe_award_all_for_user(user_id)
                    except Exception as _e:
                        current_app.logger.warning(f"Retro-award achievements failed for {user_id}: {_e}")
            except Exception as e:
                current_app.logger.warning(f"Nie udało się zaktualizować flagi osiągnięć: {e}")

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


# =======================================================================
#                       OSIĄGNIĘCIA (EXPERIMENTAL)
# =======================================================================

@admin_bp.route('/users/<user_id>/achievements', methods=['GET', 'POST'])
@quartermaster_required
def user_achievements(user_id):
    """Zarządzanie osiągnięciami użytkownika (tylko ADMIN)."""
    # Podstawowa weryfikacja istnienia użytkownika
    user = get_user_by_uid(user_id)
    if not user:
        flash('Nie znaleziono użytkownika.', 'danger')
        return redirect(url_for('admin.users_list'))

    # Przetwarzanie akcji (POST)
    if request.method == 'POST':
        if not validate_csrf_token():
            return redirect(url_for('admin.user_achievements', user_id=user_id))

        action = request.form.get('action')
        achievement_id = request.form.get('achievement_id', '').strip()

        # Przełączanie flagi funkcji
        if action == 'toggle_feature':
            enable = request.form.get('achievements_enabled') == 'on'
            try:
                set_user_feature_flag(user_id, 'achievements_enabled', enable)
                # Po włączeniu – spróbuj nadać od razu spełnione osiągnięcia
                if enable:
                    try:
                        from .achievements_service import maybe_award_all_for_user
                        maybe_award_all_for_user(user_id)
                    except Exception as _e:
                        current_app.logger.warning(f"Retro-award achievements failed for {user_id}: {_e}")
                flash('Zaktualizowano ustawienie: osiągnięcia.', 'success')
            except Exception as e:
                flash(f'Błąd podczas zapisu ustawienia: {e}', 'danger')
            return redirect(url_for('admin.user_achievements', user_id=user_id))

        # Operacje na osiągnięciach
        valid_ids = set(get_achievements_map().keys())
        if achievement_id and achievement_id in valid_ids:
            try:
                if action == 'grant':
                    add_user_achievement(user_id, achievement_id)
                    flash('Osiągnięcie przyznane.', 'success')
                elif action == 'revoke':
                    remove_user_achievement(user_id, achievement_id)
                    flash('Osiągnięcie odebrane.', 'warning')
            except Exception as e:
                flash(f'Błąd podczas aktualizacji osiągnięcia: {e}', 'danger')
        else:
            if action in ('grant', 'revoke'):
                flash('Nieprawidłowe ID osiągnięcia.', 'danger')

        return redirect(url_for('admin.user_achievements', user_id=user_id))

    # GET – przygotowanie danych do widoku
    achievements_map = get_user_achievements_map(user_id)
    features = user.get('features', {}) or {}
    achievements_list = get_all_achievements()
    return render_template(
        'admin/user_achievements.html',
        user=user,
        achievements=achievements_list,
        achievements_map=achievements_map,
        features=features,
    )


# =======================================================================
#                       OSIĄGNIĘCIA — DEFINICJE (ADMIN)
# =======================================================================

def _slugify(text: str) -> str:
    import re
    text = (text or '').strip().lower()
    # zamień polskie znaki i inne diakrytyki w prosty sposób
    repl = {
        'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z'
    }
    text = ''.join(repl.get(ch, ch) for ch in text)
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = re.sub(r'-{2,}', '-', text).strip('-')
    return text or 'achiev'


@admin_bp.route('/achievements', methods=['GET'])
@admin_required
def achievements_defs_list():
    """Lista definicji osiągnięć (z bazy)."""
    items = get_all_achievements()
    return render_template('admin/achievements_list.html', achievements=items)


@admin_bp.route('/achievements/new', methods=['GET', 'POST'])
@admin_required
def achievements_new():
    """Dodawanie nowej definicji osiągnięcia (z warunkami)."""
    if request.method == 'POST':
        if not validate_csrf_token():
            return redirect(url_for('admin.achievements_new'))

        aid = (request.form.get('id') or '').strip()
        name = (request.form.get('name') or '').strip()
        description = (request.form.get('description') or '').strip()
        icon = (request.form.get('icon') or '').strip() or '🏅'
        enabled = request.form.get('enabled') == 'on'
        secret = request.form.get('secret') == 'on'
        order = request.form.get('order')
        try:
            order = int(order) if order not in (None, '') else None
        except ValueError:
            order = None

        condition_type = (request.form.get('condition_type') or '').strip()
        event = (request.form.get('event') or '').strip()
        threshold = request.form.get('threshold')
        category = (request.form.get('category') or '').strip()
        # Nowe pola dla log_count
        action = (request.form.get('action') or '').strip()
        target_type = (request.form.get('target_type') or '').strip()
        try:
            threshold = int(threshold) if (threshold not in (None, '') and condition_type in ('event_count','item_add_count','item_edit_count','log_count')) else None
        except ValueError:
            threshold = None

        if not name:
            flash('Nazwa osiągnięcia jest wymagana.', 'danger')
            return render_template('admin/achievement_form.html')

        if not aid:
            aid = _slugify(name)

        # Zbuduj definicję z warunkami
        condition = None
        if condition_type == 'event_count':
            if event not in ('report_created', 'loan_created'):
                flash('Dla event_count dozwolone zdarzenia: report_created lub loan_created.', 'danger')
                return render_template('admin/achievement_form.html')
            if threshold is None or threshold <= 0:
                flash('Dla event_count wymagany jest próg (liczba >= 1).', 'danger')
                return render_template('admin/achievement_form.html')
            condition = {
                'type': 'event_count',
                'event': event,
                'threshold': threshold,
            }
        elif condition_type in ('item_add_count', 'item_edit_count'):
            if threshold is None or threshold <= 0:
                flash('Dla liczników dodawania/edycji wymagany jest próg (liczba >= 1).', 'danger')
                return render_template('admin/achievement_form.html')
            condition = {
                'type': condition_type,
                'threshold': threshold,
            }
            if category:
                condition['category'] = category
        elif condition_type == 'log_count':
            if threshold is None or threshold <= 0:
                flash('Dla Liczby logów wymagany jest próg (liczba >= 1).', 'danger')
                return render_template('admin/achievement_form.html')
            condition = {
                'type': 'log_count',
                'threshold': threshold,
            }
            if action:
                condition['action'] = action
            if target_type:
                condition['target_type'] = target_type
            if category:
                condition['category'] = category
        elif condition_type in ('speedy_return', 'help_resolve'):
            # Event informacyjny (może być użyty w przyszłości), ale nie jest wymagany
            condition = {
                'type': condition_type,
                'event': 'loan_return' if condition_type == 'speedy_return' else 'help_resolve'
            }
        else:
            flash('Nieprawidłowy typ warunku.', 'danger')
            return render_template('admin/achievement_form.html')

        data = {
            'id': aid,
            'name': name,
            'description': description,
            'icon': icon,
            'enabled': enabled,
            'secret': secret,
            'order': order if order is not None else 9999,
            'condition': condition,
        }
        try:
            set_achievement_def(aid, data)
            flash('Dodano nowe osiągnięcie.', 'success')
            return redirect(url_for('admin.achievements_defs_list'))
        except Exception as e:
            flash(f'Błąd podczas zapisu osiągnięcia: {e}', 'danger')
            return render_template('admin/achievement_form.html', achievement=data)

    return render_template('admin/achievement_form.html')


@admin_bp.route('/achievements/<achievement_id>/delete', methods=['POST'])
@admin_required
def achievements_delete(achievement_id):
    if not validate_csrf_token():
        return redirect(url_for('admin.achievements_defs_list'))
    try:
        delete_item(COLLECTION_ACHIEVEMENTS, achievement_id)
        flash('Osiągnięcie zostało usunięte.', 'warning')
    except Exception as e:
        flash(f'Nie udało się usunąć osiągnięcia: {e}', 'danger')
    return redirect(url_for('admin.achievements_defs_list'))


@admin_bp.route('/achievements/<achievement_id>/edit', methods=['GET', 'POST'])
@admin_required
def achievements_edit(achievement_id):
    """Edycja istniejącej definicji osiągnięcia."""
    ach_map = get_achievements_map()
    achievement = ach_map.get(achievement_id)
    if not achievement:
        flash('Nie znaleziono osiągnięcia.', 'danger')
        return redirect(url_for('admin.achievements_defs_list'))

    if request.method == 'POST':
        if not validate_csrf_token():
            return redirect(url_for('admin.achievements_edit', achievement_id=achievement_id))

        name = (request.form.get('name') or '').strip()
        description = (request.form.get('description') or '').strip()
        icon = (request.form.get('icon') or '').strip() or (achievement.get('icon') or '🏅')
        enabled = request.form.get('enabled') == 'on'
        secret = request.form.get('secret') == 'on'
        order = request.form.get('order')
        try:
            order = int(order) if order not in (None, '') else (achievement.get('order') or 9999)
        except ValueError:
            order = achievement.get('order') or 9999

        condition_type = (request.form.get('condition_type') or '').strip()
        event = (request.form.get('event') or '').strip()
        threshold = request.form.get('threshold')
        category = (request.form.get('category') or '').strip()
        action = (request.form.get('action') or '').strip()
        target_type = (request.form.get('target_type') or '').strip()
        try:
            threshold = int(threshold) if (threshold not in (None, '') and condition_type in ('event_count','item_add_count','item_edit_count','log_count')) else None
        except ValueError:
            threshold = None

        if not name:
            flash('Nazwa osiągnięcia jest wymagana.', 'danger')
            return render_template('admin/achievement_form.html', achievement=achievement, edit=True)

        condition = None
        if condition_type == 'event_count':
            if event not in ('report_created', 'loan_created'):
                flash('Dla event_count dozwolone zdarzenia: report_created lub loan_created.', 'danger')
                return render_template('admin/achievement_form.html', achievement=achievement, edit=True)
            if threshold is None or threshold <= 0:
                flash('Dla event_count wymagany jest próg (liczba >= 1).', 'danger')
                return render_template('admin/achievement_form.html', achievement=achievement, edit=True)
            condition = {
                'type': 'event_count',
                'event': event,
                'threshold': threshold,
            }
        elif condition_type in ('item_add_count', 'item_edit_count'):
            if threshold is None or threshold <= 0:
                flash('Dla liczników dodawania/edycji wymagany jest próg (liczba >= 1).', 'danger')
                return render_template('admin/achievement_form.html', achievement=achievement, edit=True)
            condition = {
                'type': condition_type,
                'threshold': threshold,
            }
            if category:
                condition['category'] = category
        elif condition_type == 'log_count':
            if threshold is None or threshold <= 0:
                flash('Dla Liczby logów wymagany jest próg (liczba >= 1).', 'danger')
                return render_template('admin/achievement_form.html', achievement=achievement, edit=True)
            condition = {
                'type': 'log_count',
                'threshold': threshold,
            }
            if action:
                condition['action'] = action
            if target_type:
                condition['target_type'] = target_type
            if category:
                condition['category'] = category
        elif condition_type in ('speedy_return', 'help_resolve'):
            condition = {
                'type': condition_type,
                'event': 'loan_return' if condition_type == 'speedy_return' else 'help_resolve'
            }
        else:
            flash('Nieprawidłowy typ warunku.', 'danger')
            return render_template('admin/achievement_form.html', achievement=achievement, edit=True)

        data = {
            'id': achievement_id,  # ID niezmienne podczas edycji
            'name': name,
            'description': description,
            'icon': icon,
            'enabled': enabled,
            'secret': secret,
            'order': order,
            'condition': condition,
        }
        try:
            set_achievement_def(achievement_id, data)
            flash('Zapisano zmiany osiągnięcia.', 'success')
            return redirect(url_for('admin.achievements_defs_list'))
        except Exception as e:
            flash(f'Błąd podczas zapisu: {e}', 'danger')
            return render_template('admin/achievement_form.html', achievement=data, edit=True)

    return render_template('admin/achievement_form.html', achievement=achievement, edit=True)


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
    
    return safe_redirect_back('views.logs_list')


def safe_redirect_back(fallback_endpoint: str):
    """Bezpieczny redirect po akcji POST.

    Jeżeli nagłówek Referer wskazuje ten sam host, wykonaj redirect do niego,
    inaczej zawsze przekieruj do zdefiniowanego endpointu fallback.
    """
    try:
        ref = request.referrer
        if ref:
            ref_url = urlparse(ref)
            # Porównaj hosty (uwzględniając reverse proxy, Flask użyje Host z żądania)
            if ref_url.hostname and ref_url.hostname.lower() == (request.host.split(':')[0]).lower():
                # Utrzymujemy tylko ścieżkę + query, by nie zmieniać schematu/hosta
                target = ref_url.path or '/'
                if ref_url.query:
                    target = f"{target}?{ref_url.query}"
                return redirect(target)
    except Exception as e:
        # W razie jakiegokolwiek błędu logujemy go i przechodzimy do bezpiecznego fallbacku.
        current_app.logger.exception("safe_redirect_back failed while processing referrer")
    return redirect(url_for(fallback_endpoint))


@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    """Zarządzanie ustawieniami aplikacji (np. PIN)."""
    if request.method == 'POST':
        # === listy wyboru ===
        owners_raw = (request.form.get('owners') or '').strip()
        magazyny_raw = (request.form.get('magazyny_names') or '').strip()

        pin = request.form.get('view_pin')
        auto_rotate = request.form.get('pin_auto_rotate') == 'on'
        rotate_hours = request.form.get('pin_rotate_hours', '').strip()
        next_rotate_at_raw = (request.form.get('pin_next_rotate_at') or '').strip()

        # Opcjonalnie: walidacja tokena CSRF, jeśli admin go używa (widzę że admin.py go używa)
        if not validate_csrf_token():
             return redirect(url_for('admin.settings'))

        update_data = {'pin_auto_rotate': auto_rotate}

        # Validate and set rotation hours - always set it even if empty (use default)
        if not rotate_hours:
            update_data['pin_rotate_hours'] = 24  # Default value
        else:
            try:
                hours = int(rotate_hours)
                if hours < 1 or hours > 720:  # Between 1 hour and 30 days
                    flash('Interwał rotacji musi być między 1 a 720 godzin (30 dni).', 'danger')
                    return redirect(url_for('admin.settings'))
                update_data['pin_rotate_hours'] = hours
            except ValueError:
                flash('Interwał rotacji musi być liczbą całkowitą.', 'danger')
                return redirect(url_for('admin.settings'))
        
        # Optional: ustaw ręcznie termin następnej rotacji (datetime-local)
        if next_rotate_at_raw:
            try:
                # datetime-local zwraca np. 2026-01-24T14:30
                # Zapisujemy jako ISO string; rotate_pin_if_due umie go sparsować.
                dt = datetime.fromisoformat(next_rotate_at_raw)
                update_data['pin_next_rotate_at'] = dt.isoformat()
            except Exception:
                flash('Nieprawidłowy format daty/godziny następnej rotacji PIN.', 'danger')
                return redirect(url_for('admin.settings'))
        else:
            # jeśli puste - usuń ustawienie, automat wróci do last_rotate + interwał
            update_data['pin_next_rotate_at'] = None

        if pin:
            if not pin.isdigit() or len(pin) != 6:
                flash('PIN musi składać się z 6 cyfr.', 'danger')
                return redirect(url_for('admin.settings'))
            update_data['view_pin'] = pin
            from .db_firestore import _warsaw_now
            now = _warsaw_now()
            update_data['pin_last_rotate'] = now
            # Jeżeli admin zmienia PIN ręcznie, a auto-rotate jest włączone,
            # to ustawiamy kolejny termin wg interwału (automat przejmuje).
            try:
                rh = int(update_data.get('pin_rotate_hours', 24) or 24)
            except Exception:
                rh = 24
            if auto_rotate:
                update_data['pin_next_rotate_at'] = (now + timedelta(hours=rh)).isoformat()

        update_config(**update_data)

        # Zapis list: jedna wartość na linię
        if owners_raw:
            owners_list = [l.strip() for l in owners_raw.splitlines() if l.strip()]
            update_list_setting('owners', owners_list)
        if magazyny_raw:
            magazyny_list = [l.strip() for l in magazyny_raw.splitlines() if l.strip()]
            update_list_setting('magazyny_names', magazyny_list)

        flash('Ustawienia zostały zapisane.', 'success')
        return redirect(url_for('admin.settings'))

    rotate_pin_if_due()
    config = get_config()
    owners = get_list_setting('owners')
    magazyny_names = get_list_setting('magazyny_names')
    return render_template('admin/settings.html', config=config, owners=owners, magazyny_names=magazyny_names)

