from . import get_firestore_client
from google.cloud import firestore

COLLECTION_SPRZET = 'sprzet'
COLLECTION_USTERKI = 'usterki'

def _get_doc_data(doc):
    """Pomocnicza funkcja do konwersji dokumentu Firestore na słownik z ID i formatowaniem daty."""
    if not doc.exists:
        return None
    data = doc.to_dict()
    data['id'] = doc.id
    if 'data_zgloszenia' in data and hasattr(data['data_zgloszenia'], 'strftime'):
        data['data_zgloszenia'] = data['data_zgloszenia'].strftime('%Y-%m-%d %H:%M')
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

def get_all_sprzet():
    return get_all_items(COLLECTION_SPRZET, order_by='__name__', direction=firestore.Query.ASCENDING)

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
        data['data_zgloszenia'] = firestore.SERVER_TIMESTAMP
    
    _, doc_ref = db.collection(collection).add(data)
    return doc_ref.id

def add_usterka(sprzet_id: str, opis: str, zgloszono_przez: str):
    data = {
        'sprzet_id': sprzet_id,
        'opis': opis,
        'zgloszono_przez': zgloszono_przez,
        'status': 'oczekuje'
    }
    return add_item(COLLECTION_USTERKI, data)