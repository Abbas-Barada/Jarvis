import os
import re

import core.state as state


def search_current_folder(command):

    if not state.CURRENT_FOLDER:
        return None

    text = command.lower()

    for c in ".,!?":
        text = text.replace(c, "")

    remove_words = [
        "open",
        "find",
        "search",
        "show",
        "locate",
        "go to",
        "inside",
        "folder",
        "file",
        "document",
        "documents"
    ]

    query = text

    for word in remove_words:
        query = query.replace(word, "")

    query = query.strip()

    if not query:
        return None

    print("SEARCHING IN:", state.CURRENT_FOLDER)
    print("QUERY:", query)

    for root, dirs, files in os.walk(state.CURRENT_FOLDER):

        # folders
        for folder in dirs:

            query_words = query.split()

            if all(
                word in folder.lower()
                for word in query_words
            ):

                path = os.path.join(root, folder)

                os.startfile(path)

                if state.CURRENT_FOLDER:
                    state.FOLDER_HISTORY.append(
                        state.CURRENT_FOLDER
                    )

                state.CURRENT_FOLDER = path

                return f"Opening folder {folder}"

        # files
        for file in files:

            query_words = query.split()

            if all(
                word in file.lower()
                for word in query_words
            ):

                path = os.path.join(root, file)

                os.startfile(path)

                return f"Opening {file}"

    return None

def list_current_folder():

    if not state.CURRENT_FOLDER:
        return None

    try:

        items = os.listdir(state.CURRENT_FOLDER)

        if not items:
            return "This folder is empty."

        folders = []
        files = []

        state.LAST_LIST = []

        for item in items:

            path = os.path.join(
                state.CURRENT_FOLDER,
                item
            )

            if os.path.isdir(path):
                folders.append(item)
                state.LAST_LIST.append(path)
            else:
                files.append(item)
                state.LAST_LIST.append(path)

        response = "Current folder contains: "

        if folders:
            response += (
                "Folders: "
                + ", ".join(folders[:10])
            )

        if files:
            response += (
                ". Files: "
                + ", ".join(files[:10])
            )

        return response

    except Exception as e:
        return f"Error reading folder: {e}"

def open_numbered_item(command):

    m = re.search(
        r"(?:open|show)\s+(?:number|file|folder)?\s*(\d+)",
        command.lower()
    )

    if not m:
        return None

    if not state.LAST_LIST:
        return "No numbered list available."

    idx = int(m.group(1)) - 1

    if idx < 0 or idx >= len(state.LAST_LIST):
        return "Invalid number."

    path = state.LAST_LIST[idx]

    os.startfile(path)

    if os.path.isdir(path):

        if state.CURRENT_FOLDER:
            state.FOLDER_HISTORY.append(
                state.CURRENT_FOLDER
            )

        state.CURRENT_FOLDER = path

    return f"Opening {os.path.basename(path)}"
