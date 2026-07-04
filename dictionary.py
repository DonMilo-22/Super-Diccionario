import os
import sys

from used_words import load_used

def resource_path(relative_path):

    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(
        base_path,
        relative_path
    )

def remove_used(words):

    used = load_used()

    return [
        w for w in words
        if w.lower() not in used
    ]
def load_words(path):
    with open(path, "r", encoding="utf-8") as f:
        return [w.strip() for w in f.readlines()]

english = load_words(resource_path("data/english_words.txt"))
spanish = load_words(resource_path("data/spanish_words.txt"))

def starts_with(prefix, words):
    prefix = prefix.lower()

    results = [
        w for w in words
        if w.lower().startswith(prefix)
    ]

    return sorted(results, key=len)

def ends_with(suffix, words):
    suffix = suffix.lower()

    results = [
        w for w in words
        if w.lower().endswith(suffix)
    ]

    return sorted(results, key=len)

def generate_suggestions(prefix, words):

    prefix = prefix.lower()

    matches = [
        w for w in words
        if w.lower().startswith(prefix)
    ]

    matches = remove_used(matches)

    short_words = [
        w for w in matches
        if len(w) <= 4
    ]

    medium_words = [
        w for w in matches
        if len(w) >= 5
    ]

    long_words = [
        w for w in matches
        if len(w) > 10
    ]

    same_end = [
        w for w in matches
        if w.lower().endswith(prefix)
    ]

    result = []

    result.extend(sorted(short_words, key=len)[:5])

    result.extend(
        sorted(medium_words, key=len)[:5]
    )

    result.extend(
        sorted(long_words, key=len)[:5]
    )

    result.extend(
        sorted(same_end, key=len)[:5]
    )

    unique = []

    seen = set()

    for word in result:

        if word not in seen:
            unique.append(word)
            seen.add(word)

    if len(unique) < 20:

        remaining = [
            w for w in matches
            if w not in seen
        ]

        unique.extend(
            remaining[:20 - len(unique)]
        )

    return unique[:20]