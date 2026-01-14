r"""Export Firestore collections to a single .json file.

Usage (PowerShell, from the `app/` directory):
  $env:GOOGLE_APPLICATION_CREDENTIALS="..\credentials\service-account.json"
  python -m scripts.export_firestore_json --out ..\export\firestore_export.json

(Recommended) If you run it as a file, make sure `app/` is on PYTHONPATH.

By default exports the project's main top-level collections.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

try:
    # When run as module: `python -m scripts.export_firestore_json`
    from .firestore_export import export_many_collections
except ImportError:  # pragma: no cover
    # When run as file: `python scripts/export_firestore_json.py`
    # (requires app/ on sys.path)
    from scripts.firestore_export import export_many_collections


DEFAULT_COLLECTIONS = ["sprzet", "usterki", "logs", "users"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Export Firestore database to JSON")
    p.add_argument(
        "--out",
        required=True,
        help="Output JSON path (will be overwritten if exists)",
    )
    p.add_argument(
        "--collections",
        nargs="*",
        default=DEFAULT_COLLECTIONS,
        help=f"Collections to export (default: {', '.join(DEFAULT_COLLECTIONS)})",
    )
    p.add_argument(
        "--page-size",
        type=int,
        default=1000,
        help="Firestore pagination page size (default: 1000)",
    )
    p.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON (human readable)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    # Load env similarly to the app: scripts are run from app/ usually.
    # We keep override=False so existing env vars win.
    here = Path(__file__).resolve()
    app_dir = here.parents[1]
    repo_root = app_dir.parent
    load_dotenv(app_dir / ".env", override=False)
    load_dotenv(repo_root / ".env", override=False)

    args = build_parser().parse_args(argv)

    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    collections, stats = export_many_collections(
        args.collections,
        page_size=args.page_size,
        include_document_name=True,
    )

    payload = {
        "metadata": {
            "exported_at": _utc_now_iso(),
            "collections": list(args.collections),
            "counts": stats.collections,
            "google_project_id": os.getenv("GOOGLE_PROJECT_ID") or os.getenv("GCP_PROJECT_ID"),
        },
        "collections": collections,
    }

    indent = 2 if args.pretty else None
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=indent)

    total = sum(stats.collections.values())
    print(f"✅ Export complete: {out_path} ({total} documents)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
