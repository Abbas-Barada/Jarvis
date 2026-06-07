import subprocess
import keyboard

from config import EVERYTHING_EXE


def handle_file_commands(text):
    command = text.lower().strip()

    # CV / Resume detection
    if any(word in command for word in ["cv", "resume", "curriculum vitae"]):
        subprocess.Popen([EVERYTHING_EXE, "-search", "*.pdf cv"])
        return "Searching for your CV."

    # General file searches
    keywords = {
        "autonomous": "autonomous",
        "arduino": "arduino",
        "pid": "pid",
        "solidworks": "*.sldprt",
        "report": "*.pdf",
        "presentation": "*.pptx",
    }

    for trigger, query in keywords.items():
        if trigger in command:
            subprocess.Popen([EVERYTHING_EXE, "-search", query])
            return f"Searching for {trigger} files."

    # Natural language file commands
    if any(word in command for word in ["find", "search", "locate", "open"]):
        query = (
            command.replace("find", "")
                   .replace("search", "")
                   .replace("locate", "")
                   .replace("open", "")
                   .strip()
        )

        if query:
            subprocess.Popen([EVERYTHING_EXE, "-search", query])
            return f"Searching for {query}."

    return None

def close_app_or_window(command):

    text = command.lower()

    if "close window" in text:
        keyboard.press_and_release("alt+f4")
        return "Closing window"

    processes = {
        "spotify": "Spotify.exe",
        "steam": "steam.exe",
        "discord": "Discord.exe",
        "vscode": "Code.exe",
        "vs code": "Code.exe",
        "solidworks": "SLDWORKS.exe",
        "opera": "opera.exe"
    }

    for app, proc in processes.items():

        if f"close {app}" in text:

            subprocess.run(
                ["taskkill", "/F", "/IM", proc],
                capture_output=True
            )

            return f"Closing {app}"

    return None
