from __future__ import annotations

import pytest


def _render_template(template_name: str, **ctx) -> str:
    # Aplikacja jest zdefiniowana w app/app.py jako factory create_app.
    from app import create_app

    app = create_app()
    with app.test_request_context('/'):
        # kontekst procesora szablonów używa session
        from flask import render_template, session

        session['user_role'] = 'quartermaster'
        session['user_id'] = 'test_user'
        return render_template(template_name, **ctx)


@pytest.mark.parametrize("category", ["zelastwo", "kanadyjki", "przedmiot"])
def test_sprzet_edit_template_has_qty_and_unit_fields_for_zelastwo_kanadyjki(category):
    html = _render_template(
        "sprzet_edit.html",
        sprzet=None,
        categories={
            "ZELASTWO": "zelastwo",
            "KANADYJKI": "kanadyjki",
            "PRZEDMIOT": "przedmiot",
            "NAMIOT": "namiot",
            "MAGAZYN": "magazyn",
            "POLKA": "polka_skrzynia",
        },
        magazyny_names=[],
        all_items=[],
        qty_suggestions_zelastwo=["1", "2"],
        qty_suggestions_kanadyjki=["4"],
    )

    # W HTML pola istnieją zawsze (sterowane JS-em), więc testujemy obecność.
    assert "qty_suggestions_zelastwo" in html
    assert "qty_suggestions_kanadyjki" in html
    assert "name=\"ilosc\"" in html
    assert "name=\"jednostka\"" in html


def test_normalize_qty_units_maps_sztuki_to_dot_szt():
    from src import views

    C = views.CATEGORIES

    # Test for all relevant categories
    for cat_name, cat_value in [('PRZEDMIOT', C['PRZEDMIOT']), ('ZELASTWO', C['ZELASTWO']), ('KANADYJKI', C['KANADYJKI'])]:
        for raw in ['szt', 'szt.', 'sztuki', 'Sztuki', ' .szt ', '.szt']:
            data = {'ilosc': '3', 'jednostka': raw}
            views._normalize_qty_fields(data, cat_value)
            assert data.get('jednostka') == '.szt', f"Failed for category {cat_name} with input '{raw}'"
