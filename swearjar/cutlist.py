"""Turn subtitle cues with swear words into cut list lines."""

import json
import math
import re
from pathlib import Path

WORDS_FILE = Path(__file__).with_name("swear-words.json")


def swear_pattern(words_file=WORDS_FILE):
    words = json.loads(Path(words_file).read_text())
    return re.compile(rf"\b(?:{'|'.join(words)})\b", re.IGNORECASE)


def has_swear_word(text, pattern):
    # Bracketed text describes sounds or names speakers; nobody says it.
    return bool(pattern.search(re.sub(r"\[[^\]]*\]", " ", text)))


def entries(cues, pattern):
    """Return (start, end, text) in whole seconds, merging entries that overlap."""
    result = []
    for cue in sorted(cues):
        if not has_swear_word(cue.text, pattern):
            continue
        start, end = math.floor(cue.start), math.ceil(cue.end)
        if result and start <= result[-1][1]:
            previous = result[-1]
            result[-1] = (previous[0], max(previous[1], end), f"{previous[2]} / {cue.text}")
        else:
            result.append((start, end, cue.text))
    return result


def timestamp(seconds):
    return f"{seconds // 3600:02}:{seconds % 3600 // 60:02}:{seconds % 60:02}"


def render(items):
    return "".join(f"{timestamp(start)} - {timestamp(end)}\t{text}\n" for start, end, text in items)
