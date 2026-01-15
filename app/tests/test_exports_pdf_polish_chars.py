from __future__ import annotations

import pytest


@pytest.fixture
def app():
    from app import create_app

    a = create_app()
    a.config.update({"TESTING": True})
    return a


def test_export_to_pdf_handles_polish_chars(app):
    # Minimalny test: generowanie PDF z polskimi znakami nie powinno rzucać wyjątków.
    from src.exports import export_to_pdf

    with app.test_request_context('/'):
        resp = export_to_pdf(
            data=[{'nazwa': 'Żółć', 'uwagi': 'Zażółć gęślą jaźń'}],
            filename='test',
            title='Raport: sprzęt – żółć',
        )

    assert resp.status_code == 200
    assert resp.mimetype == 'application/pdf'
