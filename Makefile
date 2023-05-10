# defaults
IMAGE_NAME := jveldboom/video-swear-jar
IMAGE_VERSION := latest
IMAGE_TAG := ${IMAGE_NAME}:${IMAGE_VERSION}
DIR := $(shell pwd)

build:
	docker build -t ${IMAGE_TAG} .

tag-major:
	docker tag ${IMAGE_TAG} ${IMAGE_NAME}:${MAJOR_TAG}

## Testing
test-clean:
	docker run --rm \
		-v ${DIR}/.whisper:/app/.whisper \
		-v ${DIR}/examples:/data \
		${IMAGE_TAG} \
		clean -i /data/curious-george.mp4 -m tiny.en -l en

## Targets Used for Development
whisper:
	docker run -it --rm \
		-v ${DIR}:/app \
		-v ${DIR}/.whisper:/root/.cache/whisper \
		${IMAGE_TAG} \
		whisper ${VIDEO_FILE} \
			--model ${MODEL} \
			--language ${LANG} \
			--output_format json \
			--output_dir data

bash:
	docker run -it --rm \
		-v ${DIR}/examples:/data \
		${IMAGE_TAG} /bin/bash
