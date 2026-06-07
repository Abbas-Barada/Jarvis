from config import *

from core.ai import *
from core.speech import *
from core.shortcuts import *
from core.navigation import *
from core.app_control import *
from core.file_reader import *

import core.state as state
import keyboard
import time


print("================================")
print("Jarvis Ready")
print("Model:", OLLAMA_MODEL)
print("F8 = Start/Stop Recording")
print("Press F8 to talk")
print("================================")


while True:

    print("\nPress F8 to start recording...")

    keyboard.wait("f8")

    time.sleep(0.3)

    record_audio()

    text = transcribe()

    if not text:
        continue

    # shortcuts
    result = open_shortcut(text)

    if result:
        speak(result)
        continue

    # folder navigation
    result = search_current_folder(text)

    if result:
        speak(result)
        continue

    # open numbered item
    result = open_numbered_item(text)

    if result:
        speak(result)
        continue

    # file search (Everything)
    result = handle_file_commands(text)

    if result:
        speak(result)
        continue

    # read file
    result = read_file_from_current_folder(text)

    if result:
        speak(result)
        continue

    # explain last file
    if "explain this file" in text.lower():

        content = explain_last_file()

        if content:

            answer = ask_ollama(
                "Explain this file:\n\n" + content
            )

            speak(answer)

            continue

    # close apps
    result = close_app_or_window(text)

    if result:
        speak(result)
        continue

    # fallback AI
    answer = ask_ollama(text)

    speak(answer)
