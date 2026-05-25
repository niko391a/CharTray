"""
CharTray - System tray character counter
Copy text normally (Ctrl+C) and the tray icon updates automatically.
The tray icon tooltip shows the live count.
"""

import threading
import time
import sys
import os
import pyperclip
import pystray
from PIL import Image, ImageDraw, ImageFont


# ── Config ────────────────────────────────────────────────────────────────────
POLL_INTERVAL = 0.3     # seconds between clipboard polls
ICON_SIZE = 64          # pixels; Windows tray icons are typically 16x16 but PIL scales down
FONT_SIZE = 34          # font size inside the generated icon image
RESET_AFTER = 25        # seconds before icon resets to idle state


# ── Icon generation ───────────────────────────────────────────────────────────

def make_icon(text: str, bg: tuple, fg: tuple) -> Image.Image:
    """Render a small PIL image with `text` centred on a coloured background."""
    img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), bg)
    draw = ImageDraw.Draw(img)

    # Try to load a compact system font; fall back to PIL default
    font = None
    candidates = [
        "arialbd.ttf", "arial.ttf",   # Windows
        "DejaVuSans-Bold.ttf",         # Linux
    ]
    for name in candidates:
        try:
            font = ImageFont.truetype(name, FONT_SIZE)
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default()

    # Centre the text
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (ICON_SIZE - w) / 2 - bbox[0]
    y = (ICON_SIZE - h) / 2 - bbox[1]
    draw.text((x, y), text, font=font, fill=fg)
    return img


def idle_icon() -> Image.Image:
    """Grey icon shown when no selection has been counted yet."""
    return make_icon("Ch", bg=(60, 60, 60, 255), fg=(200, 200, 200, 255))


def count_icon(n: int) -> Image.Image:
    """Blue icon showing the character count (abbreviated if large)."""
    label = str(n) if n < 1000 else f"{n//1000}k"
    return make_icon(label, bg=(30, 100, 200, 255), fg=(255, 255, 255, 255))


def error_icon() -> Image.Image:
    """Red icon shown when clipboard access fails."""
    return make_icon("Err", bg=(180, 30, 30, 255), fg=(255, 255, 255, 255))


# ── State ──────────────────────────────────────────────────────────────────────

class AppState:
    def __init__(self):
        self.tray: pystray.Icon | None = None
        self.last_text: str = ""
        self.char_count: int = 0          # no spaces
        self.char_count_spaces: int = 0   # with spaces
        self.word_count: int = 0
        self._reset_timer: threading.Timer | None = None

    def update_counts(self, text: str):
        self.last_text = text
        self.char_count_spaces = len(text)
        self.char_count = len(text.replace(" ", "").replace("\t", "").replace("\n", ""))
        self.word_count = len(text.split()) if text.strip() else 0

    def tooltip(self) -> str:
        return (
            f"CharTray\n"
            f"Chars (no spaces): {self.char_count}\n"
            f"Chars (with spaces): {self.char_count_spaces}\n"
            f"Words: {self.word_count}"
        )


state = AppState()


# ── Clipboard monitor ──────────────────────────────────────────────────────────

def monitor_clipboard():
    """Poll clipboard and update counts whenever content changes (triggered by Ctrl+C)."""
    previous = ""
    while True:
        try:
            current = pyperclip.paste()
        except Exception:
            time.sleep(POLL_INTERVAL)
            continue

        if current != previous and current.strip():
            previous = current
            if state.tray is not None:
                state.update_counts(current)
                state.tray.icon = count_icon(state.char_count_spaces)
                state.tray.title = state.tooltip()
                state.tray.update_menu()

                if state._reset_timer:
                    state._reset_timer.cancel()
                state._reset_timer = threading.Timer(RESET_AFTER, reset_icon)
                state._reset_timer.daemon = True
                state._reset_timer.start()

        time.sleep(POLL_INTERVAL)


def reset_icon():
    if state.tray:
        state.tray.icon = idle_icon()
        state.tray.title = "CharTray  |  Copy text (Ctrl+C) to count"


# ── Tray menu ──────────────────────────────────────────────────────────────────

def quit_app(icon, item):
    icon.stop()


def build_menu():
    return pystray.Menu(
        pystray.MenuItem("CharTray", None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            lambda item: (
                f"Chars (no spaces): {state.char_count}"
                if state.char_count else "No text copied yet"
            ),
            None, enabled=False
        ),
        pystray.MenuItem(
            lambda item: f"Chars (with spaces): {state.char_count_spaces}",
            None, enabled=False
        ),
        pystray.MenuItem(
            lambda item: f"Words: {state.word_count}",
            None, enabled=False
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", quit_app),
    )


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    t = threading.Thread(target=monitor_clipboard, daemon=True)
    t.start()

    icon = pystray.Icon(
        name="CharTray",
        icon=idle_icon(),
        title="CharTray  |  Copy text (Ctrl+C) to count",
        menu=build_menu(),
    )
    state.tray = icon

    print("CharTray running. Copy any text (Ctrl+C) to count it.  |  Right-click tray icon to quit.")
    icon.run()   # blocks until quit_app() calls icon.stop()


if __name__ == "__main__":
    main()
