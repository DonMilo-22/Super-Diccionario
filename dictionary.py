import os
import sys

from stats import favorites, usage_counts
from used_words import load_used


COMMON_WORDS = {
    "the": 1000, "love": 990, "lover": 950, "lovely": 940, "like": 930, "life": 920,
    "good": 910, "great": 900, "happy": 890, "hello": 880, "world": 870, "game": 860,
    "play": 850, "player": 840, "quick": 830, "quickly": 820, "slow": 810, "slowly": 800,
    "house": 790, "water": 780, "light": 770, "night": 760, "fire": 750, "friend": 740,
    "amor": 990, "casa": 950, "juego": 940, "hola": 930, "mundo": 920, "feliz": 910,
    "bueno": 900, "grande": 890, "agua": 880, "fuego": 870, "amigo": 860,
}


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)


def load_words(path):
    with open(path, "r", encoding="utf-8") as file:
        return list(dict.fromkeys(word.strip() for word in file if word.strip()))


def _family_key(word):
    key = word.lower()
    for suffix in ("ingly", "edly", "ing", "ed", "es", "s", "ly"):
        if len(key) > len(suffix) + 3 and key.endswith(suffix):
            return key[:-len(suffix)]
    return key


def remove_used(words, smart=False):
    used = load_used()
    if not smart:
        return [word for word in words if word.lower() not in used]

    used_families = {_family_key(word) for word in used}
    return [
        word for word in words
        if word.lower() not in used and _family_key(word) not in used_families
    ]


english = load_words(resource_path("data/english_words.txt"))
spanish = load_words(resource_path("data/spanish_words.txt"))


def _rank(word, common_first=True):
    key = word.lower()
    favs = favorites()
    counts = usage_counts()
    favorite_boost = 1 if key in favs else 0
    usage_boost = int(counts.get(key, 0))
    common_boost = COMMON_WORDS.get(key, 0) if common_first else 0
    return (-favorite_boost, -usage_boost, -common_boost, len(word), key)


def _difficulty_rank(word, difficulty):
    key = word.lower()
    common = COMMON_WORDS.get(key, 0)
    usage = int(usage_counts().get(key, 0))

    if difficulty == "easy":
        return (-common, -usage, len(word), key)

    if difficulty == "hard":
        return (common > 0, common, usage, -len(word), key)

    return _rank(word, True)


def filter_words(words, min_length=1, max_length=32, exclude_proper=False):
    result = []
    for word in words:
        if not (min_length <= len(word) <= max_length):
            continue
        if exclude_proper and word[:1].isupper() and not word.isupper():
            continue
        result.append(word)
    return result


def starts_with(prefix, words, limit=20, **options):
    prefix = prefix.lower()
    matches = [word for word in words if word.lower().startswith(prefix)]
    matches = remove_used(
        filter_words(matches, options.get("min_length", 1), options.get("max_length", 32), options.get("exclude_proper", False)),
        smart=options.get("smart_antirepeat", False),
    )
    return sorted(matches, key=lambda word: _rank(word, options.get("common_first", True)))[:limit]


def ends_with(suffix, words, limit=20, **options):
    suffix = suffix.lower()
    matches = [word for word in words if word.lower().endswith(suffix)]
    matches = remove_used(
        filter_words(matches, options.get("min_length", 1), options.get("max_length", 32), options.get("exclude_proper", False)),
        smart=options.get("smart_antirepeat", False),
    )
    return sorted(matches, key=lambda word: _rank(word, options.get("common_first", True)))[:limit]


def generate_suggestions(prefix, words, limit=20, **options):
    return starts_with(prefix, words, limit=limit, **options)


def auto_suggestions(fragment, words, limit=20, **options):
    start = starts_with(fragment, words, limit=limit, **options)
    end = ends_with(fragment, words, limit=limit, **options)

    combined = []
    seen = set()
    for word in start + end:
        key = word.lower()
        if key not in seen:
            combined.append(word)
            seen.add(key)

    return sorted(combined, key=lambda word: _rank(word, options.get("common_first", True)))[:limit]


def chain_candidates(prefix, words, difficulty="normal", limit=80, **options):
    prefix = prefix.lower()
    matches = [word for word in words if word.lower().startswith(prefix)]
    matches = filter_words(
        matches,
        options.get("min_length", 1),
        options.get("max_length", 32),
        options.get("exclude_proper", False),
    )
    matches = remove_used(
        matches,
        smart=options.get("smart_antirepeat", False),
    )

    unique = []
    seen = set()
    for word in matches:
        key = word.lower()
        if key not in seen:
            unique.append(word)
            seen.add(key)

    return sorted(
        unique,
        key=lambda word: _difficulty_rank(word, difficulty),
    )[:limit]
