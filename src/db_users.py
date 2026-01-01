# python
# file: src/db_users.py

from . import get_firestore_client
from google.cloud import firestore
from datetime import datetime

# NAZWY KOLEKCJI
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

def get_all_users():
    """Pobiera wszystkich użytkowników."""
    db = get_firestore_client()
    query = db.collection(COLLECTION_USERS).order_by('email', direction=firestore.Query.ASCENDING)
    return [_get_doc_data(doc) for doc in query.stream()]

def create_user(uid: str, email: str, is_admin: bool = False, active: bool = True):
    """Tworzy nowy dokument użytkownika w Firestore."""
    db = get_firestore_client()
    user_data = {
        'email': email,
        'is_admin': is_admin,
        'active': active,
        'google_id': None,
        'microsoft_id': None,
        'created_at': firestore.SERVER_TIMESTAMP,
        'updated_at': firestore.SERVER_TIMESTAMP
    }
    db.collection(COLLECTION_USERS).document(uid).set(user_data)
    return uid

def update_user(uid: str, **kwargs):
    """Aktualizuje dane użytkownika."""
    db = get_firestore_client()
    kwargs['updated_at'] = firestore.SERVER_TIMESTAMP
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

def set_user_active_status(uid: str, active: bool):
    """Ustawia status aktywności użytkownika."""
    update_user(uid, active=active)

def set_user_admin_status(uid: str, is_admin: bool):
    """Ustawia status administratora użytkownika."""
    update_user(uid, is_admin=is_admin)
