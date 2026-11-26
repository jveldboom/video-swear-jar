# Smart cut spike (#47)

**Outcome: smart cut was dropped** in favor of re-encoding the whole video. See `docs/plan.md`.

Throwaway prototype, not the v2 cut engine. Needs `ffmpeg` (tested with 7.0.1 on an M3 Pro) and Python 3.

Run from an empty directory, with `$SPIKE` set to this folder:

```sh
mkdir clips && bash $SPIKE/mk.sh   # synthetic test clips
python3 $SPIKE/check.py clips/*.mkv
python3 $SPIKE/many.py             # 100 cuts, MKV and MP4
python3 $SPIKE/measure.py a.mkv    # re-encode quality, size and time
```

## Method

- Cut times snap outward to whole frames, using the file's real frame timestamps.
- For each kept range, copy whole GOPs and re-encode the partial GOPs at both edges (x264/x265, CRF 14).
- Select copied packets by timestamp. `-ss` with `-c copy` started one GOP early.
- Drop open-GOP leading frames at the start of a copy, and re-encode those at the end of it.
- Repeat parameter sets in-band, and rewrite decode timestamps at the final mux.
- Cut audio separately by sample, then encode once to AAC (128 kbps per channel, up to 640).
- Relabel the first keyframe of each copied HEVC piece from CRA to BLA. Without this, joins lost frames and had decode errors.
- Ignore frames before the first keyframe, which can't be decoded.

## Results (synthetic clips, 640x360, 23.976 fps)

| Source | Frame accurate | Frames copied |
|---|---|---|
| H.264 closed GOP, 8-bit and 10-bit | Yes | 1054 of 1262 |
| HEVC closed and open GOP | Yes | 1045-1054 of 1262 |
| HEVC HDR10, open GOP | Yes | 1041 of 1262 |
| H.264 open GOP | Yes | **46 of 1262** |
| HEVC 10-bit, 5.1 audio, 100 cuts, MKV and MP4 | Yes | 5104 of 8531 |

- Copied frames are bit-identical to the source. Re-encoded frames are at least 46 dB PSNR.
- 100 cuts: video and audio durations within 30 ms (AAC end padding).
- AAC sync on a longer excerpt: MP4 exact, MKV within 0.3 ms.
- No software decode errors. VideoToolbox decode of one output reported none.
- HDR10 mastering display and light level metadata are kept.

## Real files

Short excerpts of real files passed frame checks, after fixing problems the synthetic clips did not show: uneven frame timestamps, CRA joins, undecodable leading frames, re-encoded pieces shifted by one frame, and a first audio track in the wrong language.

- Re-encoded sections can use more bitrate than the source, so output may grow.
- FLAC audio was dropped because it grew the audio several times over.

## VLC playback glitch

VLC 3.0.24 on macOS showed a grey picture or a black flash at the first join. VLC's log shows why: its VideoToolbox decoder fails with `kVTVideoDecoderBadDataErr` when the VPS/SPS/PPS change, and VLC falls back to software decoding for the rest of the file.

`vlcfail.sh <seconds> <files>` detects this from VLC's log. The decoder failed on every run where VPS/SPS/PPS differed at a join, and on no run where they were identical.

- Cuts only play cleanly in VLC when the re-encoded sections have the same VPS/SPS/PPS as the source, or the mismatch is handled another way (untried: separate parameter set IDs, all declared in the container header).
- ffmpeg decodes these files correctly, so the frame checks do not catch this. `vlctest.py` did not catch it either.

## H.264 open GOP

Starting a copy on a non-IDR keyframe lost frames and corrupted the picture. The prototype only starts H.264 copies on IDR frames. A source with few IDR frames is then mostly re-encoded.

## Not tested

- A full-length real file with the current code, and more real files
- Codecs other than H.264 and HEVC (AV1, VP9, MPEG-2, VC-1, MPEG-4). The prototype would wrongly re-encode their edges as HEVC.
- Playback in real players and on TVs
- Dolby Vision and HDR10+
- Variable frame rate, interlaced, non-zero start times, multiple audio tracks
- Chapters and subtitles
- Hardware encoders for the re-encoded sections
- Speed and temporary disk use on full-length files (audio is written to disk as raw PCM)

## Full re-encode measurement

`measure.py` compares re-encodes with their source using VMAF. Hardware encoding at `-q:v 65` showed no visible difference by eye on short samples. Output size depends heavily on the source.
