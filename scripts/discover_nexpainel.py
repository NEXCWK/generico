"""One-off discovery script: logs into nexpainel.lovable.app, opens /tt-semanal,
and dumps the rendered HTML, a screenshot, and every network request/response
seen along the way (many Lovable/Supabase apps call a REST API directly —
capturing that is often more useful than scraping the DOM).

Run only via the "discover" GitHub Actions workflow. Writes to
discover_output/nexpainel/ as a workflow artifact.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

EMAIL = os.environ["NEXPAINEL_EMAIL"]
PASSWORD = os.environ["NEXPAINEL_PASSWORD"]
TARGET_URL = "https://nexpainel.lovable.app/tt-semanal"

OUT_DIR = Path("discover_output/nexpainel")
OUT_DIR.mkdir(parents=True, exist_ok=True)

network_log = []


def log_response(response):
    try:
        url = response.url
        if any(url.endswith(ext) for ext in [".js", ".css", ".png", ".svg", ".woff2", ".ico"]):
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
        page.screenshot(path=str(OUT_DIR / "01_landing.png"))
        (OUT_DIR / "01_landing.html").write_text(page.content(), encoding="utf-8")

        _try_login(page)

        page.goto(TARGET_URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3000)
        page.screenshot(path=str(OUT_DIR / "02_tt_semanal.png"), full_page=True)
        (OUT_DIR / "02_tt_semanal.html").write_text(page.content(), encoding="utf-8")

        (OUT_DIR / "network_log.json").write_text(
            json.dumps(network_log, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
        )
        browser.close()

    print(f"\ncurrent URL after login+navigation attempt: (see network log below)")
    print(f"\n=== network_log.json ({len(network_log)} entries) ===")
    text = json.dumps(network_log, indent=2, ensure_ascii=False, default=str)
    if len(text) > 12000:
        text = text[:12000] + f"\n... [truncated, {len(text)} chars total]"
    print(text)

    html = (OUT_DIR / "02_tt_semanal.html").read_text(encoding="utf-8")
    print(f"\n=== 02_tt_semanal.html (first 3000 chars of {len(html)}) ===")
    print(html[:3000])

    print(f"\nDiscovery complete. Inspect {OUT_DIR}/")


def _try_login(page) -> None:
    email_selectors = ['input[type="email"]', 'input[name="email"]', 'input[placeholder*="mail" i]']
    password_selectors = ['input[type="password"]', 'input[name="password"]']

    email_input = _first_visible(page, email_selectors)
    if not email_input:
        print("No email input found on landing page — app may already show a login link/button.")
        for text in ["Entrar", "Login", "Log in", "Sign in"]:
            btn = page.get_by_text(text, exact=False)
            if btn.count() > 0:
                btn.first.click()
                page.wait_for_timeout(1500)
                break
        email_input = _first_visible(page, email_selectors)

    if email_input:
        email_input.fill(EMAIL)
        pwd_input = _first_visible(page, password_selectors)
        if pwd_input:
            pwd_input.fill(PASSWORD)
        page.keyboard.press("Enter")
        page.wait_for_timeout(3000)
    else:
        print("WARNING: could not locate a login form — dumping page as-is for manual inspection.")


def _first_visible(page, selectors: list[str]):
    for sel in selectors:
        loc = page.locator(sel)
        if loc.count() > 0 and loc.first.is_visible():
            return loc.first
    return None


if __name__ == "__main__":
    main()
