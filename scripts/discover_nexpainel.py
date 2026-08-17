"""Round 3 of nexpainel discovery: we now know the app queries a Supabase
`sales` table (date-filtered, status-filtered) and a `revenue_classification_rules`
table. This round prints the FULL body of one `sales` page, the full
`revenue_classification_rules` table, and a sample of `contracts` (for
subscription-style products like Escritório Virtual), to learn the exact
columns available for grouping into Nex's 4 product lines.
"""

from __future__ import annotations

import json
import os

from playwright.sync_api import sync_playwright

EMAIL = os.environ["NEXPAINEL_EMAIL"]
PASSWORD = os.environ["NEXPAINEL_PASSWORD"]
TARGET_URL = "https://nexpainel.lovable.app/tt-semanal"

WANTED_SUBSTRINGS = ["/rest/v1/sales?", "/rest/v1/revenue_classification_rules", "/rest/v1/contracts?"]

captured = {}


def log_response(response):
    try:
        url = response.url
        if "supabase.co" not in url or "/rest/v1/" not in url:
            return
        path = url.split("supabase.co", 1)[-1]
        for w in WANTED_SUBSTRINGS:
            if w in path and w not in captured:
                ctype = response.headers.get("content-type", "")
                if "json" in ctype:
                    try:
                        captured[w] = {"url": path, "body": response.json()}
                    except Exception:  # noqa: BLE001
                        pass
    except Exception:  # noqa: BLE001
        pass


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.on("response", log_response)

        page.goto("https://nexpainel.lovable.app/", wait_until="networkidle", timeout=30000)
        _try_login(page)

        page.goto(TARGET_URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(4000)
        browser.close()

    for key, entry in captured.items():
        body = entry["body"]
        if isinstance(body, list):
            sample = body[:2]
            print(f"\n=== {key} -> {entry['url']} ===")
            print(f"(list of {len(body)} items, showing first 2)")
            print(json.dumps(sample, indent=2, ensure_ascii=False, default=str)[:6000])
        else:
            print(f"\n=== {key} -> {entry['url']} ===")
            print(json.dumps(body, indent=2, ensure_ascii=False, default=str)[:6000])

    missing = [w for w in WANTED_SUBSTRINGS if w not in captured]
    if missing:
        print(f"\nNot captured this run: {missing}")

    print("\nDiscovery round 3 complete.")


def _try_login(page) -> None:
    email_selectors = ['input[type="email"]', 'input[name="email"]', 'input[placeholder*="mail" i]']
    password_selectors = ['input[type="password"]', 'input[name="password"]']
    email_input = _first_visible(page, email_selectors)
    if email_input:
        email_input.fill(EMAIL)
        pwd_input = _first_visible(page, password_selectors)
        if pwd_input:
            pwd_input.fill(PASSWORD)
        page.keyboard.press("Enter")
        page.wait_for_timeout(3000)


def _first_visible(page, selectors: list[str]):
    for sel in selectors:
        loc = page.locator(sel)
        if loc.count() > 0 and loc.first.is_visible():
            return loc.first
    return None


if __name__ == "__main__":
    main()
