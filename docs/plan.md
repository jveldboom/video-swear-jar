# Rebuild plan

Replace the Docker container with a small native Python tool. Ease of use is the top requirement. It's for other users too, so it supports macOS, Windows and Linux.

## Why

- Docker on a Mac can't use the Apple GPU, so transcription runs on CPU only.
- `ffmpeg -c copy` can't cut cleanly between keyframes. Removing 1s from the example clip gave 4.80s of video against 5.00s of audio.
- One swear word removes the whole transcript segment.
- The default model, `tiny.en`, is the least accurate English option offered.
- One image carries Python, Node, ffmpeg and unpinned Whisper packages for two architectures.

## Input goal

Work with nearly any video file: different codecs, containers, resolutions, frame rates, bit depths, SDR and HDR, audio layouts, and imperfect timestamps.

- No single sample file defines the design. A real file is one test case.
- Don't assume a constant frame rate, a start time of zero, or that every packet decodes.
- Each bug found in a real file gets a small synthetic test for the general case.
- A file that can't be handled correctly fails with a clear message, never a silently broken output.
- Tests use short clips so they run in minutes.

## Quality goal

No noticeable video or audio quality loss. A small, invisible loss from re-encoding is acceptable. Changing resolution may become an option later, but not now.

- **Video: re-encode the whole video** with a hardware encoder where available, starting from the quality setting in `remove-cuts.sh` (VideoToolbox `-q:v 65`). `--mute` leaves the video untouched.
- **HDR is kept** by default. `--sdr` converts to SDR. HDR is not yet tested on a real file.
- **Audio:** re-encode once to AAC at 128 kbps per channel, capped at 640 kbps (5.1 gets 640), keeping all channels. This is one extra lossy generation, accepted so cuts stay exact. FLAC was rejected: on a full-length file it grew the audio from 202 MB to 1,106 MB. Dolby Atmos or DTS:X positional data would likely be lost.
- **No volume compression:** ffmpeg applies dynamic range compression by default when decoding AC-3 and E-AC-3. Decode with `-drc_scale 0`.

### Why not smart cut

Smart cut (copy the original video, re-encode only around cuts) was prototyped and dropped. See [`spikes/smart-cut/`](../spikes/smart-cut/README.md).

- It produced frame-accurate output for some H.264 and HEVC files, but needed format-specific fixes for each problem found.
- VLC's hardware decoder failed at joins where the re-encoded sections' decoder settings differed from the source's, while ffmpeg decoded the same files correctly.
- H.264 open-GOP sources were mostly re-encoded anyway, and other codecs were not handled.

### Measured cost of re-encoding

Hardware `-q:v 65` on two 60-second samples, on an M3 Pro:

| Sample | VMAF average / worst 1% | Video size vs. source | Full-length time (estimate) |
|---|---|---|---|
| 1080p, 60 fps, 10-bit | 96.0 / 93.8 | 4.2x | 11 min |
| 4K, 24 fps, 8-bit | 94.1 / 88.1 | 0.84x | 25 min |

No visible difference was found by eye. **Open:** low-bitrate sources grow a lot. Test a bitrate target based on the source.

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
- The `zscale` filter (needed for `--sdr`) isn't in every ffmpeg build. `swearjar` checks for it when `--sdr` is used and says what to install. On macOS it must also find `ffmpeg-full`, which isn't added to `PATH`.
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
- **Cut file format:** one removal per line as `HH:MM:SS - HH:MM:SS`, with or without milliseconds (`HH:MM:SS.mmm`) on either timestamp.
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

**Known-good baseline:** `remove-cuts.sh` has worked well in real use, with no complaints about video glitches or audio pops.

Port [`remove-cuts.sh`](https://github.com/jveldboom/utils/blob/main/ffmpeg/remove-cuts.sh) to Python: keep its segment math, source detection and concatenation. Unlike the script, tone-map HDR to SDR only with `--sdr`. Detected words and `--cuts` files share it.

The script only uses VideoToolbox, which is macOS-only. The port picks an encoder that works on the machine: VideoToolbox on macOS; NVENC, Quick Sync or AMF where available; otherwise `libx264`/`libx265` on the CPU. Quality settings need tuning per encoder.

Problems reproduced on test clips, each to be fixed and covered by a test:

| Problem | Result | Fix |
|---|---|---|
| Kept stretch under 1s | Run aborts: `Invalid duration for option t: .500000` | Format durations with a leading zero |
| One cut inside another | Part of the outer cut stays in | Merge overlapping ranges |
| Audio tagged only `fre`, or untagged MKV | Output has no audio, exit code 0 | Fall back to all audio tracks |
| Indented line, or `to` instead of `-` | Silently skipped | Fail with the line number |
| No arguments | `$1: unbound variable` | Show usage |
| AAC encoded per segment | 100 cuts: 73.4s of decoded audio where 70s expected | Keep segment audio as PCM, encode once |

The PCM fix gave 70.06s of audio, but a decode check still showed video timestamp warnings that need investigating.

Not yet checked: HDR input, chapter markers, full-length files.

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
