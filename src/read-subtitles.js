#!/usr/bin/env node
const yargs = require('yargs')
const fs = require('fs')
const log = require('./log')
const video = require('./video')

const argv = yargs.usage('read-subtitles')
  .options({
    subtitles: {
      description: 'Subtitles file',
      demandOption: true,
      type: 'string',
      alias: 's'
    },
    debug: {
      description: 'Run in debug mode for verbose output',
      default: false
    }
  }).check((argv) => {
    if (!fs.existsSync(argv.subtitles)) {
      throw new Error(`Error: the subtitles file "${argv.subtitles}" does not exist`)
    }
    return true
  }).argv

process.env.DEBUG = argv.debug

const run = async () => {
  const content = fs.readFileSync(argv.subtitles).toString()
  const subtitleBlocks = content.split(/\r?\n\r?\n/)

  const swearWords = []

  subtitleBlocks.forEach((subtitleBlock, index) => {
    const lines = subtitleBlock.split(/\r?\n/)

    if (lines.length >= 3) {
      const timestamp = lines[1]
      const textLines = lines.slice(2)

      textLines.forEach((line) => {
        if (video.containsSwearWords(line)) {
          swearWords.push({ timestamp, line })
          log.notice(`${timestamp}\t${line}`)
        }
      })
    }
  })
}

run()
