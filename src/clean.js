#!/usr/bin/env node
const yargs = require('yargs')
const log = require('./log')
const utils = require('./utils')
const video = require('./video')

const argv = yargs.usage('clean-fast')
  .options({
    input: {
      description: 'Input video filename',
      demandOption: true,
      alias: 'i'
    },
    engine: {
      description: 'Transcription engine',
      alias: 'e',
      default: 'whisper-ctranslate2',
      choices: ['whisper', 'whisper-ctranslate2']
    },
    model: {
      description: 'Whisper model name',
      alias: 'm',
      default: 'tiny.en',
      choices: ['tiny.en', 'tiny', 'base.en', 'base', 'small.en', 'small', 'medium.en', 'medium', 'large-v1', 'large-v2', 'large']
    },
    language: {
      description: 'Video file language',
      alias: 'l',
      default: 'en'
    },
    'output-dir': {
      description: 'Output directory to save cleaned video',
      alias: 'o',
      default: '.'
    },
    debug: {
      description: 'Run in debug mode for verbose output',
      default: false,
      type: 'boolean'
    }
  }).argv

process.env.DEBUG = argv.debug
const paths = utils.getFilePaths(argv.input)

const run = async () => {
  try {
    log.info('[1 of 4] Starting video transcribe...')
    const { model, language } = argv
    await video.transcribe({ engine: argv.engine, inputFile: paths.inputFile, model, language, outputDir: argv['output-dir'] })
  } catch (err) {
    log.error(`Unable to transcribe ${paths.inputFile}`, err)
    throw err
  }

  // TODO: validate expected files exist before continuing
  log.info('[2 of 4] Checking transcript for swear words...')
  const transcript = video.getTranscriptSwearWords(paths.transcript)
  if (transcript.length === 0) {
    log.success(`No swear words found in ${paths.inputFile} - nothing else to do`)
    return
  }

  try {
    log.info('[3 of 4] Creating video cut list...')
    video.createCutFile({ transcript, paths })
  } catch (err) {
    log.error(`Unable to create video cut file ${paths.cutVideo}`, err)
    throw err
  }

  try {
    log.info('[4 of 4] Cutting video and saving new video...')
    await video.cut({ cutFile: paths.cut, outputFile: paths.outputVideo })
  } catch (err) {
    log.error(`Unable to cut video ${paths.inputFile}`, err)
    throw err
  }

  log.success('Video successfully cleaned!')
  log.notice(`
  Outputs:
    Clean video: ${paths.outputVideo}
    Words Cut from Video: ${paths.cutWords}
  `)
}

run()
