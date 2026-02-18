from . import get_firestore_client
from google.cloud import firestore

from .db_firestore import _warsaw_now

COLLECTION_USERS = 'users'

def _get_doc_data(doc):
    """Pomocnicza funkcja do konwersji dokumentu Firestore na słownik z ID."""
    if not doc.exists:
        return None
    data = doc.to_dict()
    data['id'] = doc.id
    return data

def get_user_by_uid(uid: str):
    """Pobiera użytkownika po Firebase UID."""
    db = get_firestore_client()
    doc = db.collection(COLLECTION_USERS).document(uid).get()
    return _get_doc_data(doc)

def get_user_by_email(email: str):
    """Pobiera użytkownika po adresie email."""
    db = get_firestore_client()
    query = db.collection(COLLECTION_USERS).where(filter=firestore.FieldFilter('email', '==', email)).limit(1)
    docs = list(query.stream())
    if docs:
        return _get_doc_data(docs[0])
    return None

def get_user_by_google_id(google_id: str):
    """Pobiera użytkownika po Google ID."""
    db = get_firestore_client()
    query = db.collection(COLLECTION_USERS).where(filter=firestore.FieldFilter('google_id', '==', google_id)).limit(1)
    docs = list(query.stream())
    if docs:
        return _get_doc_data(docs[0])
    return None

def get_user_by_microsoft_id(microsoft_id: str):
    """Pobiera użytkownika po Microsoft ID."""
    db = get_firestore_client()
    query = db.collection(COLLECTION_USERS).where(filter=firestore.FieldFilter('microsoft_id', '==', microsoft_id)).limit(1)
    docs = list(query.stream())
    if docs:
        return _get_doc_data(docs[0])
    return None

def get_user_by_authentik_id(authentik_id: str):
    """Pobiera użytkownika po Authentik ID."""
    db = get_firestore_client()
    query = db.collection(COLLECTION_USERS).where(filter=firestore.FieldFilter('authentik_id', '==', authentik_id)).limit(1)
    docs = list(query.stream())
    if docs:
        return _get_doc_data(docs[0])
    return None

def get_all_users():
    """Pobiera wszystkich użytkowników."""
    db = get_firestore_client()
    query = db.collection(COLLECTION_USERS).order_by('email', direction=firestore.Query.ASCENDING)
    return [_get_doc_data(doc) for doc in query.stream()]

def create_user(uid: str, email: str, is_admin: bool = False, role: str = 'reporter', active: bool = True, first_name: str = None, last_name: str = None):
    """Tworzy nowy dokument użytkownika w Firestore."""
    db = get_firestore_client()
    user_data = {
        'email': email,
        'is_admin': is_admin,
        'role': role,
        'active': active,
        'first_name': first_name,
        'last_name': last_name,
        'google_id': None,
        'microsoft_id': None,
        'authentik_id': None,
        'created_at': _warsaw_now(),
        'updated_at': _warsaw_now()
    }
    db.collection(COLLECTION_USERS).document(uid).set(user_data)
    return uid

def update_user(uid: str, **kwargs):
    """Aktualizuje dane użytkownika."""
    db = get_firestore_client()
    kwargs['updated_at'] = _warsaw_now()
    db.collection(COLLECTION_USERS).document(uid).update(kwargs)

def link_google_account(uid: str, google_id: str):
    """Łączy konto użytkownika z kontem Google."""
    update_user(uid, google_id=google_id)

def unlink_google_account(uid: str):
    """Rozłącza konto użytkownika z kontem Google."""
    update_user(uid, google_id=None)

def link_microsoft_account(uid: str, microsoft_id: str):
    """Łączy konto użytkownika z kontem Microsoft."""
    update_user(uid, microsoft_id=microsoft_id)

def unlink_microsoft_account(uid: str):
    """Rozłącza konto użytkownika z kontem Microsoft."""
    update_user(uid, microsoft_id=None)

def link_authentik_account(uid: str, authentik_id: str):
    """Łączy konto użytkownika z kontem Authentik."""
    update_user(uid, authentik_id=authentik_id)

def unlink_authentik_account(uid: str):
    """Rozłącza konto użytkownika z kontem Authentik."""
    update_user(uid, authentik_id=None)

def set_user_active_status(uid: str, active: bool):
    """Ustawia status aktywności użytkownika."""
    update_user(uid, active=active)

def set_user_admin_status(uid: str, is_admin: bool):
    """Ustawia status administratora użytkownika."""
    update_user(uid, is_admin=is_admin)

def update_user_email(uid: str, new_email: str):
    """Aktualizuje email użytkownika w Firestore."""
    update_user(uid, email=new_email)

def update_user_name(uid: str, first_name: str = None, last_name: str = None):
    """Aktualizuje imię i nazwisko użytkownika w Firestore."""
    update_data = {}
    if first_name is not None:
        update_data['first_name'] = first_name
    if last_name is not None:
        update_data['last_name'] = last_name
    if update_data:
        update_user(uid, **update_data)

def delete_user(uid: str):
    """Usuwa użytkownika z Firestore."""
    db = get_firestore_client()
    db.collection(COLLECTION_USERS).document(uid).delete()

def sync_users_from_firebase_auth():
    """
    Synchronizuje użytkowników z Firebase Auth do Firestore.
    Usuwa użytkowników z Firestore, którzy nie istnieją w Firebase Auth.
    Dodaje użytkowników z Firebase Auth, którzy nie istnieją w Firestore.
    """
    from firebase_admin import auth as firebase_auth

    # Pobierz wszystkich użytkowników z Firebase Auth
    firebase_users = {}
    page = firebase_auth.list_users()
    while page:
        for user in page.users:
            firebase_users[user.uid] = user
        page = page.get_next_page()

    # Pobierz wszystkich użytkowników z Firestore
    firestore_users = get_all_users()

    deleted_count = 0
    added_count = 0

    # Usuń użytkowników z Firestore, którzy nie istnieją w Firebase Auth
    for fs_user in firestore_users:
        if fs_user['id'] not in firebase_users:
            delete_user(fs_user['id'])
            deleted_count += 1

    # Dodaj użytkowników z Firebase Auth, którzy nie istnieją w Firestore
    for uid, fb_user in firebase_users.items():
        if not get_user_by_uid(uid):
            # Sprawdź custom claims dla is_admin
            user_record = firebase_auth.get_user(uid)
            is_admin = user_record.custom_claims.get('admin', False) if user_record.custom_claims else False
            role = 'admin' if is_admin else 'reporter'
            create_user(uid, fb_user.email, is_admin=is_admin, role=role, active=not fb_user.disabled)
            added_count += 1

    return deleted_count, added_count
