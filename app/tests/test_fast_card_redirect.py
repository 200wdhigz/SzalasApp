from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.fixture
def app():
    from app import create_app

    a = create_app()
    a.config.update({"TESTING": True})
    return a


def test_sprzet_list_link_goes_to_card_when_no_children(app):
    # Arrange: parent listing contains one namiot with no children
    from flask import render_template

    with app.test_request_context('/sprzety?parent_id=PARENT'):
        html = render_template(
            'sprzet_list.html',
            sprzet_list=[
                {
                    'id': 'NA01',
                    'category': 'namiot',
                    'nazwa': 'Namiot 1',
                    'typ': '',
                    'has_children': False,
                    'fast_card': True,
                    'is_group': False,
                    'magazyn_display': 'N/A',
                }
            ],
            typy=[],
            lokalizacje=[],
            wodoszczelnosci=[],
            kategorie={'NAMIOT': 'namiot'},
            parent_item={'id': 'PARENT', 'category': 'polka_skrzynia', 'zdjecia_lista_url': []},
            selected_filters={'parent_id': 'PARENT'},
            IS_QUARTERMASTER=False,
            is_debug=False,
        )

    assert "/sprzet/NA01" in html  # link to card
    assert "parent_id=NA01" not in html


def test_sprzet_list_link_goes_to_children_when_has_children(app):
    from flask import render_template

    with app.test_request_context('/sprzety?parent_id=PARENT'):
        html = render_template(
            'sprzet_list.html',
            sprzet_list=[
                {
                    'id': 'NA01',
                    'category': 'namiot',
                    'nazwa': 'Namiot 1',
                    'typ': '',
                    'has_children': True,
                    'fast_card': True,
                    'is_group': False,
                    'magazyn_display': 'N/A',
                }
            ],
            typy=[],
            lokalizacje=[],
            wodoszczelnosci=[],
            kategorie={'NAMIOT': 'namiot'},
            parent_item={'id': 'PARENT', 'category': 'polka_skrzynia', 'zdjecia_lista_url': []},
            selected_filters={'parent_id': 'PARENT'},
            IS_QUARTERMASTER=False,
            is_debug=False,
        )

    assert "parent_id=NA01" in html


def test_sprzet_list_shows_kanadyjki_material_and_state(app):
    from flask import render_template

    with app.test_request_context('/sprzety?parent_id=PARENT'):
        html = render_template(
            'sprzet_list.html',
            sprzet_list=[
                {
                    'id': 'KA01',
                    'category': 'kanadyjki',
                    'nazwa': 'Kanadyjka',
                    'material': 'materiałowa z bolcem',
                    'sprawny': 'Tak',
                    'ilosc': 4,
                    'jednostka': '.szt',
                    'oficjalna_ewidencja': 'Tak',
                    'has_children': False,
                    'fast_card': True,
                    'is_group': False,
                    'magazyn_display': 'N/A',
                }
            ],
            typy=[],
            lokalizacje=[],
            wodoszczelnosci=[],
            kategorie={'KANADYJKI': 'kanadyjki'},
            parent_item={'id': 'PARENT', 'category': 'polka_skrzynia', 'zdjecia_lista_url': []},
            selected_filters={'parent_id': 'PARENT'},
            IS_QUARTERMASTER=False,
            is_debug=False,
        )

    assert 'Kanadyjka (materiałowa z bolcem)' in html
    assert 'Sprawna' in html
    assert 'Ilość' in html
    assert 'Jedn.' in html
    assert '>4<' in html
    assert '.szt' in html
    assert 'Ewid.' in html
    assert 'W oficjalnej ewidencji' in html


def test_qr_code_endpoint_returns_png(app):
    from unittest.mock import patch

    client = app.test_client()

    with patch('src.views.get_sprzet_item') as mock_get:
        mock_get.return_value = {'id': 'X1'}
        resp = client.get('/sprzet/X1/qrcode')

    assert resp.status_code == 200
    assert resp.mimetype == 'image/png'


def test_qr_page_endpoint_returns_html(app):
    from unittest.mock import patch

    client = app.test_client()

    with patch('src.views.get_sprzet_item') as mock_get:
        mock_get.return_value = {'id': 'X1', 'nazwa': 'Test'}
        resp = client.get('/sprzet/X1/qr')

    assert resp.status_code == 200
    assert resp.mimetype in ('text/html', 'text/html; charset=utf-8')
    body = resp.data.decode('utf-8')
    assert '/sprzet/X1/qrcode' in body

