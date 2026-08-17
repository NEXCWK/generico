"""Maps raw names (RD CRM funnel names, Google Ads campaign names, RD Station
lead tags/funnels, nexpainel product labels) to one of the four canonical
Nex product lines, by keyword similarity. Anything that doesn't match any
keyword set is intentionally dropped from the report (per spec: only these
four lines are covered, regardless of what else exists in the source
platforms).
"""

from __future__ import annotations

import unicodedata

from .constants import PRODUCT_LINES

_KEYWORDS: dict[str, list[str]] = {
    "Escritórios Privativos": ["privativ"],
    "Compartilhados": ["compartilhad", "coworking compartilhad", "estacao", "estação"],
    "Salas de Reunião": ["sala de reuniao", "sala reuniao", "meeting room", "sala de reunião"],
    "Escritório Virtual": ["virtual", "endereco fiscal", "endereço fiscal"],
}


def _normalize(s: str) -> str:
    s = s.lower().strip()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return s


def match_line(raw_name: str) -> str | None:
    normalized = _normalize(raw_name)
    for line in PRODUCT_LINES:
        for kw in _KEYWORDS[line]:
            if _normalize(kw) in normalized:
                return line
    return None


def group_by_line(items: list[tuple[str, float]]) -> dict[str, float]:
    """items: [(raw_name, value), ...]. Returns {canonical_line: summed_value}
    for values that matched a known line; unmatched items are dropped.
    """
    totals = {line: 0.0 for line in PRODUCT_LINES}
    for raw_name, value in items:
        line = match_line(raw_name)
        if line:
            totals[line] += value
    return totals
