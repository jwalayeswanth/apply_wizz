from __future__ import annotations

import re
from pathlib import Path


def slugify(value: str) -> str:
    """
    Make file-name-safe slugs across platforms.
    """

    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-") or "untitled"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

