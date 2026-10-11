from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from wfintel.api import TOPICS, create_app


def _results(tmp: Path) -> Path:
    run = tmp / "20261010T000000Z-abcdef0"
    run.mkdir(parents=True)
    for t in TOPICS:
        (run / f"{t}.json").write_text(json.dumps({"topic": t}), encoding="utf-8")
    (tmp / "LATEST").write_text(run.name + "\n", encoding="utf-8")
    return tmp


def test_topics_served_and_unknown_rejected(tmp_path: Path) -> None:
    c = TestClient(create_app(results=_results(tmp_path), static_dir=tmp_path / "none"))
    assert c.get("/api/health").json() == {"status": "ok"}
    assert c.get("/api/topics/risk").json() == {"topic": "risk"}
    assert c.get("/api/topics/..%2Fprovenance").status_code == 404
    assert c.get("/api/topics/secrets").status_code == 404
    r = c.get("/api/topics/overview")
    assert "default-src 'self'" in r.headers["content-security-policy"]
    assert c.post("/api/topics/overview").status_code == 405


def test_token_required_when_set(tmp_path: Path) -> None:
    c = TestClient(create_app(token="s3cret", results=_results(tmp_path), static_dir=tmp_path / "none"))
    assert c.get("/api/topics/overview").status_code == 401
    assert c.get("/api/topics/overview", headers={"Authorization": "Bearer s3cret"}).status_code == 200
    assert c.get("/api/health").status_code == 200


def test_pending_when_no_result(tmp_path: Path) -> None:
    c = TestClient(create_app(results=tmp_path, static_dir=tmp_path / "none"))
    assert c.get("/api/topics/overview").status_code == 404
