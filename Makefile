# defaults
DOCKER_TAG := video-swear-jar
DIR := $(shell pwd)
# VIDEO_FILE := data/test.mkv
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
			--model ${WHISPER_MODEL} \
			--language en \
			--output_format json \
			--output_dir data

swear_jar:
	VIDEO_FILE=${VIDEO_FILE} node src/run.js

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