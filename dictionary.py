import os
import sys

from used_words import load_used


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(os.path.dirname(__file__))

    return os.path.join(base_path, relative_path)


def load_words(path):
    with open(path, "r", encoding="utf-8") as file:
        return list(dict.fromkeys(
            word.strip()
            for word in file
            if word.strip()
        ))


def remove_used(words):
    used = load_used()
    return [
        word
        for word in words
        if word.lower() not in used
    ]


english = load_words(resource_path("data/english_words.txt"))
spanish = load_words(resource_path("data/spanish_words.txt"))


def starts_with(prefix, words):
    prefix = prefix.lower()
    results = [
        word
        for word in words
        if word.lower().startswith(prefix)
    ]
    return sorted(remove_used(results), key=lambda word: (len(word), word.lower()))


def ends_with(suffix, words):
    suffix = suffix.lower()
    results = [
        word
        for word in words
        if word.lower().endswith(suffix)
    ]
    return sorted(remove_used(results), key=lambda word: (len(word), word.lower()))


def generate_suggestions(prefix, words, limit=20):
    prefix = prefix.lower()
    matches = remove_used([
        word
        for word in words
        if word.lower().startswith(prefix)
    ])

    short_words = [word for word in matches if len(word) <= 4]
    medium_words = [word for word in matches if 5 <= len(word) <= 10]
    long_words = [word for word in matches if len(word) > 10]

    groups = [
        sorted(short_words, key=lambda word: (len(word), word.lower())),
        sorted(medium_words, key=lambda word: (len(word), word.lower())),
        sorted(long_words, key=lambda word: (len(word), word.lower())),
    ]

    result = []
    seen = set()

    # Give each word length group a chance to appear before filling the rest.
    for group in groups:
        for word in group[:5]:
            key = word.lower()
            if key not in seen:
                result.append(word)
                seen.add(key)

    if len(result) < limit:
        remaining = sorted(
            (word for word in matches if word.lower() not in seen),
            key=lambda word: (len(word), word.lower()),
        )
        result.extend(remaining[: limit - len(result)])

    return result[:limit]
