const fs = require('fs')
const swearWords = require('./swear-words.json')
const utils = require('./utils')

const transcribe = async ({ inputFile, model = 'tiny.en', language = 'en', outputDir = '.' }) => {
  const args = [
    inputFile,
    '--model', model,
    '--model_dir', '/app/.whisper',
    '--language', language,
    '--output_format', 'json',
    '--output_dir', outputDir,
    '--fp16', 'False' // TODO: make CLI argument to use GPU
  ]
  await utils.asyncSpawn('whisper', args)
}

const cut = async ({ cutFile, outputFile }) => {
  const args = [
    '-loglevel', 'panic',
    '-f', 'concat',
    '-i', cutFile,
    '-c', 'copy',
    outputFile
  ]
  await utils.asyncSpawn('ffmpeg', args)
}

// get and format transcript in known format
const getTranscript = (filepath) => {
  let transcript = fs.readFileSync(filepath, 'utf8')

  // whisper's transcript occasionally contains invalid JSON such as `NaN` values
  // below removes those -- may need to expand if there are other use-cases besides "NaN"
  transcript = transcript.replace(/NaN/g, 'null')
  return JSON.parse(transcript).segments
}

const getTranscriptSwearWords = (filepath) => {
  const transcript = getTranscript(filepath)
  return transcript.filter(value => {
    return containsSwearWords(value.text)
  })
}

const containsSwearWords = (text) => {
  const pattern = swearWords.join('|')
  const regex = new RegExp(`\\b(?:${pattern})\\b`, 'i') // 'i' flag for case-insensitive matching
  return regex.test(text)
}

const createCutFile = ({ transcript, paths }) => {
  const ffmpegCuts = []
  const cutWords = []
  let inpoint = 0

  for (const segment of transcript) {
    const start = segment.start
    const end = segment.end

    ffmpegCuts.push(`file '${paths.cutVideo}'`)
    ffmpegCuts.push(`inpoint ${inpoint}`)
    ffmpegCuts.push(`outpoint ${start}`)

    inpoint = end
    if (paths.cutWords) cutWords.push(`${start}-${inpoint}\t${segment.text.trim()}`)
  }

  // write ending inpoint to bring in remaining video
  ffmpegCuts.push(`file '${paths.cutVideo}'`)
  ffmpegCuts.push(`inpoint ${inpoint}`)

  fs.writeFileSync(paths.cut, ffmpegCuts.join('\n'))
  if (paths.cutWords) fs.writeFileSync(paths.cutWords, cutWords.join('\n'))
}

module.exports = {
  transcribe,
  cut,
  getTranscript,
  getTranscriptSwearWords,
  containsSwearWords,
  createCutFile
}
