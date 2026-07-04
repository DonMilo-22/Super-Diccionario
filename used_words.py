import json
import os

APP_FOLDER = os.path.expanduser(
    "~/Library/Application Support/WordHelper"
)

os.makedirs(
    APP_FOLDER,
    exist_ok=True
)

FILE = os.path.join(
    APP_FOLDER,
    "used_words.json"
)


def load_used():

    if not os.path.exists(FILE):
        return set()

    try:
        with open(FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data.get("used", []))
    except:
        return set()


def save_used(words):

    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"used": list(words)},
            f,
            indent=4,
            ensure_ascii=False
        )


def add_used(word):

    words = load_used()
    words.add(word.lower())
    save_used(words)


def clear_used():

    save_used(set())