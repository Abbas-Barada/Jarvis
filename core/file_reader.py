import os

import core.state as state

def set_last_file(path):
    state.LAST_FILE = path

def read_last_file():

    if not state.LAST_FILE:
        return None

    try:

        with open(
            state.LAST_FILE,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as f:

            return f.read(5000)

    except Exception:
        return None

def read_file_from_current_folder(command):

    if not state.CURRENT_FOLDER:
        return None

    text = command.lower()

    if not text.startswith("read"):
        return None

    query = text.replace("read", "").strip()

    for root, dirs, files in os.walk(state.CURRENT_FOLDER):

        for file in files:

            if query in file.lower():

                path = os.path.join(root, file)

                state.LAST_FILE = path

                try:

                    with open(
                        path,
                        "r",
                        encoding="utf-8",
                        errors="ignore"
                    ) as f:

                        content = f.read()

                    return (
                        "FILE CONTENT:\n\n"
                        + content[:12000]
                    )

                except Exception:

                    return (
                        f"Cannot read {file}. "
                        f"It may be binary."
                    )

    return None

def explain_last_file():

    if not state.LAST_FILE:
        return None

    try:

        with open(
            state.LAST_FILE,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as f:

            return f.read()[:12000]

    except Exception:
        return None
