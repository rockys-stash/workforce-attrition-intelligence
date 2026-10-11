"""Read-only HTTP API for the workforce dashboard: serves one pipeline result (``results/LATEST``).

With ``WFINTEL_TOKEN`` set, every route but ``/api/health`` needs ``Authorization: Bearer
<token>``. Every client is rate limited; security headers on every response; nothing is written.
"""

from __future__ import annotations

import hmac
import json
import re
import threading
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from wfintel.paths import RESULTS, ROOT

_RUN = re.compile(r"^[0-9]{8}T[0-9]{6}Z-[0-9a-z]{4,40}$")
TOPICS = (
    "overview",
    "quality",
    "attrition",
    "departments",
    "compensation",
    "tenure",
    "risk",
    "recommendations",
    "audit",
    "provenance",
)


class RateLimiter:
    """Token bucket per client address."""

    def __init__(self, rate: float, burst: int) -> None:
        self.rate, self.burst = rate, burst
        self._b: dict[str, tuple[float, float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            tokens, last = self._b.get(key, (float(self.burst), now))
            tokens = min(self.burst, tokens + (now - last) * self.rate)
            ok = tokens >= 1
            self._b[key] = (tokens - 1 if ok else tokens, now)
            if len(self._b) > 10_000:
                self._b = dict(list(self._b.items())[-5_000:])
            return ok


class Guard(BaseHTTPMiddleware):
    def __init__(self, app: Any, token: str, limiter: RateLimiter) -> None:
        super().__init__(app)
        self.token, self.limiter = token, limiter

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        if path.startswith("/api"):
            client = request.client.host if request.client else "unknown"
            if not self.limiter.allow(client):
                return JSONResponse({"detail": "rate limit exceeded"}, status_code=429, headers={"Retry-After": "1"})
            if request.method not in ("GET", "HEAD"):
                return JSONResponse({"detail": "method not allowed"}, status_code=405)
            if self.token and path != "/api/health":
                supplied = request.headers.get("authorization", "").removeprefix("Bearer ").strip()
                if not hmac.compare_digest(supplied.encode(), self.token.encode()):
                    return JSONResponse({"detail": "unauthorized"}, status_code=401)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
            "font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        )
        return response


def create_app(token: str = "", results: Path | None = None, static_dir: Path | None = None) -> FastAPI:
    res = (results or RESULTS).resolve()
    static = (static_dir or ROOT / "web" / "dist").resolve()
    app = FastAPI(title="wfintel", docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(Guard, token=token, limiter=RateLimiter(rate=20.0, burst=60))

    def run_dir() -> Path:
        m = res / "LATEST"
        if not m.is_file():
            raise HTTPException(404, "no pipeline result yet (make all)")
        rid = m.read_text(encoding="utf-8").strip()
        if not _RUN.match(rid) or not (res / rid / "provenance.json").is_file():
            raise HTTPException(404, "no pipeline result yet (make all)")
        return res / rid

    def read(name: str) -> Any:
        p = run_dir() / name
        if not p.is_file():
            raise HTTPException(404, f"{name} missing from the result")
        return json.loads(p.read_text(encoding="utf-8"))

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/topics/{topic}")
    def topic(topic: str) -> Any:
        if topic not in TOPICS:
            raise HTTPException(404, "unknown topic")
        return read(f"{topic}.json")

    @app.get("/api/{rest:path}")
    def api_404(rest: str) -> Response:
        return JSONResponse({"detail": "not found"}, status_code=404)

    @app.get("/{rest:path}")
    def spa(rest: str) -> Response:
        if not static.exists():
            return JSONResponse({"detail": "dashboard not built (npm --prefix web run build)"}, status_code=404)
        candidate = (static / rest).resolve()
        if rest and candidate.is_file() and candidate.is_relative_to(static):
            return FileResponse(candidate)
        return FileResponse(static / "index.html")

    return app
