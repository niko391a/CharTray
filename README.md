# CharTray <img width="40" height="36" alt="Adobe Express - file" src="https://github.com/user-attachments/assets/2b52be81-c8ff-46fc-827f-4da47054f1bf" />

A Windows system tray app that counts characters in any text you select,
anywhere on your PC (browsers, editors, PDFs, terminals, etc.).

## How it works

1. Select/highlight any text in any application
2. Press **Ctrl+C**
3. The tray icon near your clock updates with the character count
4. Hover over the icon for a full breakdown (chars, chars with spaces, words)
5. The icon resets after 10 seconds of inactivity
6. Right-click the tray icon -> Quit to exit

## Build it yourself (Windows only)

Requirements: Python 3.9+ installed and on PATH

```
build_windows.bat
```

The exe will appear in `dist\CharTray.exe`. No installer needed -- just run it.
Double-click to start; it will appear silently in your system tray.

## Run from source (no build needed)

```
pip install pystray pillow pyperclip keyboard
python chartray.py
```

## Make it start with Windows

1. Press Win+R, type `shell:startup`, press Enter
2. Copy a shortcut to `CharTray.exe` into that folder

## How it captures your selection

CharTray monitors the clipboard, reads it, counts it, then leaves the clipboard as-is ***(everything local!)***.
It works in any app that supports standard copy -- browsers, VS Code, Word, Notepad, terminals, PDFs in Acrobat, etc.
