"""Locate, extract and parse subtitles."""

import json
import re
import subprocess
from pathlib import Path
from typing import NamedTuple

from .errors import SwearJarError

TEXT_CODECS = {"subrip", "srt", "ass", "ssa", "mov_text", "webvtt", "text"}
LANGUAGE_ALIASES = [{"en", "eng"}, {"es", "spa"}, {"fr", "fra", "fre"}, {"de", "deu", "ger"}]

TIMING = re.compile(
    r"^\s*(\d+):(\d\d):(\d\d)[,.](\d{1,3})\s*-->\s*(\d+):(\d\d):(\d\d)[,.](\d{1,3})"
)


class Cue(NamedTuple):
    start: float
    end: float
    text: str


def language_codes(language):
    language = language.lower()
    return next((group for group in LANGUAGE_ALIASES if language in group), {language})


def _run(args):
    try:
        return subprocess.run(args, capture_output=True, check=True).stdout
    except FileNotFoundError:
        raise SwearJarError(f"{args[0]} is not installed") from None
    except subprocess.CalledProcessError as error:
        detail = error.stderr.decode(errors="replace").strip()
        raise SwearJarError(f"{args[0]} failed: {detail}") from None


def subtitle_streams(video):
    output = _run([
        "ffprobe", "-v", "error", "-select_streams", "s",
        "-show_entries", "stream=index,codec_name:stream_tags=language,title:stream_disposition=forced",
        "-of", "json", str(video),
    ])
    return json.loads(output).get("streams", [])


def choose_stream(streams, language):
    """Return the best text subtitle stream for the language, or None."""
    codes = language_codes(language)

    def tag(stream):
        return stream.get("tags", {}).get("language", "und").lower()

    def is_partial(stream):
        title = stream.get("tags", {}).get("title", "").lower()
        forced = stream.get("disposition", {}).get("forced")
        return bool(forced) or any(word in title for word in ("forced", "commentary", "sign"))

    text = [s for s in streams if s.get("codec_name") in TEXT_CODECS and not is_partial(s)]
    matches = [s for s in text if tag(s) in codes]
    if matches:
        return matches[0]
    # A lone untagged track is most likely the right one.
    untagged = [s for s in text if tag(s) == "und"]
    return untagged[0] if len(untagged) == 1 else None


def extract(video, stream_index):
    output = _run([
        "ffmpeg", "-v", "error", "-i", str(video),
        "-map", f"0:{stream_index}", "-f", "srt", "-",
    ])
    return output.decode("utf-8", errors="replace")


def sidecar(video, language):
    """Return a subtitle file saved next to the video, or None."""
    names = [f"{video.stem}.{code}.srt" for code in sorted(language_codes(language))]
    names.append(f"{video.stem}.srt")
    return next((video.with_name(n) for n in names if video.with_name(n).is_file()), None)


def read_file(path):
    data = Path(path).read_bytes()
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace")


def parse(content):
    cues = []
    timing = None
    lines = []

    def finish():
        if timing:
            text = " ".join(lines)
            text = re.sub(r"<[^>]*>|\{\\[^}]*\}", "", text)
            text = " ".join(text.split())
            if text:
                cues.append(Cue(timing[0], timing[1], text))

    for line in content.splitlines():
        match = TIMING.match(line)
        if match:
            if lines and lines[-1].strip().isdigit():
                lines.pop()  # the next cue's number
            finish()
            g = match.groups()
            timing = tuple(
                int(g[i]) * 3600 + int(g[i + 1]) * 60 + int(g[i + 2]) + int(g[i + 3].ljust(3, "0")) / 1000
                for i in (0, 4)
            )
            lines = []
        elif line.strip():
            lines.append(line.strip())
    finish()
    return cues


def load(video, language="en", srt=None):
    """Return (cues, description of where they came from)."""
    video = Path(video)
    if srt:
        content, source = read_file(srt), str(srt)
    else:
        streams = subtitle_streams(video)
        stream = choose_stream(streams, language)
        if stream:
            content = extract(video, stream["index"])
            source = f"embedded track {stream['index']}"
        elif sidecar(video, language):
            source = str(sidecar(video, language))
            content = read_file(source)
        else:
            reason = f"no embedded text subtitles for '{language}' and no .srt next to the video"
            if streams and not any(s.get("codec_name") in TEXT_CODECS for s in streams):
                reason += " (its subtitle tracks are images, which are not supported)"
            raise SwearJarError(f"{reason}. Pass one with --srt.")

    cues = parse(content)
    if not cues:
        raise SwearJarError(f"no subtitle lines could be read from {source}")
    return cues, source
