"""Utilities for exporting Firestore data to JSON.

Placed under `scripts/` so it can be imported by CLI scripts without changing
the package layout.

Contract
- Input: google.cloud.firestore.Client (via get_firestore_client())
- Output: pure-Python JSON-serializable structures (dict/list/str/float/bool/None)
- Error modes: raises on Firestore permission/network errors; type conversion is
  best-effort and falls back to string representation where needed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Iterable

from src import get_firestore_client
from src import _init_firebase_admin


@dataclass(frozen=True)
class ExportStats:
    collections: dict[str, int]


def _to_iso(dt: datetime) -> str:
    """Convert datetime to ISO-8601 with timezone."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def firestore_to_jsonable(value: Any) -> Any:
    """Convert Firestore / Python values into JSON-safe values."""

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, dict):
        return {str(k): firestore_to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [firestore_to_jsonable(v) for v in value]

    if isinstance(value, datetime):
        return {"__type__": "datetime", "value": _to_iso(value)}
    if isinstance(value, date):
        return {"__type__": "date", "value": value.isoformat()}

    if isinstance(value, Decimal):
        return {"__type__": "decimal", "value": str(value)}

    if isinstance(value, (bytes, bytearray, memoryview)):
        import base64

        return {
            "__type__": "bytes",
            "encoding": "base64",
            "value": base64.b64encode(bytes(value)).decode("ascii"),
        }

    try:
        from google.cloud.firestore import DocumentReference, GeoPoint

        if isinstance(value, DocumentReference):
            return {"__type__": "document_reference", "path": value.path}
        if isinstance(value, GeoPoint):
            return {
                "__type__": "geopoint",
                "latitude": value.latitude,
                "longitude": value.longitude,
            }
    except Exception:
        pass

    return str(value)


def export_collection(
    collection_name: str,
    *,
    page_size: int = 1000,
    include_document_name: bool = True,
) -> tuple[list[dict[str, Any]], int]:
    """Export one top-level collection using pagination."""

    # Ensure Firebase Admin is initialized for firestore.client().
    _init_firebase_admin()
    db = get_firestore_client()
    coll = db.collection(collection_name)

    exported: list[dict[str, Any]] = []
    last_doc = None

    while True:
        q = coll.order_by("__name__").limit(page_size)
        if last_doc is not None:
            q = q.start_after(last_doc)
        docs = list(q.stream())
        if not docs:
            break

        for doc in docs:
            d = doc.to_dict() or {}
            if include_document_name:
                d["id"] = doc.id
            exported.append(firestore_to_jsonable(d))

        last_doc = docs[-1]

    return exported, len(exported)


def export_many_collections(
    collection_names: Iterable[str],
    *,
    page_size: int = 1000,
    include_document_name: bool = True,
) -> tuple[dict[str, list[dict[str, Any]]], ExportStats]:
    """Export multiple collections."""

    collections: dict[str, list[dict[str, Any]]] = {}
    stats: dict[str, int] = {}

    for name in collection_names:
        docs, count = export_collection(
            name,
            page_size=page_size,
            include_document_name=include_document_name,
        )
        collections[name] = docs
        stats[name] = count

    return collections, ExportStats(collections=stats)
