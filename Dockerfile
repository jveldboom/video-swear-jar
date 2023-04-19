FROM python:3.9-slim

# Node.js 18 from NodeSource
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
RUN apt-get update \
    && apt-get install -y ffmpeg nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install -U openai-whisper
WORKDIR /app

# preload models https://github.com/openai/whisper/discussions/63#discussioncomment-5276989
# RUN python -c "import whisper; print(whisper._download(whisper._MODELS['small.en'], '$HOME/.cache/whisper', False))"
