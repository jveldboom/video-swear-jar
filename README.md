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
# build docker container
make build

# create new video file with profanity removed
docker run --rm -it -v $(pwd):/app video-swear-jar \
  clean --input video.mkv --model tiny.en --language en
```

## Available Whisper models and languages
View the [Whisper docs](https://github.com/openai/whisper#available-models-and-languages) for full list and explanation for each. Below is a quick list.

|  Size  | Parameters | English-only model | Multilingual model | Required VRAM | Relative speed |
|:------:|:----------:|:------------------:|:------------------:|:-------------:|:--------------:|
|  tiny  |    39 M    |     `tiny.en`      |       `tiny`       |     ~1 GB     |      ~32x      |
|  base  |    74 M    |     `base.en`      |       `base`       |     ~1 GB     |      ~16x      |
| small  |   244 M    |     `small.en`     |      `small`       |     ~2 GB     |      ~6x       |
| medium |   769 M    |    `medium.en`     |      `medium`      |     ~5 GB     |      ~2x       |
| large  |   1550 M   |        N/A         |      `large`       |    ~10 GB     |       1x       |

## Known Issues
- `Error: Command "whisper" exited with code null` - this is likely caused by the container needing more allocated memory. Allocating at least 4 GB memory for the `small.en` usually resolved the issue but your mileage may vary.

## Roadmap
- [x] Add Node to container to run everything within the container
- [x] Finalize initial documentation with required steps to run
- [x] Include scripts into container to not use root Makefile as the local interface
- [x] Run all processes within a Node or shell script to eliminate the need for passing variables in the Makefile
- [x] Improve logging to let users know what steps are being ran
- [ ] Publish image to GitHub Packages
- [ ] Clean up files after process is complete
- [ ] Create CI jobs to run on PRs
- [ ] Create build jobs to version and publish to GH Packages
- [ ] Allow users to pass in a custom swear-words.json file (replace or add)

## Notes
### Alternatives
- [AWS Transcribe](https://aws.amazon.com/pm/transcribe/)
- [OpenAI Whisper API](https://openai.com/blog/introducing-chatgpt-and-whisper-apis)

### Tools
- [MakeMKV](https://www.makemkv.com/) - "convert videos (DVD/Blu-ray) that you own into free and patents-unencumbered format that can be played everywhere"
- [Handbrake](https://handbrake.fr/) - "open-source tool, built by volunteers, for converting video from nearly any format to a selection of modern, widely supported codecs"