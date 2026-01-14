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
    # Kanadyjki: jednostka zawsze szt.
    data = {'ilosc': '10', 'jednostka': 'zest.'}
    _normalize_qty_fields(data, CATEGORIES['KANADYJKI'])
    assert data.get('jednostka') == 'szt.'

    data = {'ilosc': '10', 'jednostka': 'szt.'}
    _normalize_qty_fields(data, CATEGORIES['KANADYJKI'])
    assert data.get('jednostka') == 'szt.'


def test_normalize_qty_fields_zelastwo_both_allowed():
    from src.views import _normalize_qty_fields, CATEGORIES
    # Żelastwo: dozwolone zest. i szt., domyślnie zest.
    data = {'ilosc': '5', 'jednostka': 'zest.'}
    _normalize_qty_fields(data, CATEGORIES['ZELASTWO'])
    assert data.get('jednostka') == 'zest.'

    data = {'ilosc': '5', 'jednostka': 'szt.'}
    _normalize_qty_fields(data, CATEGORIES['ZELASTWO'])
    assert data.get('jednostka') == 'szt.'

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
