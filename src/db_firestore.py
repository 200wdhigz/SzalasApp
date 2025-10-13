from . import get_firestore_client
from google.cloud import firestore

# NAZWY KOLEKCJI
COLLECTION_SPRZET = 'sprzet'
COLLECTION_USTERKI = 'usterki'


def get_sprzet_item(sprzet_id: str):
    """Pobiera pojedynczy element sprzętu po ID dokumentu Firestore."""
    db = get_firestore_client()

    # KLUCZOWY PUNKT: Użycie sprzet_id do odniesienia się do DOKUMENTU
    doc_ref = db.collection(COLLECTION_SPRZET).document(sprzet_id)
    doc = doc_ref.get()

    if doc.exists:
        data = doc.to_dict()
        # Ważne: Zapisz ID dokumentu, aby Flask mógł go użyć w url_for, itp.
        data['id'] = doc.id
        return data

    # Jeśli dokument nie istnieje
    return None


def get_all_sprzet():
    """Pobiera wszystkie elementy sprzętu z kolekcji 'sprzet'."""
    db = get_firestore_client()

    # 1. Pobranie wszystkich dokumentów
    sprzet_ref = db.collection(COLLECTION_SPRZET).stream()

    sprzet_list = []
    for doc in sprzet_ref:
        # 2. Konwersja na słownik
        data = doc.to_dict()

        # 3. DODANIE UNIKALNEGO ID DOKUMENTU
        data['id'] = doc.id

        # 4. Dodanie do listy
        sprzet_list.append(data)

    return sprzet_list



# DODAJ funkcje do pobierania usterek, etc.
def get_usterki_for_sprzet(sprzet_id: str):
    """Pobiera wszystkie usterki przypisane do danego ID sprzętu."""
    db = get_firestore_client()

    # KOREKTA: Użycie nowego obiektu firestore.FieldFilter
    query = db.collection(COLLECTION_USTERKI).where(
        filter=firestore.FieldFilter('sprzet_id', '==', sprzet_id)  # <-- ZMIANA JEST TUTAJ
    ).stream()

    usterki_list = []
    for doc in query:
        data = doc.to_dict()
        data['id'] = doc.id
        usterki_list.append(data)

    return usterki_list


def get_all_usterki():
    """
    Pobiera wszystkie usterki z kolekcji, sortując je od najnowszych do najstarszych.

    Wymaga, aby pole 'data_zgloszenia' było zdefiniowane (np. jako firestore.SERVER_TIMESTAMP).
    """
    db = get_firestore_client()

    # Zapytanie: Pobierz wszystkie dokumenty z kolekcji 'usterki'
    # i posortuj je malejąco po dacie zgłoszenia (najnowsze na górze).
    query = db.collection(COLLECTION_USTERKI).order_by('data_zgloszenia', direction=firestore.Query.DESCENDING).stream()

    usterki_list = []
    for doc in query:
        # 2. Konwersja na słownik
        data = doc.to_dict()

        # 3. DODANIE UNIKALNEGO ID DOKUMENTU
        data['id'] = doc.id

        if 'data_zgloszenia' in data:
            # Możesz tu użyć .strftime() lub przekazać jako jest i formatować w Jinja2
            data['data_zgloszenia'] = data['data_zgloszenia'].strftime('%Y-%m-%d %H:%M')

        # 4. Dodanie do listy
        usterki_list.append(data)

    return usterki_list


def get_usterka_item(usterka_id: str):
    """Pobiera pojedynczy dokument usterki po ID dokumentu Firestore."""
    db = get_firestore_client()
    doc_ref = db.collection(COLLECTION_USTERKI).document(usterka_id)
    doc = doc_ref.get()

    if doc.exists:
        data = doc.to_dict()
        data['id'] = doc.id
        return data
    return None


def update_usterka(usterka_id: str, **kwargs):
    """Aktualizuje pola w dokumencie usterki (używa kwargs dla elastyczności)."""
    db = get_firestore_client()
    doc_ref = db.collection(COLLECTION_USTERKI).document(usterka_id)

    # kwargs to słownik zawierający {'status': '...', 'uwagi_admina': '...' }
    doc_ref.update(kwargs)


def add_usterka(sprzet_id: str, opis: str, zgloszono_przez: str):
    """Dodaje nową usterkę do kolekcji usterek."""
    db = get_firestore_client()

    usterka_data = {
        'sprzet_id': sprzet_id,
        'opis': opis,
        'zgloszono_przez': zgloszono_przez,
        'data_zgloszenia': firestore.SERVER_TIMESTAMP,  # Timestamp z serwera
        'status': 'oczekuje',
    }

    # Firestore automatycznie generuje ID dla nowej usterki
    db.collection(COLLECTION_USTERKI).add(usterka_data)
