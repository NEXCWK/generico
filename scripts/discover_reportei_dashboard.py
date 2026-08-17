"""Round 2: the previous run showed Reportei's dashboard pages call
`/broadcasting/auth-external` (a Laravel Echo / Pusher auth handshake) but no
REST endpoint carrying actual widget values — meaning the widget data most
likely arrives over a WebSocket (Pusher) channel, not a plain HTTP response.

This round listens for WebSocket connections and frames instead of HTTP
responses, on the same public dashboard share URLs.
"""

from __future__ import annotations

import json

from playwright.sync_api import sync_playwright

DASHBOARDS = {
    "WEEKLY_TT": "https://app.reportei.com/dashboard/J7oz6UfwKHJlU4sXudDmgeZbKbs2QzIG",
    "WEEKLY_Sales": "https://app.reportei.com/dashboard/d4CLKoh3AweubvVlEIbeJqTgStcFDsD6",
}

ws_events = []


def on_websocket(ws):
    ws_events.append({"type": "open", "url": ws.url})
    ws.on("framereceived", lambda payload: ws_events.append({"type": "recv", "url": ws.url, "payload": _trunc(payload)}))
    ws.on("framesent", lambda payload: ws_events.append({"type": "sent", "url": ws.url, "payload": _trunc(payload)}))
    ws.on("close", lambda: ws_events.append({"type": "close", "url": ws.url}))


def _trunc(payload) -> str:
    s = payload if isinstance(payload, str) else repr(payload)
    return s[:3000]


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, url in DASHBOARDS.items():
            ws_events.clear()
            page = browser.new_page()
            page.on("websocket", on_websocket)
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(6000)
            except Exception as e:  # noqa: BLE001
                print(f"error loading {name}: {e}")

            print(f"\n=== {name} ({url}) -> {len(ws_events)} ws events ===")
            for e in ws_events:
                if e["type"] in ("open", "close"):
                    print(f"{e['type']} {e['url']}")
                else:
                    print(f"{e['type']} {e['url']}\n  {e['payload']}")
            page.close()
        browser.close()

    print("\nWebSocket discovery complete.")


if __name__ == "__main__":
    main()
