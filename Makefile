# defaults
DOCKER_TAG := video-swear-jar
DIR := $(shell pwd)

build:
	docker build -t ${DOCKER_TAG} .

## Testing
test-clean:
	docker run --rm \
		-v ${DIR}/.whisper:/app/.whisper \
		-v ${DIR}/examples:/data \
		${DOCKER_TAG} \
		clean -i /data/curious-george.mp4 -m tiny.en -l en

## Targets Used for Development
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

bash:
	docker run -it --rm \
		-v ${DIR}/examples:/data \
		${DOCKER_TAG} /bin/bash
