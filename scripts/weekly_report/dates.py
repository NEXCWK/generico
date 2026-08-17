"""Computes the report period and its comparison windows, in America/Sao_Paulo time.

Report period: previous Monday 13:01 -> this Monday 12:30 (the report is sent
this Monday at 13:00, right after the period closes).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Sao_Paulo")


@dataclass
class DateRange:
    start: datetime
    end: datetime


@dataclass
class ReportWindows:
    current_week: DateRange
    previous_week: DateRange
    mtd_current: DateRange
    mtd_previous: DateRange


def _start_of_month(d: datetime) -> datetime:
    return d.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def compute_windows(run_at: datetime | None = None) -> ReportWindows:
    """run_at: the Monday the report is generated/sent, ~13:00 America/Sao_Paulo.

    If omitted, uses "now" in America/Sao_Paulo.
    """
    now = run_at.astimezone(TZ) if run_at else datetime.now(TZ)

    period_end = now.replace(hour=12, minute=30, second=0, microsecond=0)
    period_start = (period_end - timedelta(days=7)).replace(hour=13, minute=1)

    prev_period_end = period_end - timedelta(days=7)
    prev_period_start = period_start - timedelta(days=7)

    mtd_current_start = _start_of_month(period_end)
    mtd_current = DateRange(start=mtd_current_start, end=period_end)

    prev_month_end_anchor = period_end - relativedelta(months=1)
    mtd_previous_start = _start_of_month(prev_month_end_anchor)
    mtd_previous = DateRange(start=mtd_previous_start, end=prev_month_end_anchor)

    return ReportWindows(
        current_week=DateRange(start=period_start, end=period_end),
        previous_week=DateRange(start=prev_period_start, end=prev_period_end),
        mtd_current=mtd_current,
        mtd_previous=mtd_previous,
    )


def period_labels(windows: ReportWindows) -> dict:
    cw = windows.current_week
    return {
        "start_label": cw.start.strftime("%d/%m/%Y %Hh%M"),
        "end_label": cw.end.strftime("%d/%m/%Y %Hh%M"),
    }
