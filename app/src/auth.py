from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
import requests
import secrets
from firebase_admin import auth
from datetime import timedelta, datetime
from urllib.parse import urlparse

from . import GOOGLE_API_KEY
from .db_users import get_user_by_uid, create_user
from .db_firestore import _warsaw_now, get_config, update_config  # re-export dla testów i spójnego użycia czasu

auth_bp = Blueprint('auth', __name__, url_prefix='/')

def login_required(f):
    """Dekorator do sprawdzania, czy użytkownik jest zalogowany (lub zalogowany PINem)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session and not session.get('is_pin_authenticated'):
            # flash('Musisz się zalogować lub podać PIN, aby uzyskać dostęp.', 'danger')
            return redirect(url_for('auth.pin_login', next=request.full_path))
        return f(*args, **kwargs)
    return decorated_function

def full_login_required(f):
    """Dekorator do sprawdzania, czy użytkownik jest zalogowany pełnym kontem (nie PINem)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Ta strona wymaga pełnego logowania.', 'warning')
            if session.get('is_pin_authenticated'):
                return redirect(url_for('views.home'))
            return redirect(url_for('auth.login', next=request.full_path))
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

def pin_restricted_required(f):
    """Dekorator: dostęp tylko dla pełnego logowania (user_id).

    Użytkownik zalogowany PINem jest uwierzytelniony (login_required), ale ma ograniczony dostęp.
    Dla widoków listowych/administracyjnych blokujemy PIN i przekierowujemy na home.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Najpierw wymuś jakąkolwiek autoryzację (login lub PIN), inaczej daj PIN login.
        if 'user_id' not in session and not session.get('is_pin_authenticated'):
            return redirect(url_for('auth.pin_login', next=request.full_path))

        # Jeśli jest PIN, ale nie ma pełnego user_id => blok.
        if session.get('is_pin_authenticated') and 'user_id' not in session:
            flash('Ta strona wymaga pełnego logowania.', 'warning')
            return redirect(url_for('views.home'))

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
    session.pop('is_pin_authenticated', None)
    flash('Wylogowano pomyślnie.', 'info')
    return redirect(url_for('views.home'))

def _warsaw_tz():
    """Strefa Europe/Warsaw – nigdy None (fallback na astimezone)."""
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo('Europe/Warsaw')
    except Exception:
        pass
    n = _warsaw_now()
    if getattr(n, 'tzinfo', None) is not None:
        return n.tzinfo
    return datetime.now().astimezone().tzinfo


def get_current_pin():
    """Zwraca aktualny PIN z configu. Tworzy go tylko gdy brak. Nigdy nie obraca."""
    config = get_config()
    pin = config.get('view_pin')
    if not pin:
        rotate_hours = config.get('pin_rotate_hours', 24)
        pin = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        now = _warsaw_now()
        update_config(
            view_pin=pin,
            pin_last_rotate=now,
            pin_next_rotate_at=(now + timedelta(hours=int(rotate_hours) if rotate_hours else 24)),
        )
    return pin


def rotate_pin_if_due():
    """Jeśli auto_rotate włączone i minął termin – generuje nowy PIN i zapisuje w configu.
    Wywoływane przy GET /health, nigdy przy logowaniu PIN."""
    config = get_config()
    if not config.get('pin_auto_rotate'):
        return
    pin = config.get('view_pin')
    if not pin:
        return
    last_rotate = config.get('pin_last_rotate')
    next_rotate_at = config.get('pin_next_rotate_at')
    rotate_hours = config.get('pin_rotate_hours', 24)

    wtz = _warsaw_tz()
    now = _warsaw_now()
    if now.tzinfo is None:
        now = now.replace(tzinfo=wtz)
    else:
        now = now.astimezone(wtz)

    def _to_dt(val):
        if not val:
            return None
        if hasattr(val, 'tzinfo'):
            return val
        if isinstance(val, str):
            try:
                return datetime.fromisoformat(val)
            except Exception:
                return None
        return None

    def _to_warsaw_aware(dt):
        if dt is None or wtz is None:
            return None
        if hasattr(dt, 'timestamp'):
            try:
                ts = dt.timestamp()
                tz = getattr(dt, 'tzinfo', None)
                dt = datetime.fromtimestamp(ts, tz=tz) if tz else datetime.fromtimestamp(ts, tz=wtz)
            except Exception:
                pass
        if getattr(dt, 'tzinfo', None) is None:
            return dt.replace(tzinfo=wtz)
        return dt.astimezone(wtz)

    last_rotate_dt = _to_warsaw_aware(_to_dt(last_rotate))
    next_rotate_dt = _to_warsaw_aware(_to_dt(next_rotate_at))

    should_rotate = False
    if next_rotate_dt and now >= next_rotate_dt:
        should_rotate = True
    elif last_rotate_dt:
        hrs = int(rotate_hours) if rotate_hours else 24
        if now - last_rotate_dt > timedelta(hours=hrs):
            should_rotate = True

    if should_rotate:
        pin = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        update_config(
            view_pin=pin,
            pin_last_rotate=now,
            pin_next_rotate_at=(now + timedelta(hours=int(rotate_hours) if rotate_hours else 24)),
        )

@auth_bp.route('/pin', methods=['GET', 'POST'])
def pin_login():
    if request.method == 'POST':
        entered_pin = request.form.get('pin')
        actual_pin = get_current_pin()
        
        if entered_pin == actual_pin:
            session['is_pin_authenticated'] = True
            # Nadajemy podstawowe uprawnienia "gościa z pinem"
            session['user_role'] = 'reporter'
            session['user_name'] = 'Gość (PIN)'
            flash('Dostęp przyznany za pomocą PIN.', 'success')
            next_url = request.args.get('next')
            normalized_next = None
            if next_url:
                # Normalizuj i sprawdź, czy URL jest względny (bez hosta i schematu)
                candidate = next_url.replace('\\', '/').strip()
                parsed = urlparse(candidate)

                # Bezpieczeństwo:
                # - blokujemy schemat/host
                # - blokujemy URL typu //evil.com (protocol-relative)
                # - wymagamy, żeby ścieżka była absolutna i w allowliście
                if not parsed.scheme and not parsed.netloc and candidate.startswith('/') and not candidate.startswith('//'):
                    low = candidate.lower()
                    if low.startswith('/sprzet/') or low.startswith('/usterka/'):
                        normalized_next = candidate

            safe_next = normalized_next or url_for('views.sprzet_list')
            return redirect(safe_next)
        else:
            flash('Nieprawidłowy kod PIN.', 'danger')
            
    return render_template('pin_login.html')
