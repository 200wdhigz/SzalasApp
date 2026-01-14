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

