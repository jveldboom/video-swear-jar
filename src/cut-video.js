#!/usr/bin/env node
const yargs = require('yargs')
const fs = require('fs')
const log = require('./log')
const utils = require('./utils')
const video = require('./video')

const argv = yargs.usage('cut-video')
  .options({
    timestamps: {
      description: 'Timestamps file',
      demandOption: true,
      alias: 't'
    },
    video: {
      description: 'Video file to cut',
      demandOption: true,
      alias: 'v'
    },
    'cut-video': {
      description: 'Boolean to cut video',
      boolean: true,
      default: true,
      alias: 'c'
    }
  }).argv

const paths = utils.getFilePaths(argv.video)

const run = async () => {
  if (!fs.existsSync(argv.timestamps)) {
    log.error(`The timestamps file ("${argv.timestamps}") does not exist`)
    return
  }

  if (!fs.existsSync(argv.video)) {
    log.error(`The video file ("${argv.video}") does not exist`)
    return
  }

  const content = fs.readFileSync(argv.timestamps).toString()

  const cutList = []

  for (const line of content.split('\n')) {
    const times = line.split('-')
    if (times.length !== 2) {
      log.warn(`Warning: skipping invalid line found: ${line}`)
      continue
    }

    const start = times[0].trim().split(':')
    const end = times[1].trim().split(':')

    if (start.length !== 3 || end.length !== 3) {
      log.warn(`Warning: skipping invalid time found on line: ${line}`)
      continue
    }

    cutList.push({
      start: (+start[0]) * 60 * 60 + (+start[1]) * 60 + (+start[2]),
      end: (+end[0]) * 60 * 60 + (+end[1]) * 60 + (+end[2])
    })
  }

  video.createCutFile({
    transcript: cutList,
    paths: {
      cutVideo: paths.cutVideo,
      cut: paths.cut
    }
  })

  try {
    log.info('Cutting video and saving new video...')
    await video.cut({ cutFile: paths.cut, outputFile: paths.outputVideo })
  } catch (err) {
    log.error(`Unable to cut video "${paths.inputFile}"`, err)
    throw err
  }

  log.success(`Video successfully cut ${paths.outputVideo}`)
}

run()
