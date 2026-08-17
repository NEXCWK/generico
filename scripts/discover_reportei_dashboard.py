"""Discovers how Reportei's rendered dashboard pages fetch their widget data,
by opening the public share links for the "[WEEKLY] TT" and "[WEEKLY] Sales"
dashboards (found via the API in round 1) and capturing XHR/fetch calls.
No login needed — these are public share URLs.
"""

from __future__ import annotations

import json

from playwright.sync_api import sync_playwright

DASHBOARDS = {
    "WEEKLY_TT": "https://app.reportei.com/dashboard/J7oz6UfwKHJlU4sXudDmgeZbKbs2QzIG",
    "WEEKLY_Sales": "https://app.reportei.com/dashboard/d4CLKoh3AweubvVlEIbeJqTgStcFDsD6",
}

captured = []


def log_response(response):
    try:
        url = response.url
        if any(seg in url for seg in [".js", ".css", ".png", ".svg", ".woff", ".ico", ".jpg"]):
            return
        ctype = response.headers.get("content-type", "")
        if "json" not in ctype:
            return
        try:
            body = response.json()
        except Exception:  # noqa: BLE001
            return
        captured.append({"url": url, "status": response.status, "body": body})
    except Exception:  # noqa: BLE001
        pass


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, url in DASHBOARDS.items():
            captured.clear()
            page = browser.new_page()
            page.on("response", log_response)
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(4000)
            except Exception as e:  # noqa: BLE001
                print(f"error loading {name}: {e}")
            print(f"\n=== {name} ({url}) -> {len(captured)} JSON responses ===")
            for entry in captured:
                print(f"{entry['status']} {entry['url']}")
            for entry in captured[:8]:
                text = json.dumps(entry["body"], indent=2, ensure_ascii=False, default=str)
                if len(text) > 2500:
                    text = text[:2500] + f"... [truncated, {len(text)} chars]"
                print(f"\n--- body: {entry['url']} ---\n{text}")
            page.close()
        browser.close()

    print("\nDashboard discovery complete.")


if __name__ == "__main__":
    main()
