const fs = require('fs')
const swearWords = require('./swear-words.json')
const utils = require('./utils')

const transcribe = async ({ engine = 'fast-whisper', inputFile, model = 'tiny.en', language = 'en', outputDir = '.' }) => {
  const args = [
    inputFile,
    '--model', model,
    '--model_dir', '/app/.whisper',
    '--language', language,
    '--output_format', 'json',
    '--output_dir', outputDir
  ]

  // engine specific args
  switch (engine) {
    case 'whisper':
      args.push('--fp16', 'False')
      break
    case 'fast-whisper':
      args.push('--compute_type', 'int8')
      break
  }

  await utils.asyncSpawn(engine, args)
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
    const start = Math.floor(segment.start)
    const end = Math.ceil(segment.end)

    ffmpegCuts.push(`file '${paths.cutVideo}'`)
    ffmpegCuts.push(`inpoint ${inpoint}`)
    ffmpegCuts.push(`outpoint ${start}`)

    inpoint = end
    if (paths.cutWords) cutWords.push(`${formatTime(start)} - ${formatTime(inpoint)}\t${segment.text.trim()}`)
  }

  // write ending inpoint to bring in remaining video
  ffmpegCuts.push(`file '${paths.cutVideo}'`)
  ffmpegCuts.push(`inpoint ${inpoint}`)

  fs.writeFileSync(paths.cut, ffmpegCuts.join('\n'))
  if (paths.cutWords) fs.writeFileSync(paths.cutWords, cutWords.join('\n'))
}

const formatTime = (seconds) => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const remainingSeconds = seconds % 60

  const formattedHours = String(hours).padStart(2, '0')
  const formattedMinutes = String(minutes).padStart(2, '0')
  const formattedSeconds = String(remainingSeconds).padStart(2, '0')

  return `${formattedHours}:${formattedMinutes}:${formattedSeconds}`
}

module.exports = {
  transcribe,
  cut,
  getTranscript,
  getTranscriptSwearWords,
  containsSwearWords,
  createCutFile
}
