from __future__ import annotations

from datetime import datetime, timezone

from scripts.firestore_export import firestore_to_jsonable


def test_firestore_to_jsonable_primitives_and_containers():
    payload = {
        "a": 1,
        "b": True,
        "c": None,
        "d": ["x", {"y": 2}],
    }
    out = firestore_to_jsonable(payload)
    assert out == payload


def test_firestore_to_jsonable_datetime_is_tagged_iso():
    dt = datetime(2026, 1, 1, 12, 30, tzinfo=timezone.utc)
    out = firestore_to_jsonable({"ts": dt})
    assert out["ts"]["__type__"] == "datetime"
    assert out["ts"]["value"].endswith("Z")


def test_firestore_to_jsonable_fallback_to_str_for_unknown_types():
    class Weird:
        def __str__(self):
            return "weird"

    out = firestore_to_jsonable({"w": Weird()})
    assert out == {"w": "weird"}
