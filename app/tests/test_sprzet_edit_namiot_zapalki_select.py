from __future__ import annotations


def test_namiot_zapalki_is_select_with_5_6_options():
    from app import create_app

    app = create_app()
    with app.test_request_context('/'):
        from flask import render_template, session

        session['user_role'] = 'quartermaster'
        session['user_id'] = 'test_user'

        html = render_template(
            'sprzet_edit.html',
            sprzet=None,
            categories={
                'MAGAZYN': 'magazyn',
                'POLKA': 'polka_skrzynia',
                'NAMIOT': 'namiot',
                'PRZEDMIOT': 'przedmiot',
                'ZELASTWO': 'zelastwo',
                'KANADYJKI': 'kanadyjki',
            },
            magazyny_names=[],
            all_items=[],
            qty_suggestions_zelastwo=[],
            qty_suggestions_kanadyjki=[],
            do_czego_suggestions=[],
        )

    assert 'name="zapalki"' in html
    assert '<select name="zapalki"' in html
    assert 'value="5"' in html
    assert 'value="6"' in html

