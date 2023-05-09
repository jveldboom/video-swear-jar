FROM python:3.9-slim

RUN apt-get update && apt-get install -y curl

# install node.js 18 from nodesource
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash -

# install software
RUN apt-get install -y ffmpeg nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# install python dependencies
RUN pip install -U openai-whisper

# add source files
COPY src /app
WORKDIR /app

# install node dependencies
RUN npm install --omit=dev

# add commands
RUN ln -s /app/clean.js /usr/bin/clean \
    && ln -s /app/cut-video.js /usr/bin/cut-video
