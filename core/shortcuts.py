import os
import win32com.client

from config import *

import core.state as state


def get_shortcut_target(shortcut_path):
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(shortcut_path)
    return shortcut.Targetpath

def open_shortcut(command):

    command = command.lower().strip()

    for c in ".,!?":
        command = command.replace(c, "")

    # only short commands
    if len(command.split()) > 4:
        return None

    OPEN_WORDS = [
        "open",
        "launch",
        "start",
        "show"
    ]

    if not any(
        command.startswith(word)
        for word in OPEN_WORDS
    ):
        return None

    aliases = {
        "resume": "cv",
        "curriculum vitae": "cv",
        "counter strike": "counter strike 2",
        "cs2": "counter strike 2",
        "solidworks": "solid works",
        "vscode": "vs code"
    }

    for alias, target in aliases.items():

        if alias in command:
            command += " " + target

    for file in os.listdir(SHORTCUT_FOLDER):

        if not (
            file.lower().endswith(".lnk")
            or
            file.lower().endswith(".url")
        ):
            continue

        shortcut_name = os.path.splitext(
            file
        )[0].lower()

        if shortcut_name in command:

            path = os.path.join(
                SHORTCUT_FOLDER,
                file
            )

            target = get_shortcut_target(path)

            os.startfile(path)

            if os.path.isdir(target):

                if state.CURRENT_FOLDER:
                    state.FOLDER_HISTORY.append(
                        state.CURRENT_FOLDER
                    )

                state.CURRENT_FOLDER = target

            print(
                "CURRENT_FOLDER =",
                state.CURRENT_FOLDER
            )

            return f"Opening {shortcut_name}"

    return None