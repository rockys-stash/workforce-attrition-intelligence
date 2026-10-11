"""Browser tests for the BI dashboard, served from the committed pipeline result (or WFINTEL_RESULTS).

Run with ``uv run pytest -m ui`` after ``npm --prefix web run build``.
"""

from __future__ import annotations

import os
import socket
import threading
import time
import urllib.request
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
AXE = ROOT / "web" / "node_modules" / "axe-core" / "axe.min.js"
pytestmark = [pytest.mark.ui]
playwright_api = pytest.importorskip("playwright.sync_api")

VIEWPORTS = {"desktop": {"width": 1440, "height": 900}, "mobile": {"width": 390, "height": 844}}


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@pytest.fixture(scope="module")
def base_url() -> Iterator[str]:
    if not (ROOT / "web" / "dist" / "index.html").exists():
        pytest.skip("frontend not built (npm --prefix web run build)")
    results = Path(os.environ.get("WFINTEL_RESULTS", ROOT / "results"))
    if not (results / "LATEST").exists():
        pytest.skip("no committed pipeline result")
    import uvicorn

    from wfintel.api import create_app

    app = create_app(results=results)
    port = _free_port()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            urllib.request.urlopen(f"{url}/api/health", timeout=1)
            break
        except OSError:
            time.sleep(0.1)
    yield url
    server.should_exit = True
    thread.join(timeout=5)


@pytest.fixture(scope="module")
def browser() -> Iterator[Any]:
    with playwright_api.sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


PAGES = [
    ("executive", "/executive", "Groups with the highest attrition"),
    ("attrition", "/attrition", "Association tests"),
    ("departments", "/departments", "Role profiles"),
    ("compensation", "/compensation", "Pay and attrition by job level"),
    ("tenure", "/tenure", "Employees and attrition by completed years"),
    ("risk", "/risk", "Adjusted odds ratios"),
    ("method", "/method", "Data checks"),
    ("not-found", "/nowhere", "not found"),
]


def _open(browser: Any, base_url: str, viewport: str, path: str, marker: str, scheme: str = "light") -> Any:
    ctx = browser.new_context(viewport=VIEWPORTS[viewport], color_scheme=scheme)
    page = ctx.new_page()
    errors: list[str] = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" and "40" not in m.text else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(base_url + path)
    page.get_by_text(marker, exact=False).first.wait_for(timeout=30000)
    page.wait_for_load_state("networkidle")
    page.errors = errors
    return page


@pytest.mark.parametrize("viewport", list(VIEWPORTS))
@pytest.mark.parametrize(("name", "path", "marker"), PAGES)
def test_page_renders(browser: Any, base_url: str, viewport: str, name: str, path: str, marker: str) -> None:
    page = _open(browser, base_url, viewport, path, marker)
    assert page.locator("h1").count() == 1
    assert not page.locator(".skeleton").count(), "loading skeleton still visible"
    assert not page.locator("[role=alert]").count(), "error state rendered"
    overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
    assert overflow <= 1, f"page scrolls horizontally by {overflow}px"
    assert not page.errors, page.errors
    page.context.close()


def test_characteristic_picker(browser: Any, base_url: str) -> None:
    page = _open(browser, base_url, "desktop", "/attrition", "Association tests")
    page.get_by_label("Characteristic").select_option("job_role")
    page.get_by_text("Sales Representative").first.wait_for()
    page.context.close()


def test_fairness_toggle(browser: Any, base_url: str) -> None:
    page = _open(browser, base_url, "desktop", "/risk", "Adjusted odds ratios")
    page.get_by_role("button", name="Without stock options").click()
    assert page.get_by_role("button", name="Without stock options").get_attribute("aria-pressed") == "true"
    assert page.locator("table").last.locator("tbody tr").count() > 0
    page.context.close()


def test_no_per_employee_scores(browser: Any, base_url: str) -> None:
    """The risk page shows groups only: no employee number appears in any table."""
    page = _open(browser, base_url, "desktop", "/risk", "Adjusted odds ratios")
    headers = page.locator("th").all_inner_texts()
    assert not any("employee number" in h.lower() or h.strip().lower() == "employee" for h in headers), headers
    page.context.close()


def test_executive_links_to_attrition(browser: Any, base_url: str) -> None:
    page = _open(browser, base_url, "desktop", "/executive", "Groups with the highest attrition")
    page.get_by_role("link", name="Every characteristic, with intervals").click()
    page.get_by_text("Association tests").first.wait_for()
    assert page.url.endswith("/attrition")
    page.context.close()


def test_fictional_data_and_power_bi_pending(browser: Any, base_url: str) -> None:
    page = _open(browser, base_url, "desktop", "/method", "Data checks")
    page.get_by_text("Power BI: pending").wait_for()
    assert page.get_by_text("fictional", exact=False).count() > 0
    page.get_by_text("Causal-language audit").first.wait_for()
    page.context.close()


def test_keyboard_reaches_navigation(browser: Any, base_url: str) -> None:
    page = _open(browser, base_url, "desktop", "/executive", "Groups with the highest attrition")
    names = []
    for _ in range(12):
        page.keyboard.press("Tab")
        names.append(page.evaluate("document.activeElement && document.activeElement.textContent"))
    assert any(n and "Tenure" in n for n in names), names
    page.context.close()


@pytest.mark.parametrize("scheme", ["light", "dark"])
@pytest.mark.parametrize("viewport", list(VIEWPORTS))
def test_no_wcag_violations(browser: Any, base_url: str, viewport: str, scheme: str) -> None:
    """axe-core audit (WCAG 2.1 A/AA and best practices) of every view in both themes."""
    if not AXE.exists():
        pytest.skip("axe-core not installed (npm --prefix web ci)")
    ctx = browser.new_context(viewport=VIEWPORTS[viewport], color_scheme=scheme, bypass_csp=True)
    page = ctx.new_page()
    found: dict[str, list[str]] = {}
    for _, path, marker in PAGES:
        page.goto(base_url + path)
        page.get_by_text(marker, exact=False).first.wait_for(timeout=30000)
        page.wait_for_load_state("networkidle")
        page.add_script_tag(path=str(AXE))
        violations = page.evaluate(
            """async () => (await axe.run(document, {runOnly: ['wcag2a', 'wcag2aa', 'wcag21aa',
               'best-practice']})).violations.map(v => v.id + ': ' + v.nodes.map(n => n.target.join(' ')).join(', '))"""
        )
        if violations:
            found[path] = violations
    ctx.close()
    assert not found, found
