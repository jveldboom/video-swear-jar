const utils = require('./utils')
const video = require('./video')

const paths = utils.getFilePaths(process.env.VIDEO_FILE)

const run = async () => {
  try {
    const { model, language } = process.env
    await video.transcribe({ inputFile: paths.inputFile, model, language })
  } catch (err) {
    console.error(`Unable to transcribe ${paths.inputFile}`, err)
    throw err
  }

  // TODO: validate expected files exist before continuing
  const transcript = video.getTranscriptSwearWords(paths.transcript)
  if (transcript.length === 0) {
    console.log(`No swear words found in ${paths.inputFile} - nothing else to do`)
    return
  }

  try {
    video.createCutFile({ transcript, paths })
  } catch (err) {
    console.error(`Unable to create video cut file ${paths.cutVideo}`, err)
    throw err
  }

  try {
    await video.cut({ cutFile: paths.cut, outputFile: paths.outputVideo })
  } catch (err) {
    console.error(`Unable to cut video ${paths.inputFile}`, err)
    throw err
  }
}

run()
