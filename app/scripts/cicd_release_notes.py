"""CI/CD helper: generates a PR draft release payload.

Contract:
- Inputs (env):
  - GITHUB_REF_NAME: branch name (optional)
  - GITHUB_SHA: full sha (optional)
  - PR_NUMBER: pull request number (required for good tag)
  - BASE_VERSION: base version string (optional; if missing we read app/pyproject.toml)
- Output:
  - Prints JSON to stdout with keys: tag_name, name, body, prerelease, draft

This script is intentionally dependency-free (stdlib only).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path


RE_VERSION = re.compile(r"^version\s*=\s*\"(?P<ver>[^\"]+)\"\s*$")


def read_poetry_version(pyproject_path: Path) -> str:
    if not pyproject_path.exists():
        raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")

    in_poetry = False
    for line in pyproject_path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s == "[tool.poetry]":
            in_poetry = True
            continue
        if in_poetry and s.startswith("[") and s.endswith("]") and s != "[tool.poetry]":
            break
        if in_poetry:
            m = RE_VERSION.match(s)
            if m:
                return m.group("ver")

    raise ValueError("Could not find [tool.poetry].version in pyproject.toml")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    pyproject = repo_root / "app" / "pyproject.toml"

    base_version = os.environ.get("BASE_VERSION") or read_poetry_version(pyproject)
    pr_number = os.environ.get("PR_NUMBER")
    sha = (os.environ.get("GITHUB_SHA") or "")
    short_sha = sha[:7] if sha else "unknown"
    ref_name = os.environ.get("GITHUB_REF_NAME") or "unknown"

    if not pr_number:
        raise SystemExit("PR_NUMBER env var is required")

    # We use a prerelease tag that is unique per PR.
    tag_name = f"pr-{pr_number}"
    name = f"PR #{pr_number} – SzalasApp {base_version} (draft)"

    body = "\n".join(
        [
            "Automatycznie wygenerowany draft release dla Pull Request.",
            "",
            f"- PR: #{pr_number}",
            f"- Branch: `{ref_name}`",
            f"- Commit: `{short_sha}`",
            "",
            "Po merge do `master` wydaj stabilny release przez tag `vX.Y.Z`.",
        ]
    )

    payload = {
        "tag_name": tag_name,
        "name": name,
        "body": body,
        "prerelease": True,
        "draft": True,
    }

    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()

