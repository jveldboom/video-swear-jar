# usage: vlcfail.sh seconds file... : did VLC's hardware decoder fail during playback?
secs=$1; shift
for f in "$@"; do
  for i in 1 2 3; do
    log=$(mktemp)
    /Applications/VLC.app/Contents/MacOS/VLC -I dummy --vout=dummy --aout=dummy --no-media-library -vv --run-time=$secs --play-and-exit "$f" > $log 2>&1 & p=$!
    ( perl -e 'sleep(shift)' $((secs+25)); kill -9 $p 2>/dev/null ) & w=$!; wait $p; kill $w 2>/dev/null; wait $w 2>/dev/null
    echo "$(basename "$f") run $i: failures $(grep -c 'decoder failure' $log), $(grep -o "vt session error: '[A-Za-z]*'" $log | head -1)"
    rm $log
  done
done
