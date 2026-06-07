"""
jarvis_main.py  —  integrates the new GUI.

Run with:   python jarvis_main.py
The GUI window appears, all log lines go there instead of PowerShell.
"""

from config import *

import sys
import os
_base = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _base)
sys.path.insert(0, os.path.join(_base, "gui"))

import threading
import time
from typing import Optional

# ── GUI first (must create QApplication before anything else) ─────────────────
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

import jarvis_gui as gui

app = QApplication(sys.argv)
window = gui.JarvisWindow()
window.show()

# ── Core imports ──────────────────────────────────────────────────────────────
from core.ai import ask_ollama, clear_memory, get_memory_summary
from core.speech import record_audio, transcribe, speak
from core.shortcuts import open_shortcut
from core.navigation import search_current_folder, open_numbered_item
from core.app_control import close_app_or_window, handle_file_commands
from core.file_reader import read_file_from_current_folder, explain_last_file
from core.system_control import handle_system_command
from core.weather import handle_time_weather
from core.web_search import handle_web_search

import core.state as state
import keyboard
import os

# ── Wire GUI up ───────────────────────────────────────────────────────────────

def _clear_memory_from_gui():
    clear_memory()

gui.set_memory_clear_callback(_clear_memory_from_gui)

# Patch state so folder changes reflect in the GUI sidebar
_orig_folder = None

_last_folder: list = [None]

def _sync_folder():
    """Called every 500 ms — syncs state.CURRENT_FOLDER to sidebar."""
    if state.CURRENT_FOLDER != _last_folder[0]:
        gui.set_folder(state.CURRENT_FOLDER or "none")
        _last_folder[0] = state.CURRENT_FOLDER

folder_timer = QTimer()
folder_timer.timeout.connect(_sync_folder)
folder_timer.start(500)

# ── Redirect print → GUI log ───────────────────────────────────────────────────

import builtins
_real_print = builtins.print

def _gui_print(*args, **kwargs):
    text = " ".join(str(a) for a in args)
    _real_print(text, **kwargs)          # still goes to terminal if one is open

    tl = text.lower()
    if text.startswith("Jarvis:"):
        gui.log("jarvis", text[7:].strip())
    elif text.startswith("You:"):
        gui.log("user", text[4:].strip())
    elif "error" in tl or "warning" in tl:
        gui.log("error", text)
    else:
        gui.log("system", text)

builtins.print = _gui_print

# ── Startup ───────────────────────────────────────────────────────────────────

gui.log("system", f"Model: {OLLAMA_MODEL}")
gui.log("system", "F8 = talk  |  F9 = clear memory  |  F10 = exit")

if not os.path.exists(SHORTCUT_FOLDER):
    gui.log("error", f"Shortcut folder not found: {SHORTCUT_FOLDER}")

# ── Helpers ───────────────────────────────────────────────────────────────────

def handle(result: Optional[str]) -> bool:
    if result:
        gui.set_status("SPEAKING")
        speak(result)
        gui.set_status("READY")
        return True
    return False


# ── Main Jarvis loop (runs in background thread) ───────────────────────────────

def jarvis_loop():
    # Brief delay so the window renders first
    time.sleep(0.4)

    speak("Jarvis online. Ready when you are.")

    while True:
        gui.set_status("LISTENING")

        # Wait for F8 / F9 / F10
        while True:
            if keyboard.is_pressed("f10"):
                gui.log("system", "Shutting down.")
                speak("Shutting down. See you later.")
                QTimer.singleShot(0, app.quit)
                return

            if keyboard.is_pressed("f9"):
                clear_memory()
                gui.log("system", "Memory cleared.")
                speak("Memory cleared.")
                while keyboard.is_pressed("f9"):
                    time.sleep(0.05)

            if keyboard.is_pressed("f8"):
                while keyboard.is_pressed("f8"):
                    time.sleep(0.05)
                break

            time.sleep(0.05)

        # Record
        gui.set_status("RECORDING")
        record_audio()

        gui.set_status("THINKING")
        text = transcribe()

        if not text:
            gui.set_status("READY")
            continue

        gui.log("user", text)
        gui.set_command(text)

        t = text.lower().strip()

        # ── 1. Memory commands ────────────────────────────────────────────────
        if any(w in t for w in ["clear memory", "forget everything", "reset memory", "start fresh"]):
            clear_memory()
            handle("Memory cleared, starting fresh.")
            continue

        if any(w in t for w in ["what do you remember", "memory summary", "what have we talked about"]):
            handle(get_memory_summary())
            continue

        # ── 2. Time / weather ─────────────────────────────────────────────────
        result = handle_time_weather(text)
        if handle(result): continue

        # ── 3. System control ─────────────────────────────────────────────────
        result = handle_system_command(text)
        if handle(result): continue

        # ── 4. App shortcuts ──────────────────────────────────────────────────
        result = open_shortcut(text)
        if handle(result): continue

        # ── 5. Folder navigation ──────────────────────────────────────────────
        result = search_current_folder(text)
        if handle(result): continue

        # ── 6. File commands ──────────────────────────────────────────────────
        result = open_numbered_item(text)
        if handle(result): continue

        result = handle_file_commands(text)
        if handle(result): continue

        result = read_file_from_current_folder(text)
        if handle(result): continue

        # ── 7. Explain file ───────────────────────────────────────────────────
        if "explain this file" in t or "explain the file" in t:
            content = explain_last_file()
            if content:
                answer = ask_ollama("Explain this file:\n\n" + content)
                handle(answer)
            else:
                handle("No file loaded to explain.")
            continue

        # ── 8. Close apps ─────────────────────────────────────────────────────
        result = close_app_or_window(text)
        if handle(result): continue

        # ── 9. Web search ─────────────────────────────────────────────────────
        result = handle_web_search(text, ask_ollama)
        if handle(result): continue

        # ── 10. Fallback AI ───────────────────────────────────────────────────
        answer = ask_ollama(text)
        handle(answer)

        gui.set_status("READY")


# Run jarvis_loop in a daemon thread so it doesn't block the Qt event loop
t = threading.Thread(target=jarvis_loop, daemon=True)
t.start()

sys.exit(app.exec())