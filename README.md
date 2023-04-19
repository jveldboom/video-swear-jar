# Video Swear Jar - The AI-Powered Profanity Filter

Introducing Video Swear Jar, your AI-powered solution for clean video content! This project offers a Docker container with all necessary tools to process videos. It transcribes, detects profanity, and trims out inappropriate language, delivering a new, family-friendly video file. Embrace the convenience of our all-in-one profanity filtering solution and create a suitable viewing experience for all ages.

## Process Overview:
- [OpenAI Whisper](https://github.com/openai/whisper/) to transcribe the video file
- Node script to process the transcription file
  - Detects profanity based on predefined [swear-jar.json](src/swear-jar.json) file
  - Creates an ffmpeg video cut file
- FFmpeg to cut the video file at specified times and create new video file

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

## TODO
- [x] Add Node to container to run everything within the container
- [ ] Finalize initial documentation with required steps to run
- [ ] Build scripts into container to not use root Makefile as the local interface
- [ ] Publish image to GitHub Packages
- [ ] Clean up files after process is complete
- [ ] Create CI jobs to run on PRs
- [ ] Create build jobs to version and publish to GH Packages

## Features
- [ ] Ability to pass in custom swear-jar file (both replace and add)
- [ ] Run all processes within Node or shell script to prevent the ugly passing of variables in the Makefile
