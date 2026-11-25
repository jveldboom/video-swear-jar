# Rebuild plan

Replace the Docker container with a small native Python tool. Ease of use is the top requirement. It's for other users too, so it supports macOS, Windows and Linux.

## Why

- Docker on a Mac can't use the Apple GPU, so transcription runs on CPU only.
- `ffmpeg -c copy` can't cut cleanly between keyframes. Removing 1s from the example clip gave 4.80s of video against 5.00s of audio.
- One swear word removes the whole transcript segment.
- The default model, `tiny.en`, is the least accurate English option offered.
- One image carries Python, Node, ffmpeg and unpinned Whisper packages for two architectures.

## Install

Proposed commands (the package doesn't exist yet). Each platform installs `uv` and ffmpeg, then:

```sh
uv tool install git+https://github.com/jveldboom/video-swear-jar
uv tool upgrade swearjar
```

| Platform | Prerequisites |
|---|---|
| macOS | `brew install uv ffmpeg-full` |
| Windows | `uv` and ffmpeg, likely through `winget` (builds to be verified) |
| Linux | `uv` and ffmpeg from the distro or a static build (to be verified) |

- `uv` instead of a Homebrew formula: it works on all three platforms, and a formula would have to list every Python dependency.
- The `zscale` filter (needed for HDR) isn't in every ffmpeg build. `swearjar` checks for it at startup and says what to install. On macOS it must also find `ffmpeg-full`, which isn't added to `PATH`.
- A short per-platform install script can reduce setup to one step.
- The model downloads on first run. Long steps show progress.

## Commands

| Command | What it does |
|---|---|
| `swearjar movie.mkv` | Short for `swearjar clean`: transcribe, find swear words, cut |
| `swearjar movie.mkv --cuts cuts.txt` | Cut exactly the timestamps in the file (replaces `cut-video`) |
| `swearjar read-subtitles movie.srt` | List subtitle lines with swear words; also accepts a video with embedded subtitles |
| `swearjar extract-subtitles movie.mkv` | Save embedded subtitles as `.srt`; English by default, `--language`, `--list` |
| `swearjar create-subtitles movie.mkv` | Transcribe the audio and write an `.srt` |

## Decisions

- **`--cuts` replaces word detection.** Only the file's timestamps are used. The audio is still transcribed to make subtitles; `--no-subtitles` skips that. No separate `cut` command.
- **Terminal only** for now.
- **Cut by default.** `--mute` is the fast option that leaves the video untouched.
- **Word detection uses the audio only.** Subtitle files are often inaccurate, so they never decide what gets cut. `read-subtitles` only reports.
- **Word-level timestamps**, with a little padding.
- **Matching subtitles for the cleaned video**, built from the transcript, timed to the cut video and with swear words removed.
- **Subtitles are embedded by default** when the container supports it (MKV, MP4). `--external-subtitles` also saves a `movie.clean.srt`. If embedding isn't possible, the file is saved externally and the user is told.
- **Original subtitle tracks are removed** from the cleaned video.
- **Embedded subtitles are usually text**, so no OCR. Image subtitles get a clear "not supported" message.
- **Transcripts are cached**, so `create-subtitles` followed by `clean` transcribes once.
- **Keep the existing word list.**

## Cut engine

Port [`remove-cuts.sh`](https://github.com/jveldboom/utils/blob/main/ffmpeg/remove-cuts.sh) to Python: re-encode each kept segment, match the source codec and color, tone-map HDR to SDR, then concatenate. Detected words and `--cuts` files share it.

The script only uses VideoToolbox, which is macOS-only. The port picks an encoder that works on the machine: VideoToolbox on macOS; NVENC, Quick Sync or AMF where available; otherwise `libx264`/`libx265` on the CPU. Quality settings need tuning per encoder.

Problems reproduced on test clips, each to be fixed and covered by a test:

| Problem | Result | Fix |
|---|---|---|
| Kept stretch under 1s | Run aborts: `Invalid duration for option t: .500000` | Format durations with a leading zero |
| One cut inside another | Part of the outer cut stays in | Merge overlapping ranges |
| Audio tagged only `fre`, or untagged MKV | Output has no audio, exit code 0 | Fall back to all audio tracks |
| Indented line, or `to` instead of `-` | Silently skipped | Fail with the line number |
| No arguments | `$1: unbound variable` | Show usage |
| AAC encoded per segment | 100 cuts: 73.4s of decoded audio where 70s expected | Keep segment audio as PCM, encode AAC once |

The PCM fix gave 70.06s of audio, but a decode check still showed video timestamp warnings that need investigating.

Not yet checked: HDR input, 10-bit SDR, chapter markers, real movie files, playback.

## Transcription

Python only, managed with `uv`; Node is removed. One engine on every platform is easier to maintain.

**Leading candidate: `whisper.cpp`.** It can use the GPU on Apple (Metal) and on AMD, Intel and NVIDIA (Vulkan). The Windows test machine has an AMD RX 7600.

| Alternative | Limitation |
|---|---|
| `faster-whisper` | CPU only on Mac; AMD GPU support on Windows looks experimental ([CTranslate2 #2016](https://github.com/OpenNMT/CTranslate2/issues/2016)) |
| `mlx-whisper`, `parakeet-mlx` | Apple Silicon only |

**Risk:** upstream `whisper.cpp` doesn't publish Vulkan builds for Windows ([issue #3673](https://github.com/ggml-org/whisper.cpp/issues/3673)). Community builds exist, but we'd be trusting third-party binaries. Preferred: build our own in CI from a pinned upstream version. How `uv` installs that build is part of phase 1.

## Phases

1. **Benchmark.**
   - Prove `whisper.cpp` builds and uses the GPU on the Mac and the Windows RX 7600.
   - Hand-label swear words in a few real movie clips. Compare missed words, timing error, run time and transcript quality.
   - Check that the AMD encoders (`h264_amf`, `hevc_amf`) cut accurately.
2. **Core CLI.** `clean` (including embedded subtitles, `--mute` and `--cuts`) and `read-subtitles`, on all three platforms. Port the existing tests and add a many-cuts sync test. CI runs on macOS, Windows and Linux.
3. **Subtitle tools.** `extract-subtitles` and `create-subtitles`, plus embedded-subtitle input for `read-subtitles`.
4. **Install and release.** Install instructions or scripts per platform, startup checks, retire the Docker image with a note for `v1` users.
5. **Extras.** Center-channel handling for surround audio, custom word lists, batch folders, a review screen to play each hit and untick false positives.

## Testing machines

- Mac with Apple Silicon (M3 Pro).
- Windows PC with an AMD RX 7600.
- Linux and NVIDIA have no test hardware: CI can only check CPU behaviour there.

## Development

- `v1` holds the Docker version for urgent fixes.
- v2 is built on the `v2` branch. `main` stays untouched until v2 is ready, because every push to `main` publishes a Docker image.
- Before merging `v2`, replace the Docker release workflow and add a README note pointing v1 users to the old image.
- Work is tracked in GitHub milestones, one per phase.
