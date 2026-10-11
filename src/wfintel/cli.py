"""Command line: check the data, run the pipeline, audit the wording, render the report, serve the dashboard."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")


def main(argv: list[str] | None = None) -> int:
    from wfintel.paths import RESULTS

    p = argparse.ArgumentParser(prog="wfintel", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("data", help="check the committed CSV against its SHA-256 (or --download it again)")
    d.add_argument("--download", action="store_true")
    r = sub.add_parser("run", help="THE one command: employee records to recommendations (results/<run>/)")
    r.add_argument("--results", default=str(RESULTS))
    q = sub.add_parser("sql", help="run one measure query from sql/measures and print it")
    q.add_argument("measure")
    sub.add_parser("audit", help="causal-language audit of the docs, report and dashboard; exit 1 on any finding")
    sub.add_parser("report", help="render docs/generated/results.md from results/LATEST")
    s = sub.add_parser("serve", help="serve the dashboard and API")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8014)
    a = p.parse_args(argv)
    if a.cmd == "data":
        from wfintel.fetch import download, verify

        print(download() if a.download else verify())
    elif a.cmd == "run":
        from wfintel.pipeline import run

        print(run(Path(a.results)))
    elif a.cmd == "sql":
        from wfintel import db
        from wfintel.paths import SQL

        names = sorted(f.stem for f in (SQL / "measures").glob("*.sql") if f.stem != "attrition_by")
        if a.measure not in names:
            p.error(f"unknown measure; choose from {', '.join(names)}")
        import pandas as pd

        with pd.option_context("display.max_rows", 60, "display.width", 160):
            print(db.measure(db.build(), a.measure))
    elif a.cmd == "audit":
        from wfintel import audit

        res = audit.run()
        for f in res["findings"]:
            print(f"{f['file']}:{f['line']}: {f['rule']}: {f['text']}")
        print(
            f"{len(res['files'])} files scanned, {len(res['findings'])} findings: {'PASS' if res['passed'] else 'FAIL'}"
        )
        return 0 if res["passed"] else 1
    elif a.cmd == "report":
        from wfintel.report import render

        print(render())
    elif a.cmd == "serve":
        import uvicorn

        from wfintel.api import create_app

        token = os.environ.get("WFINTEL_TOKEN", "")
        if a.host not in ("127.0.0.1", "localhost", "::1") and not token:
            raise SystemExit("refusing to bind a non-loopback address without WFINTEL_TOKEN")
        uvicorn.run(create_app(token=token), host=a.host, port=a.port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
