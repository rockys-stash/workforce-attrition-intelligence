"""Causal-language audit.

The data are a cross-section, so every finding is an association. This audit scans the documents,
the generated results, the recommendations and the dashboard's source for wording that asserts
cause and effect, and fails if it finds any. Text inside double quotes or backticks is skipped, so
the rule itself can be stated by quoting the words it forbids.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from wfintel.paths import ROOT

# Each pattern is a phrase that asserts causation (or a counterfactual) rather than association.
_OBJ = r"(?:attrition|turnover|leaving|retention|quits?|resignations?|exits?|risk)"
PATTERNS: dict[str, str] = {
    "causes / caused / causing": r"\bcaus(?:e|es|ed|ing)\b",
    "drives / driven by / driver": r"\b(?:drives?|driven by|driving|drivers?)\b",
    "leads to": r"\b(?:leads?|led|leading) to\b",
    "results in": r"\bresult(?:s|ed|ing)? in\b",
    "due to": r"\bdue to\b",
    "because of": r"\bbecause of\b",
    "impact": r"\bimpact(?:s|ed|ing)?\b",
    "effect of / affects": r"\b(?:effects? of|affect(?:s|ed|ing)?)\b",
    "reduces / increases / lowers / raises <attrition>": rf"\b(?:reduc|increas|lower|rais|cut|boost|prevent|improv)\w* {_OBJ}\b",
    "<attrition> reduction / prevention": rf"\b{_OBJ} (?:reduction|prevention)\b",
    "makes employees": r"\bmakes? (?:employees|people|staff|workers)\b",
    "contributes to": r"\bcontribut(?:e|es|ed|ing) to\b",
    "determinant / root cause": r"\b(?:determinants?|root causes?)\b",
    "why employees leave": r"\bwhy (?:employees|people|staff) (?:leave|left|quit)\b",
    "reasons for leaving": r"\breasons? (?:for|behind) (?:leaving|attrition|turnover)\b",
    "explains attrition": rf"\bexplain(?:s|ed|ing)? (?:the )?{_OBJ}\b",
    "because (claim)": r"\bbecause (?:they|employees|people|staff)\b",
}
_QUOTED = re.compile(r"\"[^\"\n]*\"|“[^”\n]*”|`[^`\n]*`")
SCANNED = ("README.md", "docs/*.md", "docs/generated/*.md", "powerbi/*.md", "web/src/**/*.tsx", "web/src/**/*.ts")


@dataclass
class Finding:
    file: str
    line: int
    rule: str
    text: str


def scan_text(text: str, name: str = "<text>") -> list[Finding]:
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        clean = _QUOTED.sub(lambda m: " " * len(m.group(0)), line)
        for rule, pat in PATTERNS.items():
            for m in re.finditer(pat, clean, flags=re.IGNORECASE):
                out.append(Finding(name, i, rule, line.strip()[:200] if m else ""))
    return out


def files(root: Path = ROOT) -> list[Path]:
    seen: set[Path] = set()
    for pattern in SCANNED:
        seen.update(p for p in root.glob(pattern) if p.is_file())
    return sorted(seen)


def run(root: Path = ROOT, extra: dict[str, str] | None = None) -> dict[str, Any]:
    """Audit every scanned file plus extra named texts (the run's recommendations)."""
    found: list[Finding] = []
    scanned = []
    for p in files(root):
        rel = str(p.relative_to(root))
        scanned.append(rel)
        found += scan_text(p.read_text(encoding="utf-8"), rel)
    for name, text in (extra or {}).items():
        scanned.append(name)
        found += scan_text(text, name)
    return {"passed": not found, "files": scanned, "rules": list(PATTERNS), "findings": [asdict(f) for f in found]}
