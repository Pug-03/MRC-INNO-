"""LINE notification stub.

LINE Notify was discontinued 2025-03-31. This module keeps the /api/notify/line
endpoint working: if LINE_CHANNEL_TOKEN + LINE_TARGET_ID are set, it pushes via
the LINE Messaging API (push endpoint). Otherwise it just records the message
in an in-memory log so the frontend can confirm the call went through.
"""

from __future__ import annotations

import logging
from collections import deque
from datetime import datetime

import httpx

from .config import LINE_CHANNEL_TOKEN, LINE_TARGET_ID, LINE_WEBHOOK_URL

log = logging.getLogger(__name__)

_history: deque[dict] = deque(maxlen=50)


async def send_line(message: str) -> dict:
    ts = datetime.now().isoformat(timespec="seconds")
    delivered = False
    transport = "log-only"
    detail: str | None = None

    try:
        if LINE_CHANNEL_TOKEN and LINE_TARGET_ID:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.post(
                    "https://api.line.me/v2/bot/message/push",
                    headers={
                        "Authorization": f"Bearer {LINE_CHANNEL_TOKEN}",
                        "Content-Type": "application/json",
                    },
                    json={"to": LINE_TARGET_ID, "messages": [{"type": "text", "text": message}]},
                )
                delivered = r.status_code < 300
                transport = "messaging-api"
                if not delivered:
                    detail = f"HTTP {r.status_code}: {r.text[:200]}"
        elif LINE_WEBHOOK_URL:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.post(LINE_WEBHOOK_URL, json={"message": message})
                delivered = r.status_code < 300
                transport = "webhook"
                if not delivered:
                    detail = f"HTTP {r.status_code}"
    except Exception as e:
        detail = str(e)
        log.exception("notify.send_line failed")

    record = {
        "ts": ts,
        "message": message,
        "delivered": delivered,
        "transport": transport,
        "detail": detail,
    }
    _history.appendleft(record)
    return record


def history() -> list[dict]:
    return list(_history)
