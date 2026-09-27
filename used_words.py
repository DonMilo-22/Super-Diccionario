import json
import os
import platform
import tempfile


def _app_folder():
    override = os.environ.get("WORDHELPER_DATA_DIR")
    if override:
        return os.path.abspath(os.path.expanduser(override))

    system = platform.system()

    if system == "Windows":
        root = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(root, "WordHelper")

    if system == "Darwin":
        return os.path.expanduser("~/Library/Application Support/WordHelper")

    root = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return os.path.join(root, "WordHelper")


APP_FOLDER = _app_folder()
FILE = os.path.join(APP_FOLDER, "used_words.json")


def _ensure_folder():
    os.makedirs(APP_FOLDER, exist_ok=True)


def load_used():
    if not os.path.exists(FILE):
        return set()

    try:
        with open(FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return set()

    words = data.get("used", [])
    if not isinstance(words, list):
        return set()

    return {str(word).lower() for word in words}


def save_used(words):
    _ensure_folder()
    payload = {"used": sorted({str(word).lower() for word in words})}

    fd, temp_path = tempfile.mkstemp(
        prefix="used_words_",
        suffix=".json",
        dir=APP_FOLDER,
    )

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(payload, file, indent=4, ensure_ascii=False)
        os.replace(temp_path, FILE)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def add_used(word):
    words = load_used()
    words.add(word.lower())
    save_used(words)


def remove_used(word):
    words = load_used()
    words.discard(word.lower())
    save_used(words)


def clear_used():
    save_used(set())
