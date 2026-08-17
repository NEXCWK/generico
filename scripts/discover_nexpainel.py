"""Round 2 of nexpainel discovery: the app is Supabase-backed (confirmed via
round 1's network log — login hits {project}.supabase.co/auth/v1/token, then
the UI queries {project}.supabase.co/rest/v1/<table> with a bearer JWT).

This round prints a compact index of every rest/v1 and rpc call seen while
navigating to /tt-semanal (url + method + status only, so it fits in the log
without truncation), then full bodies only for the calls whose table/function
name looks sales/weekly related.
"""

from __future__ import annotations

import json
import os
import re

from playwright.sync_api import sync_playwright

EMAIL = os.environ["NEXPAINEL_EMAIL"]
PASSWORD = os.environ["NEXPAINEL_PASSWORD"]
TARGET_URL = "https://nexpainel.lovable.app/tt-semanal"

INTERESTING = re.compile(
    r"venda|reserva|weekly|semanal|fatura|receita|produto|funil|linha|deal|lead|invest|ads|roas|booking|contrato",
    re.IGNORECASE,
)

network_log = []


def log_response(response):
    try:
        url = response.url
        if "supabase.co" not in url:
            return
        if any(seg in url for seg in ["/auth/v1/", "/storage/v1/"]):
            return
        entry = {"url": url, "status": response.status, "method": response.request.method}
        ctype = response.headers.get("content-type", "")
        if "json" in ctype:
            try:
                entry["body"] = response.json()
            except Exception:  # noqa: BLE001
                entry["body"] = None
        network_log.append(entry)
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

    print(f"\n=== rest/v1 + rpc calls index ({len(network_log)} total) ===")
    for e in network_log:
        path = e["url"].split("supabase.co", 1)[-1]
        print(f"{e['method']} {e['status']} {path}")

    print("\n=== full bodies for interesting calls ===")
    for e in network_log:
        path = e["url"].split("supabase.co", 1)[-1]
        if INTERESTING.search(path) and e.get("body") is not None:
            text = json.dumps(e["body"], indent=2, ensure_ascii=False, default=str)[:4000]
            print(f"\n--- {e['method']} {path} ---\n{text}")

    print("\nDiscovery round 2 complete.")


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
    else:
        print("WARNING: could not locate a login form.")


def _first_visible(page, selectors: list[str]):
    for sel in selectors:
        loc = page.locator(sel)
        if loc.count() > 0 and loc.first.is_visible():
            return loc.first
    return None


if __name__ == "__main__":
    main()
