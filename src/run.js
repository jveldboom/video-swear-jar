const fs = require('fs')
const utils = require('./utils')

const paths = utils.getFilePaths(process.env.VIDEO_FILE)
// TODO: validate expected files exist before continuing
const transcript = utils.getTranscript(paths.transcript)

const ffmpegCuts = []
const cutWords = []
let inpoint = 0

for (const segment of transcript.segments) {
  if (utils.containsSwearWords(segment.text)) {
    const start = segment.start
    const end = segment.end

    ffmpegCuts.push(`file '${paths.cutVideo}'`)
    ffmpegCuts.push(`inpoint ${inpoint}`)
    ffmpegCuts.push(`outpoint ${start}`)

    inpoint = end
    cutWords.push(segment.text)
  }
}

// write ending inpoint to bring in remaining video
ffmpegCuts.push(`file '${paths.cutVideo}'`)
ffmpegCuts.push(`inpoint ${inpoint}`)

fs.writeFileSync(paths.cut, ffmpegCuts.join(`\n`))
fs.writeFileSync(paths.cutWords, cutWords.join(`\n`))
