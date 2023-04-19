# Whisper CLI Reference

https://github.com/openai/whisper

```
whisper [-h]
    [--model {tiny.en,tiny,base.en,base,small.en,small,medium.en,medium,large-v1,large-v2,large}]
    [--model_dir MODEL_DIR]
    [--device DEVICE]
    [--output_dir OUTPUT_DIR]
    [--output_format {txt,vtt,srt,tsv,json,all}]
    [--verbose VERBOSE] [--task {transcribe,translate}]
    [--language {af,am,ar,as,az,ba,be,bg,bn,bo,br,bs,ca,cs,cy,da,de,el,en,es,...}]
    [--temperature TEMPERATURE]
    [--best_of BEST_OF]
    [--beam_size BEAM_SIZE]
    [--patience PATIENCE]
    [--length_penalty LENGTH_PENALTY]
    [--suppress_tokens SUPPRESS_TOKENS]
    [--initial_prompt INITIAL_PROMPT]
    [--condition_on_previous_text CONDITION_ON_PREVIOUS_TEXT]
    [--fp16 FP16]
    [--temperature_increment_on_fallback TEMPERATURE_INCREMENT_ON_FALLBACK]
    [--compression_ratio_threshold COMPRESSION_RATIO_THRESHOLD]
    [--logprob_threshold LOGPROB_THRESHOLD]
    [--no_speech_threshold NO_SPEECH_THRESHOLD]
    [--word_timestamps WORD_TIMESTAMPS]
    [--prepend_punctuations PREPEND_PUNCTUATIONS]
    [--append_punctuations APPEND_PUNCTUATIONS]
    [--threads THREADS]
    audio [audio ...]
```