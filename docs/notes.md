## ffmpeg

### Cut Start of Video
```sh
ffmpeg \
  -ss 00:00:25 \
  -i input.mkv \
  -vcodec copy \
  -acodec copy output.mkv
```

## Whisper Research
- [Making OpenAI Whisper faster](https://nikolas.blog/making-openai-whisper-faster/)
- https://github.com/guillaumekln/faster-whisper - Faster Whisper transcription with CTranslate2
- https://github.com/Softcatala/whisper-ctranslate2 - Whisper command line client compatible with original OpenAI client based on CTranslate2
