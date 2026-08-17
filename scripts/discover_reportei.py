"""One-off discovery script: probes the Reportei API with the configured token
and prints raw responses to stdout (captured in the GitHub Actions job log)
so the real client (reportei_client.py) can be built against actual response
shapes instead of guessed ones.

Run only via the "discover" GitHub Actions workflow (needs real network
access, which local/sandboxed dev sessions may not have).
"""

from __future__ import annotations

import json
import os

import requests

TOKEN = os.environ["REPORTEI_API_TOKEN"]
BASE = "https://app.reportei.com/api/v1"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}

MAX_PRINT = 4000


def show(label: str, data) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False, default=str)
    if len(text) > MAX_PRINT:
        text = text[:MAX_PRINT] + f"\n... [truncated, {len(text)} chars total]"
    print(f"\n=== {label} ===\n{text}")


def get(path: str, params: dict | None = None) -> dict:
    url = f"{BASE}{path}"
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=20)
        try:
            body = resp.json()
        except Exception:  # noqa: BLE001
            body = resp.text[:2000]
        return {"url": url, "status": resp.status_code, "body": body}
    except Exception as e:  # noqa: BLE001
        return {"url": url, "error": str(e)}


def main() -> None:
    me = get("/me")
    show("GET /me", me)

    candidate_paths = [
        "/customers",
        "/accounts",
        "/companies",
        "/clients",
        "/workspaces",
        "/organizations",
        "/dashboards",
        "/reports",
        "/integrations",
        "/data-sources",
        "/connections",
        "/projects",
    ]
    found_lists = {}
    for path in candidate_paths:
        r = get(path)
        status = r.get("status")
        marker = "OK" if status == 200 else str(status or r.get("error"))
        print(f"probe {path}: {marker}")
        if status == 200:
            found_lists[path] = r
            show(f"GET {path}", r)

    ids_to_explore = []
    for path, r in found_lists.items():
        body = r.get("body")
        ids = _extract_ids(body)
        if ids:
            print(f"{path} -> ids found: {ids[:10]}")
            ids_to_explore.extend((path, i) for i in ids[:3])

    for path, cid in ids_to_explore[:6]:
        detail = get(f"{path}/{cid}")
        show(f"GET {path}/{cid}", detail)
        for sub in ["/integrations", "/data-sources", "/metrics", "/reports", "/campaigns", "/funnels"]:
            sub_resp = get(f"{path}/{cid}{sub}")
            if sub_resp.get("status") == 200:
                show(f"GET {path}/{cid}{sub}", sub_resp)

    print("\nDiscovery complete.")


def _extract_ids(body) -> list:
    if isinstance(body, list):
        return [item.get("id") for item in body if isinstance(item, dict) and "id" in item]
    if isinstance(body, dict):
        for key in ("data", "customers", "accounts", "results", "items"):
            if key in body and isinstance(body[key], list):
                return [item.get("id") for item in body[key] if isinstance(item, dict) and "id" in item]
    return []


if __name__ == "__main__":
    main()
