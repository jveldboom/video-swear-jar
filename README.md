# Video Swear Jar - The AI-Powered Profanity Filter

Introducing Video Swear Jar, your AI-powered solution for creating clean video content! This project offers a Docker container with all necessary tools to process videos, transcribe the audio, detect profanity, and remove inappropriate language, delivering a new, family-friendly video file.

## Project Goals
- Simplify the process of removing profanity from video files. The current process is quite technical, and we aim to make it more user-friendly.
- Enable local processing without relying on an internet connection.
- Minimize cost for users by keeping the solution as affordable as possible.

## Process Overview:
- Transcribe the video file using [OpenAI Whisper](https://github.com/openai/whisper/)
- Process the transcription file with a Node script:
  - Detects profanity based on predefined [swear-jar.json](src/swear-jar.json) file
  - Generate an FFmpeg video cut file.
- Use FFmpeg to cut the video file at specified times and create a new, edited video file.

## Requirements:
- Docker
- Shell environment to run Make targets (only tested on Mac)

## Usage
```sh
# build docker container
make build

# create new video file with profanity removed
make all \
    VIDEO_FILE=video.mkv
    WHISPER_MODEL=small.en

# run steps individually
# transcribe video to text
make whisper VIDEO_FILE=video.mkv

# detect profanity in transcription and create ffmpeg cut file
make swear_jar VIDEO_FILE=video.mkv

# cut profanity and create new video file
make cut_video VIDEO_FILE=video.mkv
```

## Roadmap
- [x] Add Node to container to run everything within the container
- [ ] Finalize initial documentation with required steps to run
- [ ] Include scripts into container to not use root Makefile as the local interface
- [ ] Publish image to GitHub Packages
- [ ] Clean up files after process is complete
- [ ] Create CI jobs to run on PRs
- [ ] Create build jobs to version and publish to GH Packages

## Future Features
- [ ] Allow users to pass in a custom swear-jar file (replace or add)
- [ ] Run all processes within a Node or shell script to eliminate the need for passing variables in the Makefile

## Notes
### Alternatives
- [AWS Transcribe](https://aws.amazon.com/pm/transcribe/)
- [OpenAI Whisper API](https://openai.com/blog/introducing-chatgpt-and-whisper-apis)

### Tools
- [MakeMKV](https://www.makemkv.com/) - "convert videos (DVD/Blu-ray) that you own into free and patents-unencumbered format that can be played everywhere"
- [Handbrake](https://handbrake.fr/) - "open-source tool, built by volunteers, for converting video from nearly any format to a selection of modern, widely supported codecs"