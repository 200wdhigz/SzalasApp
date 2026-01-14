"""ID generation utilities.

We use human-readable IDs for warehouses ("magazyn"), derived from their names,
so users can recognize the location quickly.

Rules for warehouse IDs:
- prefix: MAG_
- slug of the warehouse name (ASCII, lowercase, words separated by `_`)
- optional numeric suffix to ensure uniqueness

Example:
- "Magazyn Warszawa" -> "MAG_WARSZAWA"
- second one with same name -> "MAG_WARSZAWA_2"
"""

from __future__ import annotations

import re
import time
import unicodedata


_slug_invalid_re = re.compile(r"[^a-z0-9]")


def slugify_id(text: str) -> str:
    """Convert text to an ASCII slug usable in IDs.

    Requirements:
    - only [A-Z0-9] effectively (we generate lowercase here and uppercase later)
    - no separators like `_`
    - max length: 8 characters
    """

    text = (text or "").strip()
    if not text:
        return ""

    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = ascii_text.lower()

    # Remove all non-alphanumeric characters (no underscores/separators)
    ascii_text = _slug_invalid_re.sub("", ascii_text)

    # Enforce max length
    return ascii_text[:8]


def generate_magazyn_id_base(name: str) -> str:
    slug = slugify_id(name)
    if not slug:
        # Safe fallback with timestamp to prevent collisions
        return f"MAG_{int(time.time())}"
    return f"MAG_{slug}".upper()


def generate_unique_magazyn_id(name: str, existing_ids: set[str]) -> str:
    """Generate a human-readable, unique warehouse ID.

    existing_ids: set of current document IDs in the `sprzet` collection.
    """
    base = generate_magazyn_id_base(name)
    if base not in existing_ids:
        return base

    i = 2
    while True:
        candidate = f"{base}_{i}"
        if candidate not in existing_ids:
            return candidate
        i += 1
