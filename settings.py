import json
import os
import tempfile

from used_words import APP_FOLDER


DEFAULT_SETTINGS = {
    "profile": "Roblox",
    "language": "both",
    "search_mode": "auto",
    "hotkey": "<alt>+<space>",
    "auto_enter": False,
    "auto_select_single": False,
    "common_words_first": True,
    "min_length": 1,
    "max_length": 32,
    "exclude_proper_names": False,
    "sound_feedback": True,
    "start_with_system": False,
    "compact_overlay": True,
    "reset_on_new_session": True,
    "show_ocr_confidence": True,
}

PROFILE_PRESETS = {
    "Roblox": {
        "language": "english",
        "search_mode": "auto",
        "auto_enter": True,
        "compact_overlay": True,
        "common_words_first": True,
    },
    "English": {
        "language": "english",
        "search_mode": "auto",
        "auto_enter": False,
        "compact_overlay": True,
    },
    "Español": {
        "language": "spanish",
        "search_mode": "auto",
        "auto_enter": False,
        "compact_overlay": True,
    },
    "Ambos": {
        "language": "both",
        "search_mode": "auto",
        "auto_enter": False,
        "compact_overlay": True,
    },
}

FILE = os.path.join(APP_FOLDER, "settings.json")


def _write_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix="settings_", suffix=".json", dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2, ensure_ascii=False)
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def load_settings():
    data = {}
    if os.path.exists(FILE):
        try:
            with open(FILE, "r", encoding="utf-8") as file:
                loaded = json.load(file)
                if isinstance(loaded, dict):
                    data = loaded
        except (OSError, json.JSONDecodeError):
            data = {}

    merged = DEFAULT_SETTINGS.copy()
    merged.update(data)
    return merged


def save_settings(settings):
    merged = DEFAULT_SETTINGS.copy()
    merged.update(settings)
    _write_json(FILE, merged)


def apply_profile(settings, profile):
    updated = settings.copy()
    updated["profile"] = profile
    updated.update(PROFILE_PRESETS.get(profile, {}))
    return updated
