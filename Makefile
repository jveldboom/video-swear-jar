# defaults
DOCKER_TAG := video-swear-jar
DIR := $(shell pwd)
VIDEO_FILE := data/test.mkv
WHISPER_MODEL := small.en

build:
	docker build -t ${DOCKER_TAG} .

audio:
	docker run -it --rm -v ${DIR}:/app ${DOCKER_TAG} \
		ffmpeg -i ${VIDEO_FILE} -vn -acodec pcm_s16le -ar 16000 -af "highpass=f=100" -ac 1 ${AUDIO_OUTPUT}

whisper:
	docker run -it --rm \
		-v ${DIR}:/app \
		-v ${DIR}/.whisper:/root/.cache/whisper \
		${DOCKER_TAG} \
		whisper ${VIDEO_FILE} \
			--model ${MODEL} \
			--language ${LANG} \
			--output_format json \
			--output_dir data

swear-jar:
	docker run -it --rm \
		-v ${DIR}:/app \
		-e VIDEO_FILE=${VIDEO_FILE} \
		-e MODEL=${MODEL} \
		-e LANG=${LANG} \
		${DOCKER_TAG} \
		node src/run.js

cut_video:
	docker run -it --rm \
		-v ${DIR}:/app \
		${DOCKER_TAG} \
    ffmpeg -f concat -i ${VIDEO_FILE}-cut.txt -c copy ${VIDEO_FILE}-output.mp4

bash:
	docker run -it --rm \
		-v ${DIR}:/app \
		-v ${DIR}/.whisper:/root/.cache/whisper \
		${DOCKER_TAG} /bin/bash

all:
	$(MAKE) whisper swear_jar cut_video