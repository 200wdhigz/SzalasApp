from __future__ import annotations

from unittest.mock import patch


def test_sprzet_list_sets_fast_card_and_has_children_flags():
    # This is a logic-level test: in a folder view, items of specified categories
    # should get fast_card=True; has_children should reflect whether they have children.
    from src import views

    C = views.CATEGORIES

    items = [
        {'id': 'A', 'category': C['NAMIOT']},
        {'id': 'B', 'category': C['MAGAZYN']},
        {'id': 'C', 'category': C['PRZEDMIOT']},
    ]

    # children of parent listing include one doc with parent_id == 'A'
    children_in_parent_listing = [{'id': 'X', 'parent_id': 'A'}]

    def get_items_by_parent_side_effect(pid):
        # 1) for folder listing: pid == 'PARENT'
        if pid == 'PARENT':
            return children_in_parent_listing
        # 2) for child checks per item
        if pid == 'A':
            return [{'id': 'X1', 'parent_id': 'A'}]
        return []

    with patch('src.views.get_items_by_parent', side_effect=get_items_by_parent_side_effect), \
         patch('src.views.get_items_by_filters', return_value=items), \
         patch('src.views.get_all_sprzet', return_value=[]), \
         patch('src.views.get_sprzet_item', return_value=None):
        # Build a minimal request context to execute view
        from app import create_app

        app = create_app()
        with app.test_request_context('/sprzety?parent_id=PARENT'):
            # populate session minimally
            from flask import session
            session['user_role'] = 'user'
            session['user_id'] = 'u'
            # call view
            resp = views.sprzet_list()

    # resp is rendered HTML; flags are set in items in-place
    assert items[0].get('fast_card') is True
    assert items[0].get('has_children') is True
    assert items[1].get('fast_card') is False
    assert items[2].get('fast_card') is True
    assert items[2].get('has_children') is False


def test_sprzet_list_sets_fast_card_flags_in_global_search_view():
    # W widoku globalnym (bez parent_id) też chcemy, żeby fast-card działał.
    from src import views

    C = views.CATEGORIES

    items = [
        {'id': 'A', 'category': C['NAMIOT'], 'nazwa': 'Namiot Alpha'},
        {'id': 'B', 'category': C['MAGAZYN'], 'nazwa': 'Magazyn Beta'},
    ]

    # Przy samym `search` (bez filtrów) widok bierze `get_all_sprzet()`, a potem filtruje w pamięci.
    with patch('src.views.get_items_by_parent', return_value=[]), \
         patch('src.views.get_all_sprzet', return_value=items), \
         patch('src.views.get_sprzet_item', return_value=None):
        from app import create_app

        app = create_app()
        with app.test_request_context('/sprzety?search=namiot'):
            from flask import session

            session['user_role'] = 'user'
            session['user_id'] = 'u'
            _ = views.sprzet_list()

    assert items[0].get('fast_card') is True
    assert items[0].get('has_children') is False
