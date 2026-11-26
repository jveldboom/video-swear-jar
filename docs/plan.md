# Rebuild plan

Replace the Docker container with a small Python tool that drafts a cut list from subtitles, which you edit and then apply.

The problem it solves: finding good subtitles and picking out every swear word by hand. The list is still reviewed by a person, to add other content and to cut at full sentences.

## Commands

| Command | What it does | State |
|---|---|---|
| `swearjar find movie.mkv` | Write `movie-cuts.txt` from the video's subtitles | Embedded, `.srt` next to the video and `--srt` work; online search to do |
| `swearjar cut movie.mkv` | Apply the cut list | To do |

## Finding subtitles

1. `--srt` if given.
2. An embedded text subtitle track in the requested language (English by default).
3. An `.srt` next to the video.
4. OpenSubtitles (to do): match on a fingerprint of the file first, then title and episode. Needs a free account; the API key is read from the environment.

Image subtitles are not supported.

## Cut list

One entry per line, edited by hand:

```
00:00:10 - 00:00:12        text from the subtitle
00:01:00 - 00:01:03 [mute] text from the subtitle
```

- Times are `HH:MM:SS`, with or without milliseconds.
- `[mute]` directly after the times silences the range and keeps the picture. Without it the range is removed.
- Anything after that is a note and is ignored.
- `find` never replaces an existing list without `--force`.

## Cutting

Port [`remove-cuts.sh`](https://github.com/jveldboom/utils/blob/main/ffmpeg/remove-cuts.sh), which has worked well in real use.

- **Mute-only lists** copy the video and re-encode only the audio.
- **Video** is re-encoded whole with a hardware encoder (VideoToolbox `-q:v 65`).
- **HDR is kept** by default; `--sdr` converts to SDR (needs ffmpeg with `zscale`).
- **Audio** is encoded once, to AAC at 128 kbps per channel up to 640 kbps, with all channels. Decode AC-3 and E-AC-3 with `-drc_scale 0`, so ffmpeg doesn't compress the volume.
- **Speed:** time each step first, then try parallel segments and hardware decoding.
- Smart cut was prototyped and dropped. See [`spikes/smart-cut/`](../spikes/smart-cut/README.md).

Known problems in the script, each to be fixed with a test:

| Problem | Result | Fix |
|---|---|---|
| Kept stretch under 1s | Run aborts | Format durations with a leading zero |
| One cut inside another | Part of the outer cut stays in | Merge overlapping ranges |
| Audio tagged only another language, or untagged | Output has no audio | Fall back to all audio tracks |
| Indented line, or `to` instead of `-` | Silently skipped | Fail with the line number |
| No arguments | `$1: unbound variable` | Show usage |
| AAC encoded per segment | Audio drifts longer with each cut | Keep segment audio as PCM, encode once |

## Setup

Plain Python (3.10+) with no packages, plus ffmpeg. macOS comes first. Word list: `swearjar/swear-words.json`.

## Not doing: transcription

Finding words by transcribing the audio was tested with whisper.cpp `large-v3-turbo`. It found nearly all hand-made cuts but was slow, and timing precision was never verified. Subtitles are faster and missed none of the spoken ones.

## Development

- `v1` holds the Docker version for urgent fixes.
- v2 is built on the `v2` branch. `main` stays untouched until v2 is ready, because every push to `main` publishes a Docker image.
- Before merging `v2`, remove the Node code and Docker release workflow, and tell `v1` users in the README where the old image is.
