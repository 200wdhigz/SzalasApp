# python
# file: src/oauth.py

from flask import Blueprint, request, redirect, url_for, flash, session, render_template
import os
import secrets
from authlib.integrations.requests_client import OAuth2Session
from firebase_admin import auth as firebase_auth

from .db_users import (
    get_user_by_google_id, get_user_by_microsoft_id, get_user_by_uid,
    create_user, link_google_account, link_microsoft_account,
    unlink_google_account, unlink_microsoft_account
)
from .auth import login_required

oauth_bp = Blueprint('oauth', __name__, url_prefix='/auth')

# OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
GOOGLE_AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v2/userinfo"

MICROSOFT_CLIENT_ID = os.getenv('MICROSOFT_CLIENT_ID')
MICROSOFT_CLIENT_SECRET = os.getenv('MICROSOFT_CLIENT_SECRET')
MICROSOFT_TENANT_ID = os.getenv('MICROSOFT_TENANT_ID', 'common')
MICROSOFT_AUTHORIZATION_ENDPOINT = f"https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}/oauth2/v2.0/authorize"
MICROSOFT_TOKEN_ENDPOINT = f"https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}/oauth2/v2.0/token"
MICROSOFT_USERINFO_ENDPOINT = "https://graph.microsoft.com/v1.0/me"

ALLOWED_MICROSOFT_DOMAINS = ['zhp.net.pl', 'zhp.pl']


def get_redirect_uri(provider):
    """Generuje redirect URI dla danego providera."""
    base_url = os.getenv('BASE_URL', 'http://localhost:5000')
    return f"{base_url}/auth/{provider}/callback"


# =======================================================================
#                       GOOGLE OAUTH
# =======================================================================

@oauth_bp.route('/google')
def google_login():
    """Inicjuje proces logowania przez Google OAuth."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        flash('Google OAuth nie jest skonfigurowany.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Generuj state dla bezpieczeństwa CSRF
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state
    
    # Zapisz, czy to jest proces linkowania (użytkownik już zalogowany)
    if 'user_id' in session:
        session['oauth_linking'] = True
    
    redirect_uri = get_redirect_uri('google')
    
    client = OAuth2Session(
        GOOGLE_CLIENT_ID,
        redirect_uri=redirect_uri,
        scope='openid email profile'
    )
    
    authorization_url, state = client.create_authorization_url(
        GOOGLE_AUTHORIZATION_ENDPOINT,
        state=state
    )
    
    return redirect(authorization_url)


@oauth_bp.route('/google/callback')
def google_callback():
    """Obsługuje callback z Google OAuth."""
    # Sprawdź state dla ochrony CSRF
    state = request.args.get('state')
    if state != session.get('oauth_state'):
        flash('Błąd weryfikacji stanu OAuth.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Usuń state z sesji
    session.pop('oauth_state', None)
    
    code = request.args.get('code')
    if not code:
        flash('Błąd podczas logowania przez Google.', 'danger')
        return redirect(url_for('auth.login'))
    
    redirect_uri = get_redirect_uri('google')
    
    try:
        client = OAuth2Session(
            GOOGLE_CLIENT_ID,
            redirect_uri=redirect_uri
        )
        
        token = client.fetch_token(
            GOOGLE_TOKEN_ENDPOINT,
            code=code,
            client_secret=GOOGLE_CLIENT_SECRET
        )
        
        # Pobierz informacje o użytkowniku
        resp = client.get(GOOGLE_USERINFO_ENDPOINT)
        user_info = resp.json()
        
        google_id = user_info.get('id')
        email = user_info.get('email')
        
        if not google_id or not email:
            flash('Nie udało się pobrać informacji o użytkowniku z Google.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Sprawdź, czy to proces linkowania
        if session.get('oauth_linking'):
            session.pop('oauth_linking', None)
            current_user_id = session.get('user_id')
            
            # Sprawdź, czy to konto Google nie jest już powiązane z innym użytkownikiem
            existing_user = get_user_by_google_id(google_id)
            if existing_user and existing_user['id'] != current_user_id:
                flash('To konto Google jest już powiązane z innym użytkownikiem.', 'danger')
                return redirect(url_for('oauth.account'))
            
            # Powiąż konto Google z aktualnym użytkownikiem
            link_google_account(current_user_id, google_id)
            flash('Konto Google zostało pomyślnie powiązane.', 'success')
            return redirect(url_for('oauth.account'))
        
        # Proces logowania
        # Sprawdź, czy użytkownik z tym Google ID już istnieje
        user = get_user_by_google_id(google_id)
        
        if user:
            # Sprawdź, czy konto jest aktywne
            if not user.get('active', True):
                flash('Twoje konto zostało wyłączone. Skontaktuj się z administratorem.', 'danger')
                return redirect(url_for('auth.login'))
            
            # Zaloguj użytkownika
            session['user_id'] = user['id']
            session['is_admin'] = user.get('is_admin', False)
            flash('Pomyślnie zalogowano przez Google!', 'success')
            return redirect(url_for('views.sprzet_list'))
        else:
            # Nowy użytkownik - w tym systemie tylko admin może tworzyć użytkowników
            flash('Nie znaleziono konta powiązanego z tym kontem Google. Poproś administratora o utworzenie konta.', 'warning')
            return redirect(url_for('auth.login'))
    
    except Exception as e:
        flash(f'Wystąpił błąd podczas logowania przez Google: {str(e)}', 'danger')
        return redirect(url_for('auth.login'))


# =======================================================================
#                       MICROSOFT OAUTH
# =======================================================================

@oauth_bp.route('/microsoft')
def microsoft_login():
    """Inicjuje proces logowania przez Microsoft OAuth."""
    if not MICROSOFT_CLIENT_ID or not MICROSOFT_CLIENT_SECRET:
        flash('Microsoft OAuth nie jest skonfigurowany.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Generuj state dla bezpieczeństwa CSRF
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state
    
    # Zapisz, czy to jest proces linkowania
    if 'user_id' in session:
        session['oauth_linking'] = True
    
    redirect_uri = get_redirect_uri('microsoft')
    
    client = OAuth2Session(
        MICROSOFT_CLIENT_ID,
        redirect_uri=redirect_uri,
        scope='openid email profile User.Read'
    )
    
    authorization_url, state = client.create_authorization_url(
        MICROSOFT_AUTHORIZATION_ENDPOINT,
        state=state
    )
    
    return redirect(authorization_url)


@oauth_bp.route('/microsoft/callback')
def microsoft_callback():
    """Obsługuje callback z Microsoft OAuth."""
    # Sprawdź state dla ochrony CSRF
    state = request.args.get('state')
    if state != session.get('oauth_state'):
        flash('Błąd weryfikacji stanu OAuth.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Usuń state z sesji
    session.pop('oauth_state', None)
    
    code = request.args.get('code')
    if not code:
        flash('Błąd podczas logowania przez Microsoft.', 'danger')
        return redirect(url_for('auth.login'))
    
    redirect_uri = get_redirect_uri('microsoft')
    
    try:
        client = OAuth2Session(
            MICROSOFT_CLIENT_ID,
            redirect_uri=redirect_uri
        )
        
        token = client.fetch_token(
            MICROSOFT_TOKEN_ENDPOINT,
            code=code,
            client_secret=MICROSOFT_CLIENT_SECRET
        )
        
        # Pobierz informacje o użytkowniku
        resp = client.get(MICROSOFT_USERINFO_ENDPOINT)
        user_info = resp.json()
        
        microsoft_id = user_info.get('id')
        email = user_info.get('mail') or user_info.get('userPrincipalName')
        
        if not microsoft_id or not email:
            flash('Nie udało się pobrać informacji o użytkowniku z Microsoft.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Sprawdź domenę email (tylko zhp.net.pl i zhp.pl)
        email_domain = email.split('@')[-1].lower()
        if email_domain not in ALLOWED_MICROSOFT_DOMAINS:
            flash(f'Tylko konta z domen {", ".join(ALLOWED_MICROSOFT_DOMAINS)} są dozwolone.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Sprawdź, czy to proces linkowania
        if session.get('oauth_linking'):
            session.pop('oauth_linking', None)
            current_user_id = session.get('user_id')
            
            # Sprawdź, czy to konto Microsoft nie jest już powiązane z innym użytkownikiem
            existing_user = get_user_by_microsoft_id(microsoft_id)
            if existing_user and existing_user['id'] != current_user_id:
                flash('To konto Microsoft jest już powiązane z innym użytkownikiem.', 'danger')
                return redirect(url_for('oauth.account'))
            
            # Powiąż konto Microsoft z aktualnym użytkownikiem
            link_microsoft_account(current_user_id, microsoft_id)
            flash('Konto Microsoft zostało pomyślnie powiązane.', 'success')
            return redirect(url_for('oauth.account'))
        
        # Proces logowania
        # Sprawdź, czy użytkownik z tym Microsoft ID już istnieje
        user = get_user_by_microsoft_id(microsoft_id)
        
        if user:
            # Sprawdź, czy konto jest aktywne
            if not user.get('active', True):
                flash('Twoje konto zostało wyłączone. Skontaktuj się z administratorem.', 'danger')
                return redirect(url_for('auth.login'))
            
            # Zaloguj użytkownika
            session['user_id'] = user['id']
            session['is_admin'] = user.get('is_admin', False)
            flash('Pomyślnie zalogowano przez Microsoft!', 'success')
            return redirect(url_for('views.sprzet_list'))
        else:
            # Nowy użytkownik - w tym systemie tylko admin może tworzyć użytkowników
            flash('Nie znaleziono konta powiązanego z tym kontem Microsoft. Poproś administratora o utworzenie konta.', 'warning')
            return redirect(url_for('auth.login'))
    
    except Exception as e:
        flash(f'Wystąpił błąd podczas logowania przez Microsoft: {str(e)}', 'danger')
        return redirect(url_for('auth.login'))


# =======================================================================
#                       ACCOUNT MANAGEMENT
# =======================================================================

@oauth_bp.route('/account')
@login_required
def account():
    """Wyświetla panel zarządzania kontem użytkownika."""
    user_id = session.get('user_id')
    user = get_user_by_uid(user_id)
    
    if not user:
        flash('Nie znaleziono danych użytkownika.', 'danger')
        return redirect(url_for('views.sprzet_list'))
    
    return render_template('account.html', user=user)


@oauth_bp.route('/account/unlink/google', methods=['POST'])
@login_required
def unlink_google():
    """Rozłącza konto Google od konta użytkownika."""
    user_id = session.get('user_id')
    user = get_user_by_uid(user_id)
    
    if not user or not user.get('google_id'):
        flash('Brak powiązanego konta Google.', 'warning')
        return redirect(url_for('oauth.account'))
    
    unlink_google_account(user_id)
    flash('Konto Google zostało rozłączone.', 'success')
    return redirect(url_for('oauth.account'))


@oauth_bp.route('/account/unlink/microsoft', methods=['POST'])
@login_required
def unlink_microsoft():
    """Rozłącza konto Microsoft od konta użytkownika."""
    user_id = session.get('user_id')
    user = get_user_by_uid(user_id)
    
    if not user or not user.get('microsoft_id'):
        flash('Brak powiązanego konta Microsoft.', 'warning')
        return redirect(url_for('oauth.account'))
    
    unlink_microsoft_account(user_id)
    flash('Konto Microsoft zostało rozłączone.', 'success')
    return redirect(url_for('oauth.account'))
