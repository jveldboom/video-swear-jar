## ffmpeg

### Cut Start of Video
```sh
ffmpeg \
  -ss 00:00:25 \
  -i input.mkv \
  -vcodec copy \
  -acodec copy output.mkv
```