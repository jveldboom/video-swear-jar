#!/usr/bin/env node
const yargs = require('yargs')
const chalk = require('chalk')
const utils = require('./utils')
const video = require('./video')

const argv = yargs.usage('clean')
  .options({
    input: {
      description: 'Input video filename',
      demandOption: true,
      alias: 'i'
    },
    model: {
      description: 'Whisper model name',
      alias: 'm',
      default: 'tiny.en',
      choices: ['tiny.en', 'tiny', 'base.en', 'base', 'small.en', 'small']
    },
    language: {
      description: 'Video file language',
      alias: 'l',
      default: 'en'
    },
    'output-dir': {
      description: 'Output directory to save cleaned video',
      alias: 'o'
    }
  }).argv

const paths = utils.getFilePaths(argv.input)

const run = async () => {
  try {
    console.log(chalk.cyan('[1 of 4] Starting video transcribe...'))
    const { model, language } = argv
    await video.transcribe({ inputFile: paths.inputFile, model, language, outputDir: argv.outputDir })
  } catch (err) {
    console.error(chalk.red(`Unable to transcribe ${paths.inputFile}`), err)
    throw err
  }

  // TODO: validate expected files exist before continuing
  console.log(chalk.cyan('[2 of 4] Checking transcript for swear words...'))
  const transcript = video.getTranscriptSwearWords(paths.transcript)
  if (transcript.length === 0) {
    console.log(chalk.green(`No swear words found in ${paths.inputFile} - nothing else to do`))
    return
  }

  try {
    console.log(chalk.cyan('[3 of 4] Creating video cut list...'))
    video.createCutFile({ transcript, paths })
  } catch (err) {
    console.error(chalk.red(`Unable to create video cut file ${paths.cutVideo}`), err)
    throw err
  }

  try {
    console.log(chalk.cyan('[4 of 4] Cutting video and saving new video...'))
    await video.cut({ cutFile: paths.cut, outputFile: paths.outputVideo })
  } catch (err) {
    console.error(chalk.red(`Unable to cut video ${paths.inputFile}`), err)
    throw err
  }

  console.log(chalk.green('Video successfully cleaned!'))
  console.log(`
  Outputs:
    Clean video: ${paths.outputVideo}
    Words Cut from Video: ${paths.cutWords}
  `)
}

run()
