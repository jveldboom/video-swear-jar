# Whisper CLI Reference

https://github.com/openai/whisper

| Option | Description  | Default | Valid Values |
| ------ |------------- | ------- | ------------ |
| -h, --help| Show this help message and exit  | - | - |
| --model | Name of the Whisper model to use                                                                   | small             | tiny.en, tiny, base.en, base, small.en, small, medium.en, medium, large-v1, large-v2, large |
| --model_dir MODEL_DIR                 | The path to save model files; uses `~/.cache/whisper` by default                                   | None              | -                                               |
| --device DEVICE                       | Device to use for PyTorch inference                                                                | cpu               | cpu, gpu                                        |
| --output_dir OUTPUT_DIR, -o OUTPUT_DIR | Directory to save the outputs                                                                       | .                 | -                                               |
| --output_format ,-f | Format of the output file; if not specified, all available formats will be produced               | all               | txt, vtt, srt, tsv, json, all                     |
| --verbose                             | Whether to print out the progress and debug messages                                               | True              | True, False                                     |
| --task         | Whether to perform X->X speech recognition ('transcribe') or X->English translation ('translate')  | transcribe        | transcribe, translate                           |
| --language                           | Language spoken in the audio, specify None to perform language detection                           | None              | af, am, ar, as, az, ... (full list of languages) |
| --temperature                         | Temperature to use for sampling                                                                    | 0                 | -                                               |
| --best_of                             | Number of candidates when sampling with non-zero temperature                                       | 5                 | -                                               |
| --beam_size                           | Number of beams in beam search, only applicable when temperature is zero                          | 5                 | -                                               |
| --patience                            | Optional patience value to use in beam decoding                                                     | None              | -                                               |
| --length_penalty                      | Optional token length penalty coefficient                                                          | None              | -                                               |
| --suppress_tokens                     | Comma-separated list of token ids to suppress during sampling                                      | -1                | -                                               |
| --initial_prompt                      | Optional text to provide as a prompt for the first window                                          | None              | -                                               |
| --condition_on_previous_text          | Whether to use the previous output as a prompt for the next window                                 | True              | True, False                                     |
| --fp16                                | Whether to perform inference in fp16                                                               | True              | True, False                                     |
| --temperature_increment_on_fallback  | Temperature to increase when falling back                                                          | 0.2               | -                                               |
| --compression_ratio_threshold         | Threshold for treating the decoding as failed based on gzip compression ratio                      | 2.4               | -                                               |
| --logprob_threshold                   | Threshold for treating the decoding as failed based on average log probability                     | -1.0              | -                                               |
| --no_speech_threshold                 | Threshold for treating the segment as silence                                                      | 0.6               | -                                               |
| --word_timestamps                     | Whether to extract word-level timestamps and refine the results based on them                     | False             | True, False                                     |
|

Argument Notes:
- `--word_timestamps` creates a timestamps for each word. For example, `--output_format` json will include a "words" key in each segment containing a list of the individual words and their timestamps for that segment.