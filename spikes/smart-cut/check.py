import sys, subprocess as sp, re, json, random, collections
from smartcut import *

def md5s(path, vf=None):
    a = ['ffmpeg','-v','error','-i',path,'-map','0:v:0'] + (['-vf',vf] if vf else []) + ['-fps_mode','passthrough','-f','framemd5','-']
    r = sp.run(a, capture_output=True, text=True)
    return [l.split(',')[-1].strip() for l in r.stdout.splitlines() if l and l[0] != '#'], r.stderr

def check(src, dst, res):
    sel = '+'.join(f'between(n\\,{a}\\,{b-1})' for a, b in res['ranges'])
    want = sum(b-a for a, b in res['ranges'])
    exp, _ = md5s(src, f"select='{sel}'")
    got, err = md5s(dst)
    fps = res['fps']
    f = f"[0:v]settb=AVTB,setpts=N/({fps})/TB[a];[1:v]select='{sel}',settb=AVTB,setpts=N/({fps})/TB[b];[a][b]psnr=stats_file=psnr.log"
    sp.run(['ffmpeg','-v','error','-y','-i',dst,'-i',src,'-filter_complex',f,'-f','null','-'], capture_output=True)
    psnr = [float(m) for m in re.findall(r'psnr_avg:(\S+)', open('psnr.log').read())]
    pts = sorted(float(x.strip(',')) for x in run('ffprobe','-v','error','-select_streams','v','-show_entries','packet=pts_time','-of','csv=p=0',dst).stdout.split())
    T = probe(src)[0]['times']                      # compare against the source's own frame spacing
    want_gaps = [T[i+1]-T[i] for x, y in res['ranges'] for i in range(x, y)]
    bad_gap = sum(abs((q-p)-w) > 0.002 for p, q, w in zip(pts, pts[1:], want_gaps))
    adur = len(sp.run(['ffmpeg','-v','error','-i',dst,'-map','0:a','-ac','1','-f','s16le','-'],capture_output=True).stdout)/2/48000
    return dict(frames=f'{len(got)}/{want}', exact=sum(a==b for a,b in zip(got,exp)), copied=res['stats']['copy'],
        min_psnr=round(min(psnr),1), below35=sum(p<35 for p in psnr), bad_ts=bad_gap,
        v_s=round(pts[-1]-pts[0]+float(1/fps),3), a_s=round(adur,3),
        decode_err=err.strip().splitlines()[:3], mux=res['mux_warnings'].strip().splitlines()[:3])

if __name__ == '__main__':
    cuts = [(3.3,4.1),(11.0,11.4),(23.7,29.2),(41.5,42.0)]
    for src in sys.argv[1:]:
        dst = 'out_' + os.path.basename(src)
        try: print(os.path.basename(src), check(src, dst, smartcut(src, cuts, dst)))
        except sp.CalledProcessError as e: print(src, 'FAIL', e.stderr[-600:])
