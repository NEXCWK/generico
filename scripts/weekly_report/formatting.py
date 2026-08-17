"""Locale-aware (pt-BR) formatting helpers for the weekly report."""

from __future__ import annotations


def fmt_int(n: float) -> str:
    return f"{round(n):,}".replace(",", ".")


def fmt_currency(n: float) -> str:
    s = f"{abs(n):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    sign = "-" if n < 0 else ""
    return f"{sign}R$ {s}"


def fmt_pct(n: float, decimals: int = 1) -> str:
    sign = "+" if n > 0 else ""
    return f"{sign}{n:.{decimals}f}%".replace(".", ",")


def fmt_ratio(n: float, decimals: int = 2) -> str:
    return f"{n:.{decimals}f}x".replace(".", ",")


def direction(n: float, flat_threshold: float = 0.05) -> str:
    if n > flat_threshold:
        return "up"
    if n < -flat_threshold:
        return "down"
    return "flat"


def arrow(dir_: str) -> str:
    return {"up": "▲", "down": "▼", "flat": "—"}[dir_]


def pct_change(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0 if current == 0 else 100.0
    return ((current - previous) / previous) * 100.0
