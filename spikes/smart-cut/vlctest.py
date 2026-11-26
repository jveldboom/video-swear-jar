# Decode a file with VLC's own VideoToolbox decoder and compare each frame with ffmpeg's decode.
import sys, os, subprocess as sp, numpy as np
def small(p, t=None):
    r = sp.run(['ffmpeg','-v','error','-i',p,'-map','0:v:0',*(['-t',t] if t else []),'-vf','scale=240:104,format=gray','-fps_mode','passthrough','-f','rawvideo','-'],capture_output=True).stdout
    return np.frombuffer(r,np.uint8).reshape(-1,240*104).astype(np.float32)
def run(src, secs, runs):
    ref = small(src, str(secs+2))
    for n in range(runs):
        dst = os.path.abspath('vlccap/t.mkv'); 
        if os.path.exists(dst): os.remove(dst)
        sp.run(['/Applications/VLC.app/Contents/MacOS/VLC','-I','dummy','--no-media-library','--no-audio',f'--run-time={secs}','--play-and-exit','--codec=videotoolbox',
                '--sout',f'#transcode{{vcodec=h264,vb=40000}}:std{{access=file,mux=mkv,dst={dst}}}',os.path.abspath(src)], capture_output=True, timeout=120)
        got = small(dst)
        err = np.array([np.abs(ref - g).mean(1).min() for g in got])     # distance to the closest correct frame
        bad = [i for i, e in enumerate(err) if e > 8]
        print(f'run {n+1}: {len(got)} frames, worst error {err.max():.1f}, median {np.median(err):.2f}, bad frames {len(bad)}', f'(from {bad[0]} to {bad[-1]})' if bad else '', flush=True)
        if bad:
            sp.run(['ffmpeg','-v','error','-y','-i',dst,'-vf',f'select=eq(n\\,{bad[len(bad)//2]})','-frames:v','1','vlccap/bad.png'])
if __name__ == '__main__':
    run(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
