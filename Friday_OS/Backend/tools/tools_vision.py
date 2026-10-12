"""Local desktop screenshot capture for FridayOS visual-context requests."""

import asyncio
from datetime import datetime
from pathlib import Path

import pyautogui
from livekit.agents import function_tool

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


@function_tool(
    description=(
        "Captures the primary monitor on the local Windows host for user-requested "
        "visual context such as code errors, terminal output, designs, or documents."
    )
)
async def capture_active_screen() -> str:
    """Capture and save a PNG screenshot without blocking the asyncio event loop."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        screenshot_path = CACHE_DIR / f"live_ctx_{timestamp}.png"
        screenshot = await asyncio.to_thread(pyautogui.screenshot)
        await asyncio.to_thread(screenshot.save, str(screenshot_path), "PNG")
        return (
            f"Screenshot saved locally at {screenshot_path}. The file is not "
            "automatically attached to the model's vision input; an image-capable "
            "analysis path must load it before visual analysis can occur."
        )
    except Exception as exc:
        return f"Screen capture failed: {type(exc).__name__}: {exc}"
