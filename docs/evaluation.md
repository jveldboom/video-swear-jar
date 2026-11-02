# Project Evaluation & Plan — video-swear-jar

Branch evaluated: `jveldboom/mute-audio` (including uncommitted working-tree changes), 2026-11-02.
Method: four parallel read-only review agents (one per question) run in herdr, then consolidated. Findings are from code reading plus `npm test` (1 failed, 23 passed); ffmpeg/Whisper behavior claims were **not** executed — verify before acting.

> Created using Anthropic Claude. AI-generated draft — keep on internal versions until a human has reviewed and verified the content.

## TL;DR

| Question | Answer |
|---|---|
| 1. Critical issues? | Yes — 5 high-severity bugs, most in the new mute path (un-awaited `mute`, broken `--output-dir`, no `-y`, dropped streams, broken `cut-video` + failing test). |
| 2. UX improvements? | Yes — `--dry-run`, word list flags, correct output summary/exit codes, README/Makefile sync. |
| 3. Best/fastest/easiest approach? | Easiest: yes. Fastest: transcription dominates and `whisper-ctranslate2` int8 is right. Best: not yet — segment-level muting is too coarse; use word-level timestamps + padding. |
| 4. Adopt `remove-cuts.sh`? | **Partially.** Port the segment math (sort/merge/clamp, no floor/ceil). Don't port the macOS-only VideoToolbox encoders or forced HDR→SDR tone-map. Offer accurate cut only as opt-in `--mode cut`. Mute stays the default. |

## 1. Critical issues

### High
1. **`video.mute` not awaited** — `src/clean.js:66`. try/catch can't catch ffmpeg failures; "successfully cleaned" prints before ffmpeg finishes. Also `run()` returns errors instead of setting `process.exitCode = 1`, so failures exit 0. Fix: `await`, add `.catch`, set exit code.
2. **`createCutFile` regression** — `src/video.js:72,81` changed `paths.cutVideo` → `paths.inputFile`; `cut-video.js:67-70` doesn't pass `inputFile`, so the concat list gets `file 'undefined'`. This is the 1 failing test (`video.test.js:73-90`).
3. **`--output-dir` effectively broken** — whisper writes JSON to `outputDir` (`video.js:12`) but `clean.js:58` reads `paths.transcript` from cwd; output video also ignores it (`utils.js:9,13`). `-i /data/x.mp4` also writes relative to cwd.
4. **No `-y` / `-nostdin` on ffmpeg** — `video.js:108-114`. Re-run with existing output prompts on stdin and hangs.
5. **Streams silently dropped** — no `-map`, so extra audio tracks, subtitles, chapters are lost (matters for the README's main MKV use case); audio re-encoded at default AAC bitrate.

### Medium
6. Whole-segment muting (see §3).
7. `NaN` → `null` regex (`video.js:46`) can corrupt text; null `start/end` would throw on `.toFixed`.
8. Swear regex built from unescaped JSON entries and recompiled per segment (`video.js:58-59`); add a test for the list.
9. Word list over-aggressive (`god`, `jesus`, `hell`, `heck`, `stupid`…). Uncommitted `monkey` addition (`swear-words.json:42`) looks like test scaffolding for the example video — don't ship.
10. Concat-file path quoting (`'` unescaped) and cut list must sit beside the video.
11. Dead code/stale messaging: output summary lists `cutWords` file that is never written; commented-out blocks; "[3 of 4]"; typo "Mutting"; transcript existence unchecked (TODO at `clean.js:56`).
12. Tests: no `mute()` test; async tests not awaited; CI test run unverified.

### Low / infra
13. Dockerfile: `python:3.9-slim` and Node 18 are EOL; NodeSource `setup_18.x` deprecated; unpinned `pip install -U`; `curl | bash`; `npm install` → `npm ci`; runs as root.
14. Makefile: `node` target path wrong with new mount; `MAJOR_VERSION` undefined in `docker-buildx`; no `.PHONY`; host `node_modules` overlay risk.
15. `asyncSpawn` logs every stdout/stderr chunk; `yargs` `input` lacks `type: 'string'`.
16. Untracked `examples/s03e11.mp4` — keep out of git (`.gitignore`/LFS). `CONTRIBUTING.md` untracked — commit if intended.

Verified OK: no shell injection (`spawn` without `shell:true`); spaces in filenames fine.

## 2. User-experience improvements

Priority order:
1. Correct completion/exit behavior and accurate output summary (write a detected-words report: time range + text).
2. `--dry-run`: transcribe + detect, print `HH:MM:SS  word/segment`, no ffmpeg.
3. Reuse an existing transcript (`--skip-transcribe`) — transcription is the slow step.
4. `--words <file>`, `--extra-words`, `--exclude-words`; optional `--strictness mild|strong`.
5. `--mode mute|cut` (default `mute`) instead of commented-out code; `--padding`.
6. Friendlier errors: validate input exists, map `exit code null` to "likely OOM — raise Docker memory ≥4 GB", show stack only with `--debug`.
7. CLI polish: `yargs.usage('clean-fast')` → real usage, `.strict()`, `.help()`, examples, `--output` for explicit filename; better default naming (`<name>-clean<ext>`).
8. Docs: README still says "cut"; missing `-o`/`--debug`; `medium.sm` typo; `:v1` vs `latest`; recommend `small.en` over `tiny.en` for recall.

## 3. Is this the best/fastest/easiest approach?

Overall design (transcribe → match → ffmpeg `volume` mute, video stream-copied) is the right, simple one and far better than the prior concat-cut. Gaps:

- **Segment → word granularity (largest win).** Use `--word_timestamps True` (supported by both engines; ~10–30% slower), match per word, fall back to segment span when word times are null. Handle multi-word entries via sliding window.
- **Padding + interval merging:** ~0.15 s before / ~0.25 s after; merge overlaps.
- **Filter scalability:** replace N chained `volume` filters with a single expression and/or `-filter_script:a` file; add short ramps to avoid clicks.
- **Stream handling:** `-map 0`, copy non-target tracks and subs; match source audio bitrate/channels.
- **Model:** keep `whisper-ctranslate2` int8; default to `base.en`/`small.en` (missed word = leak); consider `--vad_filter`, `--condition_on_previous_text False`; `distil-large-v3` if supported.
- **Later/optional:** bleep tone, whisperX/stable-ts alignment, subtitle-based pre-pass (repo already has `read-subtitles.js`).
- No maintained off-the-shelf library does exactly this; Whisper + ffmpeg is the common pattern.

## 4. Adopt `remove-cuts.sh` logic?

**Recommendation: partially.**

Take:
- Keep-segment math: sort, merge overlaps, clamp to `[0, duration]`, derive gaps (more robust than current inpoint/outpoint chain; current code can emit empty `inpoint 0/outpoint 0`).
- Exact float boundaries (drop `Math.floor/ceil`, which widens cuts up to ~2 s) — helps even in copy mode.
- Per-segment encode then stream-copy concat; ffprobe duration; `-of json` probing (avoids the CSV trailing-comma HDR gotcha).

Don't take:
- `h264/hevc_videotoolbox` (macOS-only; fails in the Linux Docker image) — use `libx264`/`libx265`, optionally detect nvenc/vaapi.
- Forced HDR→SDR tone-map as default (make `--tonemap-sdr` explicit; verify `zscale`/libzimg in the image).
- English-only audio filtering and `.mp4` segment container (drops subs/tracks) — use `.mkv` + `-map 0`.

Trade-off: accurate cut = full software re-encode (slow for feature films, generational loss, HDR10+/DV lost). Keep mute (lossless video, instant) as default; offer accurate cut as opt-in. A "smart cut" (re-encode only GOPs around boundaries) is a possible later enhancement.

## Recommended plan

**Phase 1 — Distribution (npm/npx)** — see "Distribution" section below. Everything else builds on this; ship the package skeleton first (`bin`/`files`/`engines`, `doctor`, preflight, models cache, npm publish workflow).

**Phase 2 — Correctness (small PR)**
- `await video.mute`, `.catch`, `process.exitCode = 1`
- Fix `createCutFile` regression / update test + caller
- Join `outputDir` into all paths; verify transcript exists
- `-y -nostdin -hide_banner -loglevel error`; `-map 0` stream handling
- Remove dead code/typos, fix summary; drop `monkey`; gitignore example video
- Add `mute()` tests and await existing async tests

**Phase 3 — Quality**
- Word-level timestamps, padding, interval merge, single-expression/`-filter_script` filter
- Default model `base.en`/`small.en`

**Phase 4 — UX**
- `--dry-run`, words report, `--skip-transcribe`, `--words`/`--exclude-words`, `--mode`, yargs cleanup, README/Makefile sync

**Phase 5 — Docker image (low priority, optional)**
- Kept as an alternative for users who don't want to install ffmpeg/Whisper on the host (and for Linux servers/NAS). Rebuild the image to install the published npm package (`npm i -g @jveldboom/video-swear-jar`) plus ffmpeg and a Whisper engine, instead of copying `src` in. Move to Node 22 LTS and Python ≥3.11, pin dependencies, run as non-root. Fix the Makefile Docker targets (`MAJOR_VERSION`, `node` path, `.PHONY`). Document that Docker on macOS is CPU-only and slower than the native install.

**Phase 6 — Optional cut mode**
- Port segment math + libx264/libx265 accurate cut behind `--mode cut`; opt-in tone-map

## Distribution: npm / npx instead of Docker (decided direction)

Why: Docker on macOS cannot use the Apple Silicon GPU (Whisper runs CPU-only), the image is multi-GB (Python + PyTorch), and volume mounts/OOM add friction. Keep the Node CLI (no rewrite); publish to npm; keep Docker as a secondary option for Linux servers/NAS.

Decisions:
- **Package:** `@jveldboom/video-swear-jar` (the unscoped name was unpublished 2024-05-11 and can't reuse versions). The scoped name already exists on npm — verify its contents/ownership before the first publish.
- **`package.json`:** add `bin` (`video-swear-jar`, `vsj`), `files`, `engines` (node >=20), `repository`; remove stale `"main": "run.js"`. Subcommands `clean`, `cut`, `subtitles`, `doctor` replace the three Docker symlinks.
- **Dependency policy: the tool never installs software.** ffmpeg/ffprobe are installed by the user (not bundled — avoids GPL static-build licensing, package size, and compatibility concerns). The Whisper engine (`whisper-cpp` or `whisper-ctranslate2`) is also user-installed. Missing dependency: print the OS-specific command (`brew`/`apt`/`winget`) and exit non-zero. Never run brew/apt/sudo automatically.
- **Exception — models are data:** auto-download on first use into `~/.cache/video-swear-jar` (honor `XDG_CACHE_HOME`) with size warning and confirmation; `--yes` for non-interactive runs. Remove hardcoded `/app/.whisper`.
- **Preflight (before any work):** ffmpeg/ffprobe exist and meet a minimum version; required encoders/filters present (`aac`, `volume`; `zscale` only for the optional tone-map mode); engine found; model present. Optional `--ffmpeg <path>` / `FFMPEG_PATH` override.
- **`doctor` command:** runs the same checks on demand, prints a readable report (versions, paths, chosen engine, optional-feature status), exits non-zero if a required item is missing. No TTY: never prompt.
- **Engine abstraction:** add `whisper-cpp` behind `--engine`; verify its word-level timestamp accuracy versus whisper-ctranslate2 before making it the default.
- **Publishing:** switch `.github/workflows/release.yaml` to npm publish with provenance (verify what the workflow currently does). Optional later: Homebrew tap (depends on `ffmpeg` and `whisper-cpp`), winget/scoop, Node SEA/Bun single-file build.
- **Sequencing:** this is Phase 1 — later phases ship through this package. Because the correctness bugs (Phase 2) are still present, publish the first versions as a prerelease (`0.x` / `next` dist-tag) and promote to `latest` once Phase 2 lands. Combine the engine abstraction with the word-level timestamp work (Phase 3; same transcript-parsing code).

## Open questions for the owner
- Is cut mode still wanted, or should `cut-video`/`createCutFile` be removed?
- Is `monkey` intentional for the example, or test scaffolding?
- Target audience (family-safety = prioritize recall → larger model, padding)?

Please review for accuracy and completeness before use, and share only with people authorized to see the source material.
