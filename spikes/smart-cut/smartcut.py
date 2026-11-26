import bisect, re, json, math, subprocess as sp, sys, tempfile, os, re
from fractions import Fraction

def run(*a): return sp.run(a, check=True, capture_output=True, text=True)

def probe(src):
    s = json.loads(run('ffprobe','-v','error','-select_streams','v:0','-show_streams','-of','json',src).stdout)['streams'][0]
    out = run('ffprobe','-v','error','-select_streams','v:0','-show_entries','packet=pts_time,flags','-of','csv=p=0',src).stdout
    pk = [(float(l.split(',')[0]), 'K' in l.split(',')[1]) for l in out.split()]
    first = next(p for p, k in pk if k)
    pk = [x for x in pk if x[0] >= first]
    rank = {p: i for i, p in enumerate(sorted(p for p, _ in pk))}
    pk = [(rank[p], k, p) for p, k in pk]           # decode order: (frame no, is key, pts)
    s['times'] = sorted(p for _, _, p in pk)
    s['times'].append(s['times'][-1] + float(1/Fraction(s['r_frame_rate'])))
    keys = []
    for i, (f, k, t) in enumerate(pk):
        if not k: continue
        lead = 0
        for g, _, _ in pk[i+1:]:                      # leading pictures: decoded after, shown before
            if g < f: lead += 1
            else: break
        keys.append(dict(i=i, f=f, t=t, lead=lead))
    if s['codec_name'] == 'h264':               # only IDR frames are safe places to start a copy
        o = run('ffmpeg','-v','error','-copyts','-i',src,'-map','0:v:0','-c','copy','-bsf:v','h264_mp4toannexb,filter_units=pass_types=5','-f','framecrc','-').stdout
        tb = Fraction(re.search(r'#tb 0: (\S+)', o).group(1))
        idr = [float(int(l.split(',')[2])*tb) for l in o.splitlines() if l[0] != '#']
        for k in keys: k['idr'] = any(abs(k['t']-t) < 0.002 for t in idr)
    return s, pk, keys

def keeps(removals, times):
    out, prev, total = [], 0, len(times) - 1
    for a, b in sorted(removals):
        a, b = max(0, bisect.bisect_right(times, a+1e-3)-1), min(total, bisect.bisect_left(times, b-1e-3))
        if a > prev: out.append((prev, a))
        prev = max(prev, b)
    if prev < total: out.append((prev, total))
    return out

def plan(ks, pk, keys):
    s, e = ks
    total = len(pk)
    start = next((k for k in keys if k['f'] >= s and k.get('idr', True)), None)
    ends = [(k['f'] - k['lead'], k['i']) for k in keys] + [(total, total)]
    if start:
        ok = [(f, i) for f, i in ends if start['f'] < f <= e and i > start['i']]
        if ok:
            f, i = ok[-1]
            return [p for p in [('enc', s, start['f']), ('copy', start['f'], f, start, i), ('enc', f, e)] if p[2] > p[1]]
    return [('enc', s, e)]

def encoder(s):
    pix = s['pix_fmt']
    color = []
    for k, o in (('color_primaries','-color_primaries'),('color_transfer','-color_trc'),('color_space','-colorspace'),('color_range','-color_range')):
        if s.get(k) not in (None, 'unknown'): color += [o, s[k]]
    if s['codec_name'] == 'h264':
        return ['-c:v','libx264','-crf','14','-pix_fmt',pix,*color,'-x264-params',f"fps={s['r_frame_rate']}"]
    p = ['log-level=error','open-gop=0','repeat-headers=1',f"fps={s['r_frame_rate']}"]
    return ['-c:v','libx265','-crf','14','-pix_fmt',pix,*color,'-x265-params',':'.join(p)]

def cra_to_bla(path):
    """Relabel a copied piece's first keyframe from CRA (21) to BLA_N_LP (18) so the
    decoder restarts picture numbering at the join without discarding earlier frames."""
    d = bytearray(open(path, 'rb').read())
    es, where = bytearray(), []          # video payload and each byte's offset in the TS file
    for p in range(0, len(d), 188):
        if ((d[p+1] & 0x1f) << 8 | d[p+2]) != 0x100 or not d[p+3] & 0x10: continue
        i = p + 4 + (1 + d[p+4] if d[p+3] & 0x20 else 0)
        if d[p+1] & 0x40:                # a new frame starts here
            if es: break                 # only the first frame needs patching
            i += 9 + d[i+8]              # skip the PES header
        es += d[i:p+188]; where += range(i, p+188)
    for m in re.finditer(b'\x00\x00\x01', bytes(es)):
        o = m.end()
        if (es[o] >> 1) & 63 == 21: d[where[o]] = (es[o] & 0x81) | (18 << 1)
    open(path, 'wb').write(d)

def video(src, removals, work):
    s, pk, keys = probe(src)
    fps = Fraction(s['r_frame_rate'])
    T = s['times']
    ranges = keeps(removals, T)
    h264 = s['codec_name'] == 'h264'
    bsf = 'h264_mp4toannexb' if h264 else 'hevc_mp4toannexb'
    pieces, stats = [], dict(copy=0, enc=0)
    t0 = float(run('ffprobe','-v','error','-show_entries','format=start_time','-of','csv=p=0',src).stdout)
    for ks in ranges:
        for p in plan(ks, pk, keys):
            out = f'{work}/{len(pieces):05d}.ts'
            n = p[2] - p[1]
            seek = lambda f: f'{max(0, T[f] - t0 - float(1/fps)/2):.6f}'
            if p[0] == 'enc':
                run('ffmpeg','-v','error','-y','-ss',seek(p[1]),'-i',src,'-map','0:v:0','-frames:v',str(n),'-vf','setpts=PTS-STARTPTS','-fps_mode','passthrough','-enc_time_base','demux',*encoder(s),'-f','mpegts',out)
            else:
                k, endi = p[3], p[4]
                # packets from this keyframe to the end keyframe, minus its leading pictures
                count = endi - k['i']
                half = float(1/fps)/2
                drop = f",noise=drop='lt(pts*tb\\,{k['t']-half:.6f})'"
                run('ffmpeg','-v','error','-y','-ss',f"{max(0,k['t']-t0-1):.6f}",'-copyts','-i',src,'-map','0:v:0','-c','copy',
                    '-bsf:v',bsf+(',dump_extra=freq=keyframe' if h264 else '')+drop,'-frames:v',str(n),'-muxdelay','0','-f','mpegts',out)
                if not h264: cra_to_bla(out)
            stats[p[0]] += n
            pieces.append((out, T[p[2]] - T[p[1]]))
    lst = f'{work}/list.txt'
    open(lst,'w').write(''.join(f"file '{f}'\nduration {d:.9f}\n" for f, d in pieces))
    return s, fps, ranges, lst, stats

def audio(src, ranges, T, work):
    info = json.loads(run('ffprobe','-v','error','-select_streams',f'a:{audio_index(src)}','-show_streams','-of','json',src).stdout)['streams'][0]
    rate, ch = int(info['sample_rate']), info['channels']
    raw, cut = f'{work}/a.raw', f'{work}/cut.raw'
    run('ffmpeg','-v','error','-y','-copyts','-i',src,'-map',f'0:a:{audio_index(src)}','-af','aresample=async=1:first_pts=0','-f','s32le','-c:a','pcm_s32le',raw)
    w = 4*ch
    with open(raw,'rb') as i, open(cut,'wb') as o:
        for a, b in ranges:
            x, y = round(T[a]*rate), round(T[b]*rate)
            i.seek(x*w); o.write(i.read((y-x)*w))
    return ['-f','s32le','-ar',str(rate),'-ch_layout',info.get('channel_layout',f'{ch}c'),'-i',cut]

def audio_index(src):
    """First English track, else the first track."""
    langs = run('ffprobe','-v','error','-select_streams','a','-show_entries','stream_tags=language','-of','default=nw=1:nk=1',src).stdout.split()
    return langs.index('eng') if 'eng' in langs else 0

def channels(src):
    return int(run('ffprobe','-v','error','-select_streams',f'a:{audio_index(src)}','-show_entries','stream=channels','-of','csv=p=0',src).stdout.split(',')[0])

def smartcut(src, removals, dst):
    with tempfile.TemporaryDirectory() as work:
        s, fps, ranges, lst, stats = video(src, removals, work)
        a = audio(src, ranges, s['times'], work)
        tag = ['-tag:v','hev1'] if s['codec_name']=='hevc' and dst.endswith('.mp4') else []
        r = run('ffmpeg','-v','warning','-y','-f','concat','-safe','0','-i',lst,*a,'-map','0:v','-map','1:a','-c:v','copy','-bsf:v',f"setts=pts=PTS:dts='(N-8)/({fps})/TB'",*tag,'-c:a','aac','-b:a',f'{min(640, 128*channels(src))}k',dst)
        return dict(ranges=ranges, fps=fps, stats=stats, mux_warnings=r.stderr)
