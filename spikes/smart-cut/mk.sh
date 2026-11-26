set -e
SRC="testsrc2=size=640x360:rate=24000/1001:duration=60"
AUD="sine=frequency=440:beep_factor=4:sample_rate=48000:duration=60"
gen(){ n=$1; shift; ffmpeg -v error -y -f lavfi -i "$SRC" -f lavfi -i "$AUD" "$@" -c:a ac3 -shortest clips/$n.mkv; }
gen h264_closed -pix_fmt yuv420p -c:v libx264 -g 48 -bf 3
gen h264_open   -pix_fmt yuv420p -c:v libx264 -g 48 -bf 3 -x264-params open-gop=1
gen h264_10bit  -pix_fmt yuv420p10le -c:v libx264 -g 48
gen hevc_closed -pix_fmt yuv420p -c:v libx265 -x265-params open-gop=0:keyint=48:log-level=error
gen hevc_open   -pix_fmt yuv420p -c:v libx265 -x265-params open-gop=1:keyint=48:log-level=error
gen hevc_hdr10  -pix_fmt yuv420p10le -c:v libx265 -color_primaries bt2020 -color_trc smpte2084 -colorspace bt2020nc -x265-params "open-gop=1:keyint=48:log-level=error:hdr10=1:repeat-headers=1:colorprim=bt2020:transfer=smpte2084:colormatrix=bt2020nc:master-display=G(13250,34500)B(7500,3000)R(34000,16000)WP(15635,16450)L(10000000,1):max-cll=1000,400"
