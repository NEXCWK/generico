"""Generates a preview of the weekly report using mock data (no live credentials needed).

Usage: python scripts/render_preview.py [output_path]
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from weekly_report.constants import PRODUCT_LINES
from weekly_report.render import render_report_html
from weekly_report.report_builder import MetricSeries, build_context

MOCK_RAW = {
    "TOTAL": {
        "leads": MetricSeries(week_current=842, week_previous=771, mtd_current=2510, mtd_previous=2290),
        "opportunities": MetricSeries(week_current=96, week_previous=104, mtd_current=310, mtd_previous=298),
        "revenue": MetricSeries(week_current=187400, week_previous=162300, mtd_current=612000, mtd_previous=548000),
        "investment": MetricSeries(week_current=21300, week_previous=19800, mtd_current=68500, mtd_previous=71200),
    },
    "Escritórios Privativos": {
        "leads": MetricSeries(week_current=310, week_previous=290, mtd_current=940, mtd_previous=880),
        "opportunities": MetricSeries(week_current=42, week_previous=39, mtd_current=138, mtd_previous=120),
        "revenue": MetricSeries(week_current=98000, week_previous=81000, mtd_current=312000, mtd_previous=270000),
        "investment": MetricSeries(week_current=9800, week_previous=9100, mtd_current=31200, mtd_previous=33000),
    },
    "Compartilhados": {
        "leads": MetricSeries(week_current=205, week_previous=210, mtd_current=610, mtd_previous=640),
        "opportunities": MetricSeries(week_current=21, week_previous=25, mtd_current=68, mtd_previous=74),
        "revenue": MetricSeries(week_current=34200, week_previous=36800, mtd_current=112000, mtd_previous=118000),
        "investment": MetricSeries(week_current=5200, week_previous=5400, mtd_current=16900, mtd_previous=18100),
    },
    "Salas de Reunião": {
        "leads": MetricSeries(week_current=180, week_previous=155, mtd_current=520, mtd_previous=450),
        "opportunities": MetricSeries(week_current=18, week_previous=22, mtd_current=61, mtd_previous=58),
        "revenue": MetricSeries(week_current=28900, week_previous=24100, mtd_current=94000, mtd_previous=79000),
        "investment": MetricSeries(week_current=3600, week_previous=3200, mtd_current=11400, mtd_previous=11800),
    },
    "Escritório Virtual": {
        "leads": MetricSeries(week_current=147, week_previous=116, mtd_current=440, mtd_previous=320),
        "opportunities": MetricSeries(week_current=15, week_previous=18, mtd_current=43, mtd_previous=46),
        "revenue": MetricSeries(week_current=26300, week_previous=20400, mtd_current=94000, mtd_previous=81000),
        "investment": MetricSeries(week_current=2700, week_previous=2100, mtd_current=9000, mtd_previous=8300),
    },
}

assert set(MOCK_RAW.keys()) - {"TOTAL"} == set(PRODUCT_LINES)


def main() -> None:
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("scripts/preview_output.html")
    context = build_context(
        raw=MOCK_RAW,
        period={"start_label": "10/08/2026 13h01", "end_label": "17/08/2026 12h30"},
        generated_at="17/08/2026 13h00 (Brasília)",
    )
    html = render_report_html(context)
    out_path.write_text(html, encoding="utf-8")
    print(f"Preview written to {out_path}")


if __name__ == "__main__":
    main()
