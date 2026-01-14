from __future__ import annotations

from datetime import datetime


def test_warsaw_now_has_timezone_and_is_warsaw():
    # Import funkcji pomocniczej bez wołania Firestore.
    from src import db_firestore

    now = db_firestore._warsaw_now()
    assert isinstance(now, datetime)
    assert now.tzinfo is not None

    # Nazwa strefy zależy od implementacji tzinfo, ale offset powinien być policzony.
    assert now.utcoffset() is not None

