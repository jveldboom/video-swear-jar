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
- AAC sync on a 5-minute real excerpt: MP4 exact, MKV within 0.3 ms.
- No software decode errors. VideoToolbox decode of one output reported none.
- HDR10 mastering display and light level metadata are kept.

## Real file

HEVC 10-bit SDR, 1920x804, 60 fps, 5.1 AAC. A 60-second excerpt passed with 6 cuts: all frames present, copied frames bit-identical, frame spacing matching the source, no decode errors.

A real file exposed problems the synthetic clips did not: uneven frame timestamps, CRA joins, undecodable leading frames, and re-encoded pieces shifted by one frame.

FLAC audio was dropped: on a full-length file it grew the audio from 202 MB to 1,106 MB.

A second real file, HEVC 8-bit SDR 3840x2160 at 23.976 fps with two 5.1 E-AC-3 tracks, passed on a 60-second excerpt:

- All frames present, 1083 of 1337 copied bit-identical, no decode errors, audio within 0.3 ms.
- VPS/SPS/PPS differ between copied and re-encoded sections. VLC's VideoToolbox decoder was clean over the first 15 seconds, 3 runs.
- Video grew from 156 MB to 195 MB with a cut about every 10 seconds, because the CRF 14 sections use more bitrate than the source.
- The first audio track was not English. The prototype now picks the first English track.

## VLC playback glitch

VLC 3.0.24 on macOS showed a grey picture or a black flash at the first join. VLC's log shows why: its VideoToolbox decoder fails with `kVTVideoDecoderBadDataErr` when the VPS/SPS/PPS change, and VLC falls back to software decoding for the rest of the file.

`vlcfail.sh <seconds> <files>` detects this from VLC's log, 3 runs per file:

| File | VPS/SPS/PPS at joins | Decoder failed |
|---|---|---|
| 4K source, not cut | No joins | 0 of 3 |
| 4K cut | Differ | 3 of 3 |
| 1080p cut, before the frame rate fix | Differ | 3 of 3 |
| 1080p cut, after the fix | Identical | 0 of 3 |

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

`measure.py` on an M3 Pro, 60-second samples, software decoding. VMAF compares each encode with its source.

```text
1080p sample: 1920x804 yuv420p10le 60/1 fps, source video 7.0 MB
  hardware-q65: vmaf mean 96.0, worst 1% 93.8, min 92.6, frames 3684; video 29.5 MB; encode 84 s for 62 s of video
  hardware-q75: vmaf mean 97.4, worst 1% 96.0, min 95.2, frames 3684; video 59.5 MB; encode 72 s for 62 s of video
  software-crf18: vmaf mean 96.4, worst 1% 93.0, min 92.0, frames 3684; video 10.5 MB; encode 83 s for 62 s of video
4K sample: 3840x2160 yuv420p 24000/1001 fps, source video 156.2 MB
  hardware-q65: vmaf mean 94.1, worst 1% 88.1, min 87.4, frames 1467; video 131.7 MB; encode 55 s for 63 s of video
  hardware-q75: vmaf mean 97.1, worst 1% 92.9, min 92.5, frames 1467; video 258.0 MB; encode 56 s for 63 s of video
  software-crf18: vmaf mean 97.2, worst 1% 93.1, min 92.6, frames 1467; video 277.7 MB; encode 343 s for 63 s of video
```

The encode times above are too high: the machine was heavily loaded. Rerun at lighter load with `remove-cuts.sh` settings (hardware q65) took 14 s for the 1080p sample (not 84 s) and 28 s for the 4K sample (not 55 s), about 11 and 25 minutes full length. Sizes and VMAF are unaffected by load.
