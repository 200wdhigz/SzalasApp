from __future__ import annotations
import pytest

@pytest.fixture
def app():
    from app import create_app
    app = create_app()
    app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False
    })
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_normalize_qty_fields_kanadyjki_only_sztuki():
    from src.views import _normalize_qty_fields, CATEGORIES
    # Kanadyjki: jednostka zawsze .szt
    data = {'ilosc': '10', 'jednostka': 'zest.'}
    _normalize_qty_fields(data, CATEGORIES['KANADYJKI'])
    assert data.get('jednostka') == '.szt'

    data = {'ilosc': '10', 'jednostka': 'szt.'}
    _normalize_qty_fields(data, CATEGORIES['KANADYJKI'])
    assert data.get('jednostka') == '.szt'


def test_normalize_qty_fields_zelastwo_both_allowed():
    from src.views import _normalize_qty_fields, CATEGORIES
    # Żelastwo: dozwolone zest. i .szt, domyślnie zest.
    data = {'ilosc': '5', 'jednostka': 'zest.'}
    _normalize_qty_fields(data, CATEGORIES['ZELASTWO'])
    assert data.get('jednostka') == 'zest.'

    data = {'ilosc': '5', 'jednostka': 'szt.'}
    _normalize_qty_fields(data, CATEGORIES['ZELASTWO'])
    assert data.get('jednostka') == '.szt'

    data = {'ilosc': '5'}
    _normalize_qty_fields(data, CATEGORIES['ZELASTWO'])
    assert data.get('jednostka') == 'zest.'

def test_loan_return_self_block(client):
    from unittest.mock import patch
    # Mock database calls
    with patch('src.views.get_item') as mock_get_item, \
         patch('src.db_users.get_user_by_uid') as mock_get_user, \
         patch('src.views.mark_loan_returned') as mock_mark_returned:
        
        # Mock loan data
        mock_get_item.return_value = {
            'id': 'loan123',
            'przez_kogo': 'Jan Kowalski',
            'status': 'active'
        }
        
        # Mock current user
        mock_get_user.return_value = {
            'first_name': 'Jan',
            'last_name': 'Kowalski',
            'email': 'jan@example.com'
        }
        
        with client.session_transaction() as sess:
            sess['user_id'] = 'user123'
            sess['user_role'] = 'quartermaster'
        
        # Attempt to return own loan
        response = client.post('/loan/return/loan123', follow_redirects=True)
        
        assert 'Osoba która wypożyczała nie może sama sobie zwrócić wypożyczenia.'.encode('utf-8') in response.data
        mock_mark_returned.assert_not_called()

def test_loan_return_other_success(client):
    from unittest.mock import patch
    # Mock database calls
    with patch('src.views.get_item') as mock_get_item, \
         patch('src.db_users.get_user_by_uid') as mock_get_user, \
         patch('src.views.mark_loan_returned') as mock_mark_returned:
        
        # Mock loan data
        mock_get_item.return_value = {
            'id': 'loan123',
            'przez_kogo': 'Inna Osoba',
            'status': 'active'
        }
        
        # Mock current user
        mock_get_user.return_value = {
            'first_name': 'Jan',
            'last_name': 'Kowalski',
            'email': 'jan@example.com'
        }
        
        with client.session_transaction() as sess:
            sess['user_id'] = 'user123'
            sess['user_role'] = 'quartermaster'
        
        # Attempt to return someone else's loan
        response = client.post('/loan/return/loan123', follow_redirects=True)
        
        assert 'Przedmiot został zwrócony.'.encode('utf-8') in response.data
        mock_mark_returned.assert_called_once_with('loan123')

def test_oficjalna_ewidencja_filtering(client):
    from unittest.mock import patch
    with patch('src.views.get_all_sprzet') as mock_all, \
         patch('src.views.get_items_by_filters') as mock_filtered, \
         patch('src.views.get_item') as mock_get_item, \
         patch('src.views.get_firestore_client') as mock_db:
        
        mock_get_item.return_value = None
        mock_all.return_value = []
        mock_filtered.return_value = [{'id': 'item1', 'oficjalna_ewidencja': 'Tak'}]

        with client.session_transaction() as sess:
            sess['user_id'] = 'user123'
            sess['user_role'] = 'quartermaster'
        
        # Test filtering
        response = client.get('/sprzety?oficjalna_ewidencja=Tak')
        assert response.status_code == 200
        # Check if filter was called with correct parameters
        args, kwargs = mock_filtered.call_args
        assert ('oficjalna_ewidencja', '==', 'Tak') in args[1]

def test_oficjalna_ewidencja_in_grouped_items(client):
    from unittest.mock import patch
    from src.db_firestore import CATEGORIES
    with patch('src.views.get_all_sprzet') as mock_all, \
         patch('src.views.get_items_by_filters') as mock_filtered, \
         patch('src.views.get_item') as mock_get_item, \
         patch('src.views.get_items_by_parent') as mock_parent, \
         patch('src.views.get_sprzet_item') as mock_get_sprzet:
        
        # Przygotowujemy dane do grupowania (np. dwa takie same maszty)
        items = [
            {
                'id': 'MASZT1', 
                'category': CATEGORIES['ZELASTWO'], 
                'typ_zelastwa': 'maszt', 
                'do_czego': 'Namiot 1', 
                'sprawny': 'Tak', 
                'oficjalna_ewidencja': 'Tak',
                'lokalizacja': 'Magazyn A'
            },
            {
                'id': 'MASZT2', 
                'category': CATEGORIES['ZELASTWO'], 
                'typ_zelastwa': 'maszt', 
                'do_czego': 'Namiot 1', 
                'sprawny': 'Tak', 
                'oficjalna_ewidencja': 'Tak',
                'lokalizacja': 'Magazyn A'
            }
        ]
        
        mock_filtered.return_value = items
        mock_all.return_value = items
        mock_get_item.return_value = {'id': 'PARENT', 'category': 'magazyn'}
        mock_get_sprzet.return_value = {'id': 'PARENT', 'category': 'magazyn'}
        mock_parent.return_value = []

        with client.session_transaction() as sess:
            sess['user_id'] = 'user123'
            sess['user_role'] = 'quartermaster'

        # Wywołujemy listę z parent_id, aby uruchomić grupowanie
        response = client.get('/sprzety?parent_id=PARENT')
        
        assert response.status_code == 200
        # Sprawdzamy czy w HTML pojawił się badge "Tak" dla ewidencji w pogrupowanym wierszu
        html = response.data.decode('utf-8')
        assert 'W oficjalnej ewidencji' in html
        assert 'Tak</span>' in html

def test_export_oficjalna_ewidencja_filter(client):
    from unittest.mock import patch
    with patch('src.views.get_items_by_filters') as mock_filtered, \
         patch('src.views.get_all_sprzet') as mock_all:
        
        mock_filtered.return_value = []
        
        with client.session_transaction() as sess:
            sess['user_id'] = 'user123'
            sess['user_role'] = 'quartermaster'
            
        # Sprawdzamy czy eksport przyjmuje parametr oficjalna_ewidencja
        client.get('/sprzet/export/csv?oficjalna_ewidencja=Tak')
        
        # Weryfikujemy czy filtr został przekazany do bazy
        args, kwargs = mock_filtered.call_args
        filters = args[1]
        assert ('oficjalna_ewidencja', '==', 'Tak') in filters

def test_oficjalna_ewidencja_default_value(client):
    from unittest.mock import patch
    with patch('src.views.get_sprzet_item') as mock_get, \
         patch('src.views.set_item') as mock_set, \
         patch('src.views.process_uploads') as mock_uploads, \
         patch('src.views.get_firestore_client') as mock_db, \
         patch('src.views.add_log') as mock_log:

        mock_get.return_value = None
        mock_uploads.return_value = ([], None)
        
        with client.session_transaction() as sess:
            sess['user_id'] = 'user123'
            sess['user_role'] = 'quartermaster'
            
        # Add item without oficjalna_ewidencja field
        data = {
            'id': 'new_item',
            'category': 'przedmiot',
            'nazwa': 'Test Item'
        }
        response = client.post('/sprzet/add', data=data, follow_redirects=True)
        
        assert response.status_code == 200
        # Verify that default 'Nie' was added
        added_data = mock_set.call_args[0][2]
        assert added_data['oficjalna_ewidencja'] == 'Nie'

def test_sprzet_bulk_edit_oficjalna_ewidencja(client):
    from unittest.mock import patch
    with patch('src.views.get_sprzet_item') as mock_get, \
         patch('src.views.update_sprzet') as mock_update, \
         patch('src.views.add_log') as mock_log, \
         patch('src.views.get_firestore_client') as mock_db:
        
        # Mock two items
        mock_get.side_effect = [
            {'id': 'item1', 'oficjalna_ewidencja': 'Nie'},
            {'id': 'item2', 'oficjalna_ewidencja': 'Nie'}
        ]
        
        with client.session_transaction() as sess:
            sess['user_id'] = 'user123'
            sess['user_role'] = 'quartermaster'
            sess['_csrf_token'] = 'test_token'
            
        data = {
            'sprzet_ids': ['item1', 'item2'],
            'oficjalna_ewidencja': 'Tak',
            '_csrf_token': 'test_token'
        }
        
        response = client.post('/sprzet/bulk-edit/confirm', data=data, follow_redirects=True)
        
        assert response.status_code == 200
        assert mock_update.call_count == 2
        
        # Check first call
        args, kwargs = mock_update.call_args_list[0]
        assert args[0] == 'item1'
        assert kwargs['oficjalna_ewidencja'] == 'Tak'
        
        # Check second call
        args, kwargs = mock_update.call_args_list[1]
        assert args[0] == 'item2'
        assert kwargs['oficjalna_ewidencja'] == 'Tak'

def test_usterki_oficjalna_ewidencja_filtering(client):
    from unittest.mock import patch
    with patch('src.views.get_all_usterki') as mock_usterki, \
         patch('src.views.get_all_sprzet') as mock_sprzet, \
         patch('src.views.get_firestore_client') as mock_db:
        
        mock_usterki.return_value = [
            {'id': 'u1', 'sprzet_id': 's1', 'status': 'oczekuje'},
            {'id': 'u2', 'sprzet_id': 's2', 'status': 'oczekuje'}
        ]
        mock_sprzet.return_value = [
            {'id': 's1', 'oficjalna_ewidencja': 'Tak'},
            {'id': 's2', 'oficjalna_ewidencja': 'Nie'}
        ]
        
        with client.session_transaction() as sess:
            sess['user_id'] = 'user123'
            
        # Filtrowanie po oficjalnej ewidencji
        response = client.get('/usterki?oficjalna_ewidencja=Tak')
        assert response.status_code == 200
        assert 'u1'.encode() in response.data
        assert 'u2'.encode() not in response.data
