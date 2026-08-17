"""Round 2 of Reportei API discovery: now that we know the shape (client_id
458229 "Nex", integrations for RD Station Marketing/CRM/Google Ads, and
pre-built "reports" a.k.a. dashboards), dig into report widgets and
integration-level metrics endpoints to find where actual date-ranged,
campaign/funnel-level numbers live.
"""

from __future__ import annotations

import json
import os

import requests

TOKEN = os.environ["REPORTEI_API_TOKEN"]
BASE = "https://app.reportei.com/api/v1"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}
CLIENT_ID = 458229

INTEGRATIONS = {
    "rd_marketing": 1351098,
    "rd_crm": 1351117,
    "google_ads": 1979996,
}
REPORT_IDS = {
    "WEEKLY_TT": 2874248,
    "WEEKLY_Sales": 4762966,
}

MAX_PRINT = 3500


def show(label: str, data) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False, default=str)
    if len(text) > MAX_PRINT:
        text = text[:MAX_PRINT] + f"\n... [truncated, {len(text)} chars total]"
    print(f"\n=== {label} ===\n{text}")


def get(path: str, params: dict | None = None) -> dict:
    url = f"{BASE}{path}"
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=25)
        try:
            body = resp.json()
        except Exception:  # noqa: BLE001
            body = resp.text[:1500]
        return {"url": resp.url, "status": resp.status_code, "body": body}
    except Exception as e:  # noqa: BLE001
        return {"url": url, "error": str(e)}


def probe(label: str, path: str, params: dict | None = None) -> None:
    r = get(path, params)
    status = r.get("status")
    print(f"probe {path} params={params}: {status or r.get('error')}")
    if status == 200:
        show(label, r)


def main() -> None:
    for name, report_id in REPORT_IDS.items():
        probe(f"report {name} detail", f"/clients/{CLIENT_ID}/reports/{report_id}")
        for sub in ["/widgets", "/blocks", "/data", "/metrics"]:
            probe(f"report {name}{sub}", f"/clients/{CLIENT_ID}/reports/{report_id}{sub}")

    date_params_variants = [
        {"start_date": "2026-08-10", "end_date": "2026-08-17"},
        {"date_start": "2026-08-10", "date_end": "2026-08-17"},
        {"from": "2026-08-10", "to": "2026-08-17"},
    ]

    for int_name, int_id in INTEGRATIONS.items():
        for sub in ["/metrics", "/data", "/campaigns", "/funnels", "/deals"]:
            path = f"/clients/{CLIENT_ID}/integrations/{int_id}{sub}"
            probe(f"{int_name}{sub} (no params)", path)
            probe(f"{int_name}{sub} (dates)", path, date_params_variants[0])

    print("\nDiscovery round 2 complete.")


if __name__ == "__main__":
    main()
