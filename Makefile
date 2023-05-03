# defaults
DOCKER_TAG := video-swear-jar
DIR := $(shell pwd)

build:
	docker build -t ${DOCKER_TAG} .

## Targets Used for Development
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

clean:
	docker run -it --rm \
		-v ${DIR}:/app \
		${DOCKER_TAG} \
		node src/clean.js --input data/test.mkv

cut_video:
	docker run -it --rm \
		-v ${DIR}:/app \
		${DOCKER_TAG} \
    ffmpeg -f concat -i ${CUT_FILE} -c copy ${VIDEO_FILE}-cut.mkv

bash:
	docker run -it --rm \
		-v ${DIR}:/app \
		-v ${DIR}/.whisper:/root/.cache/whisper \
		${DOCKER_TAG} /bin/bash
