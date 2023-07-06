FROM python:3.9-slim

RUN apt-get update && apt-get install -y curl

# install node.js 18 from nodesource
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash -

# install software
RUN apt-get install -y ffmpeg nodejs=18.* \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# install python dependencies
RUN pip install -U openai-whisper whisper-ctranslate2

# add source files
COPY src /app

# install node dependencies
RUN cd /app && npm install --omit=dev

# add commands to global space
RUN ln -s /app/clean.js /usr/bin/clean \
    && ln -s /app/cut-video.js /usr/bin/cut-video

WORKDIR /data
