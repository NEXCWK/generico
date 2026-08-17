"""One-off discovery script: probes the Reportei API with the configured token
and dumps raw responses so the real client (reportei_client.py) can be built
against actual response shapes instead of guessed ones.

Run only via the "discover" GitHub Actions workflow (needs real network
access, which local/sandboxed dev sessions may not have). Writes JSON dumps
to discover_output/ for inspection as a workflow artifact.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import requests

TOKEN = os.environ["REPORTEI_API_TOKEN"]
BASE_CANDIDATES = [
    "https://app.reportei.com/api/v1",
    "https://api.reportei.com/v1",
]
OUT_DIR = Path("discover_output")
OUT_DIR.mkdir(exist_ok=True)


def dump(name: str, data) -> None:
    path = OUT_DIR / f"{name}.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"wrote {path}")


def try_get(base: str, path: str, headers: dict, params: dict | None = None) -> dict:
    url = f"{base}{path}"
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=20)
        return {
            "url": url,
            "status": resp.status_code,
            "headers": dict(resp.headers),
            "body": _safe_json(resp),
        }
    except Exception as e:  # noqa: BLE001
        return {"url": url, "error": str(e)}


def _safe_json(resp):
    try:
        return resp.json()
    except Exception:  # noqa: BLE001
        return resp.text[:5000]


def main() -> None:
    headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}

    results = {}
    for base in BASE_CANDIDATES:
        for path in ["/customers", "/me", "/account", "/user"]:
            key = f"{base}{path}"
            results[key] = try_get(base, path, headers)

    dump("00_probe_roots", results)

    working_base = None
    working_customers_path = None
    for key, r in results.items():
        if r.get("status") == 200:
            print(f"OK: {key}")
            if "/customers" in key:
                working_base = key.split("/customers")[0]
                working_customers_path = "/customers"

    if working_base and working_customers_path:
        customers = try_get(working_base, working_customers_path, headers)
        dump("01_customers", customers)

        body = customers.get("body")
        customer_ids = _extract_ids(body)
        for cid in customer_ids[:3]:
            detail = try_get(working_base, f"/customers/{cid}", headers)
            dump(f"02_customer_{cid}", detail)

            for sub in ["/integrations", "/data-sources", "/metrics", "/reports"]:
                sub_resp = try_get(working_base, f"/customers/{cid}{sub}", headers)
                dump(f"03_customer_{cid}_{sub.strip('/')}", sub_resp)

    print("Discovery complete. Inspect discover_output/*.json")


def _extract_ids(body) -> list:
    if isinstance(body, list):
        return [item.get("id") for item in body if isinstance(item, dict) and "id" in item]
    if isinstance(body, dict):
        for key in ("data", "customers", "results"):
            if key in body and isinstance(body[key], list):
                return [item.get("id") for item in body[key] if isinstance(item, dict) and "id" in item]
    return []


if __name__ == "__main__":
    main()
