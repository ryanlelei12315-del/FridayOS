"""Optional client for the local JarvisBridge wallpaper service.

The bridge is a separate Node.js process listening on 127.0.0.1:3000.
All calls are best-effort: an unavailable wallpaper must never crash FRIDAY.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Literal

BridgeState = Literal["idle", "listening", "thinking", "speaking"]
BridgeLevel = Literal["info", "warn", "critical"]

BRIDGE_URL = os.getenv("JARVIS_BRIDGE_URL", "http://127.0.0.1:3000").rstrip("/")


def _post(path: str, payload: dict, timeout: float = 0.35) -> int | None:
    request = urllib.request.Request(
        f"{BRIDGE_URL}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.load(response)
            return int(body.get("delivered", 0))
    except (urllib.error.URLError, OSError, ValueError, TimeoutError):
        return None


def jarvis_state(state: BridgeState, timeout: float = 0.35) -> int | None:
    """Publish FRIDAY's state to the wallpaper; returns None if bridge is offline."""
    if state not in ("idle", "listening", "thinking", "speaking"):
        raise ValueError(f"Unsupported JarvisBridge state: {state}")
    return _post("/state", {"state": state}, timeout)


def jarvis_say(
    text: object,
    level: BridgeLevel = "info",
    speak: bool = True,
    timeout: float = 0.35,
) -> int | None:
    """Show a wallpaper alert. Use speak=False when FRIDAY already speaks the reply."""
    if level not in ("info", "warn", "critical"):
        raise ValueError(f"Unsupported JarvisBridge alert level: {level}")
    message = str(text).strip()
    if not message:
        return 0
    return _post(
        "/alert",
        {"text": message[:500], "level": level, "speak": bool(speak)},
        timeout,
    )


def jarvis_health(timeout: float = 0.35) -> dict | None:
    """Return bridge health JSON, or None when the local service is unavailable."""
    request = urllib.request.Request(f"{BRIDGE_URL}/health", method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
            return payload if isinstance(payload, dict) else None
    except (urllib.error.URLError, OSError, ValueError, TimeoutError):
        return None
