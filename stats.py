import json
import os
import tempfile
from datetime import datetime

from used_words import APP_FOLDER


FILE = os.path.join(APP_FOLDER, "stats.json")


def _default():
    return {
        "total_words": 0,
        "sessions": 0,
        "words": {},
        "favorites": [],
        "session_started_at": None,
        "session_words": 0,
    }


def load_stats():
    if not os.path.exists(FILE):
        return _default()
    try:
        with open(FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, dict):
            return _default()
    except (OSError, json.JSONDecodeError):
        return _default()

    result = _default()
    result.update(data)
    return result


def save_stats(stats):
    os.makedirs(APP_FOLDER, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix="stats_", suffix=".json", dir=APP_FOLDER)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(stats, file, indent=2, ensure_ascii=False)
        os.replace(temp_path, FILE)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def start_session():
    stats = load_stats()
    stats["sessions"] = int(stats.get("sessions", 0)) + 1
    stats["session_started_at"] = datetime.now().isoformat(timespec="seconds")
    stats["session_words"] = 0
    save_stats(stats)
    return stats


def record_word(word):
    stats = load_stats()
    key = word.lower()
    stats["total_words"] = int(stats.get("total_words", 0)) + 1
    stats["session_words"] = int(stats.get("session_words", 0)) + 1
    words = stats.setdefault("words", {})
    words[key] = int(words.get(key, 0)) + 1
    save_stats(stats)
    return stats


def toggle_favorite(word):
    stats = load_stats()
    favorites = {item.lower() for item in stats.get("favorites", [])}
    key = word.lower()
    if key in favorites:
        favorites.remove(key)
        enabled = False
    else:
        favorites.add(key)
        enabled = True
    stats["favorites"] = sorted(favorites)
    save_stats(stats)
    return enabled


def favorites():
    return set(load_stats().get("favorites", []))


def usage_counts():
    return load_stats().get("words", {})
