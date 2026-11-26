# usage: measure.py sample...   Encodes are written to ./quality-test
import json, os, subprocess as sp, sys, time
from smartcut import run, audio_index
OUT = 'quality-test'; os.makedirs(OUT, exist_ok=True)

def video_mb(p):
    o = run('ffprobe','-v','error','-select_streams','v','-show_entries','packet=size','-of','csv=p=0',p).stdout
    return sum(int(x.split(',')[0]) for x in o.split() if x.split(',')[0]) / 1e6

for src in sys.argv[1:]:
    name = os.path.splitext(os.path.basename(src))[0]
    s = json.loads(run('ffprobe','-v','error','-select_streams','v:0','-show_streams','-of','json',src).stdout)['streams'][0]
    ten = '10' in s['pix_fmt']
    model = 'vmaf_4k_v0.6.1' if s['width'] > 2560 else 'vmaf_v0.6.1'
    color = [x for k, o in (('color_primaries','-color_primaries'),('color_transfer','-color_trc'),('color_space','-colorspace'),('color_range','-color_range'))
             if s.get(k) not in (None,'unknown') for x in (o, s[k])]
    hw = lambda q: ['-c:v','hevc_videotoolbox','-q:v',q,'-pix_fmt','p010le' if ten else 'nv12','-profile:v','main10' if ten else 'main','-tag:v','hvc1']
    sw = ['-c:v','libx265','-crf','18','-preset','medium','-pix_fmt',s['pix_fmt'],'-x265-params','log-level=error']
    print(f"{name}: {s['width']}x{s['height']} {s['pix_fmt']} {s['r_frame_rate']} fps, source video {video_mb(src):.1f} MB", flush=True)
    for label, enc in (('hardware-q65', hw('65')), ('hardware-q75', hw('75')), ('software-crf18', sw)):
        dst = f'{OUT}/{name}.{label}.mkv'
        t = time.time()
        run('ffmpeg','-v','error','-y','-i',src,'-map','0:v:0','-map',f'0:a:{audio_index(src)}',*enc,*color,'-fps_mode','passthrough','-c:a','copy',dst)
        secs = time.time() - t
        fmt = 'yuv420p10le' if ten else 'yuv420p'
        graph = (f"[0:v]settb=AVTB,setpts=N/({s['r_frame_rate']})/TB,format={fmt}[d];[1:v]settb=AVTB,setpts=N/({s['r_frame_rate']})/TB,format={fmt}[r];"
                 f"[d][r]libvmaf=model=version={model}:n_threads=10:log_fmt=json:log_path=vmaf.json")
        run('ffmpeg','-v','error','-i',dst,'-i',src,'-filter_complex',graph,'-f','null','-')
        fr = sorted(f['metrics']['vmaf'] for f in json.load(open('vmaf.json'))['frames'])
        dur = float(run('ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',src).stdout)
        print(f"  {label}: vmaf mean {sum(fr)/len(fr):.1f}, worst 1% {fr[len(fr)//100]:.1f}, min {fr[0]:.1f}, frames {len(fr)}; "
              f"video {video_mb(dst):.1f} MB; encode {secs:.0f} s for {dur:.0f} s of video", flush=True)
