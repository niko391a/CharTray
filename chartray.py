"""
CharTray - System tray character counter
Press Ctrl+Shift+C anywhere to count characters in your current selection.
The tray icon tooltip shows the live count.
"""

import threading
import time
import sys
import os
import pyperclip
import keyboard
import pystray
from PIL import Image, ImageDraw, ImageFont


# ── Config ────────────────────────────────────────────────────────────────────
HOTKEY = "ctrl+shift+c"
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
            f"Words: {self.word_count}\n"
            f"\nHotkey: {HOTKEY.upper()}"
        )


state = AppState()


# ── Hotkey handler ─────────────────────────────────────────────────────────────

def on_hotkey():
    """
    Called when the user presses the hotkey.
    Strategy: simulate Ctrl+C to copy the current selection, then read
    the clipboard. We save and restore whatever was in the clipboard before.
    """
    if state.tray is None:
        return

    # Save previous clipboard content so we don't clobber it permanently
    try:
        previous = pyperclip.paste()
    except Exception:
        previous = ""

    # Simulate copy -- this works in browsers, editors, terminals, etc.
    keyboard.send("ctrl+c")
    time.sleep(0.15)   # small delay to let the OS process the copy

    try:
        text = pyperclip.paste()
    except Exception:
        state.tray.icon = error_icon()
        state.tray.title = "CharTray - clipboard error"
        return

    # If clipboard didn't change, there was likely no selection
    if text == previous and text == state.last_text:
        return

    state.update_counts(text)

    # Update the tray icon and tooltip
    state.tray.icon = count_icon(state.char_count_spaces)
    state.tray.title = state.tooltip()

    # Schedule a reset back to idle after RESET_AFTER seconds
    if state._reset_timer:
        state._reset_timer.cancel()
    state._reset_timer = threading.Timer(RESET_AFTER, reset_icon)
    state._reset_timer.daemon = True
    state._reset_timer.start()


def reset_icon():
    if state.tray:
        state.tray.icon = idle_icon()
        state.tray.title = f"CharTray  |  {HOTKEY.upper()} to count selection"


# ── Tray menu ──────────────────────────────────────────────────────────────────

def quit_app(icon, item):
    icon.stop()
    # keyboard.unhook_all() is called implicitly when the process exits


def build_menu():
    return pystray.Menu(
        pystray.MenuItem("CharTray", None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            lambda item: (
                f"Chars (no spaces): {state.char_count}\n"
                if state.char_count else "No selection counted yet"
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
        pystray.MenuItem(f"Hotkey: {HOTKEY.upper()}", None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", quit_app),
    )


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    # Register global hotkey in a background thread
    keyboard.add_hotkey(HOTKEY, on_hotkey)

    icon = pystray.Icon(
        name="CharTray",
        icon=idle_icon(),
        title=f"CharTray  |  {HOTKEY.upper()} to count selection",
        menu=build_menu(),
    )
    state.tray = icon

    print(f"CharTray running. Hotkey: {HOTKEY.upper()}  |  Right-click tray icon to quit.")
    icon.run()   # blocks until quit_app() calls icon.stop()


if __name__ == "__main__":
    main()
