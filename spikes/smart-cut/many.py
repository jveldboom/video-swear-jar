import os, subprocess as sp
from smartcut import *
from check import check, md5s
sp.run('ffmpeg -v error -y -f lavfi -i testsrc2=size=640x360:rate=24000/1001:duration=420 -f lavfi -i sine=beep_factor=4:sample_rate=48000:duration=420 -ac 6 -pix_fmt yuv420p10le -c:v libx265 -x265-params open-gop=1:keyint=48:log-level=error -c:a ac3 clips/long.mkv',shell=True,check=True)
cuts = [(i*4+1.37, i*4+1.97) for i in range(100)]
for dst in ('long.out.mkv','long.out.mp4'):
    print(dst, check('clips/long.mkv', dst, smartcut('clips/long.mkv', cuts, dst)))
