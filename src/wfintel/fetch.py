"""The source data: IBM's fictional HR attrition dataset, committed under ODbL with its SHA-256."""

from __future__ import annotations

import hashlib
import urllib.request
from pathlib import Path

from wfintel.config import config
from wfintel.paths import ROOT


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def verify() -> Path:
    """Check the committed CSV against the hash in the config; fail loudly if it differs."""
    src = config()["source"]
    path = ROOT / src["file"]
    if not path.is_file():
        raise SystemExit(f"{path} is missing; run `wfintel data --download`")
    got = sha256(path)
    if got != src["sha256"]:
        raise SystemExit(f"{path} has SHA-256 {got}, expected {src['sha256']}")
    return path


def download() -> Path:
    """Fetch the CSV again from its source and check it matches the committed copy."""
    src = config()["source"]
    path = ROOT / src["file"]
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".download")
    with urllib.request.urlopen(src["url"], timeout=60) as r:
        tmp.write_bytes(r.read())
    got = sha256(tmp)
    if got != src["sha256"]:
        tmp.unlink()
        raise SystemExit(f"downloaded file has SHA-256 {got}, expected {src['sha256']}; the source has changed")
    tmp.replace(path)
    return path
