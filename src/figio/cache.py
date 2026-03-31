"""File-level caching for panel builds.

Computes content hashes of source scripts and input files to determine
whether a panel needs to be re-rendered.
"""

from __future__ import annotations

import hashlib
from pathlib import Path


def compute_hash(paths: list[Path], extra: str = "") -> str:
    """Compute SHA-256 hash of file contents and an optional extra string."""
    h = hashlib.sha256()
    for p in sorted(paths):
        if p.exists():
            h.update(p.read_bytes())
        else:
            h.update(f"MISSING:{p}".encode())
    if extra:
        h.update(extra.encode())
    return h.hexdigest()


def check_cache(cache_dir: Path, panel_id: str, current_hash: str) -> bool:
    """Return True if the cached hash matches the current hash."""
    hash_file = cache_dir / f"{panel_id}.hash"
    if not hash_file.exists():
        return False
    return hash_file.read_text().strip() == current_hash


def update_cache(cache_dir: Path, panel_id: str, hash_val: str) -> None:
    """Write the current hash to the cache file."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    hash_file = cache_dir / f"{panel_id}.hash"
    hash_file.write_text(hash_val)
