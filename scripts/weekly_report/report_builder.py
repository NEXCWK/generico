"""Turns raw fetched metrics into the context dict consumed by the Jinja2 template.

Raw input shape expected from the data-source layer (Reportei client + nexpainel
scraper + local ROAS calc), per metric per line (and totals):

    MetricSeries(
        week_current=...,   # value for the report week (Mon 13:01 -> next Mon 12:30)
        week_previous=...,  # value for the equivalent prior week
        mtd_current=...,    # month-to-date, current month, through the report's end date
        mtd_previous=...,   # month-to-date, previous month, through the same day count
    )

ROAS is never fetched directly: it is derived here from revenue / investment at
every level (total, per line, per period) so the ratio is always internally
consistent with the other two metrics.
"""

from __future__ import annotations

from dataclasses import dataclass

from .constants import METRIC_LABELS, METRICS, PRODUCT_LINES
from .formatting import arrow, direction, fmt_currency, fmt_int, fmt_pct, fmt_ratio, pct_change


@dataclass
class MetricSeries:
    week_current: float
    week_previous: float
    mtd_current: float
    mtd_previous: float


def _roas_series(revenue: MetricSeries, investment: MetricSeries) -> MetricSeries:
    def safe_div(a: float, b: float) -> float:
        return a / b if b else 0.0

    return MetricSeries(
        week_current=safe_div(revenue.week_current, investment.week_current),
        week_previous=safe_div(revenue.week_previous, investment.week_previous),
        mtd_current=safe_div(revenue.mtd_current, investment.mtd_current),
        mtd_previous=safe_div(revenue.mtd_previous, investment.mtd_previous),
    )


_FORMATTERS = {
    "leads": fmt_int,
    "opportunities": fmt_int,
    "revenue": fmt_currency,
    "investment": fmt_currency,
    "roas": fmt_ratio,
}


def _build_kpi(metric_key: str, series: MetricSeries) -> dict:
    wow_pct = pct_change(series.week_current, series.week_previous)
    dtm_pct = pct_change(series.mtd_current, series.mtd_previous)
    wow_dir = direction(wow_pct)
    dtm_dir = direction(dtm_pct)
    fmt = _FORMATTERS[metric_key]
    return {
        "key": metric_key,
        "label": METRIC_LABELS[metric_key],
        "value": fmt(series.week_current),
        "raw_value": series.week_current,
        "wow_pct": fmt_pct(wow_pct),
        "wow_dir": wow_dir,
        "wow_arrow": arrow(wow_dir),
        "dtm_pct": fmt_pct(dtm_pct),
        "dtm_dir": dtm_dir,
        "dtm_arrow": arrow(dtm_dir),
    }


def build_totals_and_lines(
    raw: dict[str, dict[str, MetricSeries]],
) -> tuple[list[dict], list[dict]]:
    """raw: {line_name_or_'TOTAL': {metric_key: MetricSeries}} for leads/opportunities/revenue/investment.

    Returns (totals_list, lines_list) ready for the template context.
    """
    def with_roas(entry: dict[str, MetricSeries]) -> dict[str, MetricSeries]:
        entry = dict(entry)
        entry["roas"] = _roas_series(entry["revenue"], entry["investment"])
        return entry

    total_raw = with_roas(raw["TOTAL"])
    totals = [_build_kpi(m, total_raw[m]) for m in METRICS]

    lines = []
    for line_name in PRODUCT_LINES:
        line_raw = with_roas(raw[line_name])
        lines.append(
            {
                "name": line_name,
                "metrics": [_build_kpi(m, line_raw[m]) for m in METRICS],
            }
        )
    return totals, lines


def _metric_insight_text(kpi: dict, lines: list[dict]) -> str:
    label = kpi["label"]
    wow_word = {"up": "subiu", "down": "caiu", "flat": "ficou estável"}[kpi["wow_dir"]]
    dtm_word = {"up": "acima", "down": "abaixo", "flat": "em linha com"}[kpi["dtm_dir"]]

    line_kpis = [(l["name"], next(m for m in l["metrics"] if m["key"] == kpi["key"])) for l in lines]
    best = max(line_kpis, key=lambda x: x[1]["raw_value"] if False else _pct_value(x[1]))
    worst = min(line_kpis, key=lambda x: _pct_value(x[1]))

    text = (
        f"{label} {wow_word} {kpi['wow_pct']} em relação à semana anterior, e está {dtm_word} "
        f"o ritmo do mesmo período do mês passado ({kpi['dtm_pct']} D2M). "
        f"Destaque para {best[0]} ({best[1]['wow_pct']} na semana), enquanto {worst[0]} "
        f"foi a linha com pior variação ({worst[1]['wow_pct']})."
    )
    return text


def _pct_value(kpi: dict) -> float:
    s = kpi["wow_pct"].replace("+", "").replace("%", "").replace(",", ".")
    return float(s)


def build_insights(totals: list[dict], lines: list[dict]) -> list[dict]:
    insights = []
    for kpi in totals:
        insights.append({"title": kpi["label"], "text": _metric_insight_text(kpi, lines)})
    return insights


def build_context(raw: dict[str, dict[str, MetricSeries]], period: dict, generated_at: str) -> dict:
    totals, lines = build_totals_and_lines(raw)
    insights = build_insights(totals, lines)
    return {
        "period": period,
        "generated_at": generated_at,
        "totals": totals,
        "lines": lines,
        "insights": insights,
    }
