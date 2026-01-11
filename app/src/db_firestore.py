from . import get_firestore_client
from google.cloud import firestore

COLLECTION_SPRZET = 'sprzet'
COLLECTION_USTERKI = 'usterki'
COLLECTION_LOGS = 'logs'
COLLECTION_WYPOZYCZENIA = 'wypozyczenia'

CATEGORIES = {
    'MAGAZYN': 'magazyn',
    'POLKA': 'polka_skrzynia',
    'NAMIOT': 'namiot',
    'PRZEDMIOT': 'przedmiot',
    'ZELASTWO': 'zelastwo',
    'KANADYJKI': 'kanadyjki'
}

MAGAZYNY_NAMES = [
    'Esperanto',
    'Obozowa/magazynek',
    'Obozowa/skrzynie',
    'Obozowa/piwnica',
    'Leśniczy/strych',
    'Leśniczy/schody',
    'Leśniczy/magazynek'
]

def _warsaw_now():
    """Zwraca bieżący czas lokalny dla Polski (Europe/Warsaw) jako datetime timezone-aware."""
    from datetime import datetime
    try:
        from zoneinfo import ZoneInfo  # py3.9+
        tz = ZoneInfo('Europe/Warsaw')
    except Exception:
        # Fallback gdyby zoneinfo nie było dostępne
        tz = None
    if tz is None:
        # lokalny czas systemu
        return datetime.now().astimezone()
    return datetime.now(tz)

def add_log(user_id, action, target_type, target_id, details=None, before=None, after=None):
    """Zapisuje log akcji użytkownika.

    Uwaga: zapisujemy czas lokalny (Warszawa) zamiast timestampu serwera Firestore,
    żeby użytkownicy widzieli spójne godziny niezależnie od strefy serwera.
    """
    db = get_firestore_client()
    log_data = {
        'user_id': user_id,
        'action': action,
        'target_type': target_type,
        'target_id': target_id,
        'details': details,
        'before': before,
        'after': after,
        'timestamp': _warsaw_now(),
    }
    db.collection(COLLECTION_LOGS).add(log_data)

def get_logs_by_user(user_id, limit=None, offset=None):
    """Pobiera logi dla konkretnego użytkownika."""
    db = get_firestore_client()
    query = db.collection(COLLECTION_LOGS).where(filter=firestore.FieldFilter('user_id', '==', user_id)).order_by('timestamp', direction=firestore.Query.DESCENDING)
    if limit:
        query = query.limit(limit)
    if offset:
        query = query.offset(offset)
    return [_get_doc_data(doc) for doc in query.stream()]

def get_logs_by_target(target_id, limit=None, offset=None):
    """Pobiera logi dla konkretnego obiektu (sprzętu lub usterki)."""
    db = get_firestore_client()
    query = db.collection(COLLECTION_LOGS).where(filter=firestore.FieldFilter('target_id', '==', target_id)).order_by('timestamp', direction=firestore.Query.DESCENDING)
    if limit:
        query = query.limit(limit)
    if offset:
        query = query.offset(offset)
    return [_get_doc_data(doc) for doc in query.stream()]

def get_all_logs(limit=None, offset=None):
    """Pobiera wszystkie logi (dla admina/zalogowanych)."""
    db = get_firestore_client()
    query = db.collection(COLLECTION_LOGS).order_by('timestamp', direction=firestore.Query.DESCENDING)
    if limit:
        query = query.limit(limit)
    if offset:
        query = query.offset(offset)
    return [_get_doc_data(doc) for doc in query.stream()]

def get_logs_count(user_id=None, target_id=None):
    """Zwraca liczbę logów, opcjonalnie filtrowaną."""
    db = get_firestore_client()
    query = db.collection(COLLECTION_LOGS)
    if user_id:
        query = query.where(filter=firestore.FieldFilter('user_id', '==', user_id))
    if target_id:
        query = query.where(filter=firestore.FieldFilter('target_id', '==', target_id))

    # Uwaga: count() w Firestore jest bardzo szybkie i tanie
    return query.count().get()[0][0].value

def get_log(log_id):
    """Pobiera pojedynczy log."""
    db = get_firestore_client()
    doc = db.collection(COLLECTION_LOGS).document(log_id).get()
    return _get_doc_data(doc)

def restore_item(log_id, user_id):
    """Przywraca stan obiektu z loga."""
    log = get_log(log_id)
    if not log:
        return False, "Nie znaleziono loga."

    target_type = log.get('target_type')
    target_id = log.get('target_id')
    action = log.get('action')

    # Walidacja: sprawdź czy log zawiera wymagane pola target_type i target_id
    if not target_type or not target_id:
        return False, "Log nie zawiera wymaganych informacji o celu przywrócenia."

    collection = COLLECTION_SPRZET if target_type == 'sprzet' else COLLECTION_USTERKI

    if action == 'add':
        # Cofnięcie dodania = usunięcie elementu
        current_item = get_item(collection, target_id)
        if not current_item:
            return False, f"Nie można cofnąć dodania, ponieważ obiekt {target_type} {target_id} już nie istnieje."

        delete_item(collection, target_id)
        add_log(user_id, 'restore_delete', target_type, target_id, details={'restored_from_log_id': log_id})
        return True, f"Cofnięto dodanie {target_type} {target_id} (element został usunięty)."

    if not log.get('before'):
        return False, "Nie znaleziono danych do przywrócenia."

    before_data = log.get('before')

    # Walidacja: sprawdź czy target_type jest poprawny
    valid_types = [COLLECTION_SPRZET, COLLECTION_USTERKI]
    if target_type not in valid_types:
        return False, f"Nieprawidłowy typ obiektu w logu: {target_type}."

    # Usuwamy pola, które nie powinny być nadpisywane podczas przywracania (np. id, timestampy jeśli są)
    data_to_restore = {k: v for k, v in before_data.items() if k not in ['id']}

    collection = COLLECTION_SPRZET if target_type == 'sprzet' else COLLECTION_USTERKI

    # Pobierz aktualny stan przed przywróceniem (do logowania)
    current_item = get_item(collection, target_id)

    # Walidacja: sprawdź czy obiekt docelowy istnieje
    if not current_item:
        return False, f"Nie znaleziono obiektu {target_type} o ID {target_id}."

    current_data = {k: v for k, v in current_item.items() if k not in ['id', 'zdjecia_lista_url']}

    # Przywróć dane
    set_item(collection, target_id, data_to_restore)

    # Zaloguj akcję przywrócenia
    add_log(user_id, 'restore', target_type, target_id, before=current_data, after=data_to_restore, details={'restored_from_log_id': log_id})

    return True, f"Przywrócono stan {target_type} {target_id}."

def _get_doc_data(doc):
    """Pomocnicza funkcja do konwersji dokumentu Firestore na słownik z ID i formatowaniem daty."""
    if not doc.exists:
        return None
    data = doc.to_dict()
    data['id'] = doc.id
    if 'data_zgloszenia' in data and hasattr(data['data_zgloszenia'], 'strftime'):
        data['data_zgloszenia'] = data['data_zgloszenia'].strftime('%Y-%m-%d %H:%M')
    if 'timestamp' in data and hasattr(data['timestamp'], 'strftime'):
        data['timestamp'] = data['timestamp'].strftime('%Y-%m-%d %H:%M')
    return data

def get_item(collection: str, item_id: str):
    """Pobiera pojedynczy element z dowolnej kolekcji."""
    db = get_firestore_client()
    doc = db.collection(collection).document(item_id).get()
    return _get_doc_data(doc)

def get_all_items(collection: str, order_by=None, direction=firestore.Query.DESCENDING):
    """Pobiera wszystkie elementy z kolekcji z opcjonalnym sortowaniem."""
    db = get_firestore_client()
    query = db.collection(collection)
    if order_by:
        query = query.order_by(order_by, direction=direction)
    return [_get_doc_data(doc) for doc in query.stream()]

def get_items_by_filters(collection: str, filters: list, order_by=None, direction=firestore.Query.DESCENDING):
    """Pobiera elementy z kolekcji na podstawie wielu filtrów."""
    db = get_firestore_client()
    query = db.collection(collection)
    for field, op, val in filters:
        query = query.where(filter=firestore.FieldFilter(field, op, val))
    if order_by:
        query = query.order_by(order_by, direction=direction)
    return [_get_doc_data(doc) for doc in query.stream()]

def get_items_by_filter(collection: str, field: str, operator: str, value: str, order_by=None, direction=firestore.Query.DESCENDING):
    """Pobiera elementy z kolekcji na podstawie filtra z opcjonalnym sortowaniem."""
    return get_items_by_filters(collection, [(field, operator, value)], order_by, direction)

def get_sprzet_item(sprzet_id: str):
    return get_item(COLLECTION_SPRZET, sprzet_id)

def get_usterka_item(usterka_id: str):
    return get_item(COLLECTION_USTERKI, usterka_id)

def get_all_sprzet(category=None):
    if category:
        return get_items_by_filter(COLLECTION_SPRZET, 'category', '==', category, order_by='__name__', direction=firestore.Query.ASCENDING)
    return get_all_items(COLLECTION_SPRZET, order_by='__name__', direction=firestore.Query.ASCENDING)

def get_items_by_parent(parent_id):
    return get_items_by_filter(COLLECTION_SPRZET, 'parent_id', '==', parent_id, order_by='__name__', direction=firestore.Query.ASCENDING)

def get_all_usterki():
    return get_all_items(COLLECTION_USTERKI, order_by='data_zgloszenia')

def get_usterki_for_sprzet(sprzet_id: str):
    return get_items_by_filter(COLLECTION_USTERKI, 'sprzet_id', '==', sprzet_id, order_by='data_zgloszenia')

def update_item(collection: str, item_id: str, **kwargs):
    """Aktualizuje dokument w dowolnej kolekcji."""
    db = get_firestore_client()
    db.collection(collection).document(item_id).update(kwargs)

def update_usterka(usterka_id: str, **kwargs):
    update_item(COLLECTION_USTERKI, usterka_id, **kwargs)

def update_sprzet(sprzet_id: str, **kwargs):
    update_item(COLLECTION_SPRZET, sprzet_id, **kwargs)

def set_item(collection: str, item_id: str, data: dict):
    """Tworzy lub nadpisuje dokument o konkretnym ID."""
    db = get_firestore_client()
    db.collection(collection).document(item_id).set(data)
    return item_id

def add_item(collection: str, data: dict):
    """Dodaje nowy dokument do kolekcji."""
    db = get_firestore_client()
    if collection == COLLECTION_USTERKI and 'data_zgloszenia' not in data:
        data['data_zgloszenia'] = _warsaw_now()
    
    _, doc_ref = db.collection(collection).add(data)
    return doc_ref.id

def delete_item(collection: str, item_id: str):
    """Usuwa dokument z kolekcji."""
    db = get_firestore_client()
    db.collection(collection).document(item_id).delete()

# =======================================================================
#                       WYPOŻYCZENIA
# =======================================================================

def add_loan(data):
    """Dodaje nowe wypożyczenie."""
    data['status'] = 'active'
    data['timestamp'] = _warsaw_now()
    return add_item(COLLECTION_WYPOZYCZENIA, data)

def get_active_loans():
    """Pobiera wszystkie aktywne wypożyczenia."""
    return get_items_by_filter(COLLECTION_WYPOZYCZENIA, 'status', '==', 'active', order_by='timestamp')

def get_loans_for_item(item_id):
    """Pobiera historię wypożyczeń dla danego przedmiotu."""
    return get_items_by_filter(COLLECTION_WYPOZYCZENIA, 'item_id', '==', item_id, order_by='timestamp')

def mark_loan_returned(loan_id):
    """Oznacza wypożyczenie jako zwrócone."""
    update_item(COLLECTION_WYPOZYCZENIA, loan_id, status='returned', return_timestamp=_warsaw_now())