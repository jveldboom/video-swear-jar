# defaults
IMAGE_NAME := jveldboom/video-swear-jar
IMAGE_VERSION := latest
IMAGE_TAG := ${IMAGE_NAME}:${IMAGE_VERSION}
DIR := $(shell pwd)

# Docker
docker-build: # only builds image for current system arch
	docker build -t ${IMAGE_TAG} .

docker-buildx:
	docker buildx create --use
	docker buildx build \
		--platform linux/arm64/v8 \
		-t ${IMAGE_TAG} \
		-t ${IMAGE_NAME}:${MAJOR_VERSION} \
		.

docker-tag:
	docker tag ${IMAGE_TAG} ${IMAGE_NAME}:${MAJOR_VERSION}
	docker tag ${IMAGE_TAG} ${IMAGE_NAME}:latest

docker-push:
	docker push --all-tags ${IMAGE_NAME}

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

node:
	docker run -it --rm \
		-v ${DIR}:/app \
		-v ${DIR}/.whisper:/root/.cache/whisper \
		${IMAGE_TAG} \
		node /app/src/cut-video.js -t test -v test.mp4

bash:
	docker run -it --rm \
		-v ${DIR}:/data \
		${IMAGE_TAG} /bin/bash
