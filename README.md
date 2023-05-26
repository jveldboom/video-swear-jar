# Video Swear Jar - The AI-Powered Profanity Filter

Introducing Video Swear Jar, your AI-powered solution for creating clean video content! This project offers a Docker container with all necessary tools to process videos, transcribe the audio, detect profanity, and remove inappropriate language, delivering a new, family-friendly video file.

## Project Goals
- Simplify the process of removing profanity from video files. The current process is quite technical, and we aim to make it more user-friendly.
- Enable local processing without relying on an internet connection.
- Minimize cost for users by keeping the solution as affordable as possible.

## Process Overview
- Transcribe the video file using [OpenAI Whisper](https://github.com/openai/whisper/)
- Process the transcription file:
  - Detects profanity based on predefined [swear-words.json](src/swear-words.json) file
  - Generate an FFmpeg video cut file.
- Use FFmpeg to cut the video file at specified times and create a new, edited video file.

## Requirements
- Docker installed

## Usage
```sh
# create new video file with profanity removed
docker run --rm -it \
  -v $(pwd):/data jveldboom/video-swear-jar:v1 \
  clean --input video.mkv --model tiny.en --language en

# recommended to mount a ".whisper" directory to locally cache large language models
docker run --rm -it \
  -v $(pwd):/data \
  -v $(pwd)/.whisper:/app/.whisper jveldboom/video-swear-jar:v1 \
  clean --input video.mkv --model tiny.en --language en
```

### Arguments
- `--input` - path to video file
- `--model` - whisper model name - `tiny`, `tiny.en` (default), `base`, `base.en`, `small`, `small.en`, `medium`, `medium.sm`, `large`. View [official docs](https://github.com/openai/whisper#available-models-and-languages) for break down of model size and performance
- `--language` - language code. Typically improves in transcription to set language instead of allowing Whisper to auto-detect.

### Known Issues
- `Error: Command "whisper" exited with code null` - this is likely caused by the container needing more allocated memory. Allocating at least 4 GB memory for the `small.en` usually resolved the issue but your mileage may vary.

## Utility Commands
There are a handful of utility commands that I find useful in the workflow to edit a video that are available in the Docker container.

### `cut-video`
Allows you to manually create a list of timestamps to cut the video.

Usage:
```shell
docker run --rm -it -v $(pwd):/data video-swear-jar \
  cut-video --timestamp timestamps.txt --video video.mkv
```

- `--timestamp` - path to file with timestamps. Each timestamp must be on a new line in `HH:MM:SS - HH:MM:SS` format
- `--video` - path to video to cut the video
- `--cut-video` - optional boolean to set to not cut video but only output cut file

### `whisper`
This is the `whisper` CLI if you need to further customize the command. Visit https://github.com/openai/whisper for full details

Usage:
```shell
docker run --rm -it -v $(pwd):/data video-swear-jar \
  whisper my-video.mp4 \
    --model tiny.en \
    --language en \
    --output_format json \
    --output_dir data
```

### ffmpeg
Usage:
```shell
docker run --rm -it -v $(pwd):/data video-swear-jar \
  ffmpeg -i input.mp4 output.avi
```

## Roadmap
- [x] Add Node to container to run everything within the container
- [x] Finalize initial documentation with required steps to run
- [x] Include scripts into container to not use root Makefile as the local interface
- [x] Run all processes within a Node or shell script to eliminate the need for passing variables in the Makefile
- [x] Improve logging to let users know what steps are being ran
- [x] Create CI jobs to run on PRs
- [x] Create build jobs to version and publish container image
- [x] Allow user to define output directory
- [x] Create logging abstraction for `info`, `warning`, `error`, `debug`, etc
- [ ] Add unit tests
- [x] Add debug flag to commands
- [ ] Clean up files after process is complete
- [ ] Allow users to pass in a custom swear-words.json file (replace or add)

## Notes
### Alternatives
Below is a small list of possible alternatives to vide-swear-jar.
- [AWS Transcribe](https://aws.amazon.com/pm/transcribe/) - in my testing this provides very good results but is relatively expensive for small projects plus it requires uploading your video files to the cloud.
- [OpenAI Whisper API](https://openai.com/blog/introducing-chatgpt-and-whisper-apis) - requires uploading video to cloud

### Tools
Small list of tool I use in my workflow
- [MakeMKV](https://www.makemkv.com/) - "convert videos (DVD/Blu-ray) that you own into free and patents-unencumbered format that can be played everywhere"
