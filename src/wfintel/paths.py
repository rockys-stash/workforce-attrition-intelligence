from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIGS = ROOT / "configs"
PROCESSED = ROOT / "data" / "processed"
SQL = ROOT / "sql"
RESULTS = ROOT / "results"
DOCS = ROOT / "docs"
WEB_DIST = ROOT / "web" / "dist"
