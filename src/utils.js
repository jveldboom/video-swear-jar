const fs = require('fs')
const path = require('path')
const swearJar = require('./swear-jar')


const getFilePaths = (inputFile) => {
  const paths = path.parse(inputFile)
  return {
    transcript: `${paths.dir}/${paths.name}.json`,
    cut: `${paths.dir}/${paths.base}-cut.txt`,
    cutVideo: paths.base, // location in cut file - ffmpeg requires video to be in same dir as cut file
    cutWords: `${paths.dir}/${paths.name}-cut-words.txt`
  }
}

const removeBuildFiles = (files) => {
  for (const file of files) {
    try {
      fs.rmSync(file, { force: true });
    } catch (error) {
      if (error.code !== 'ENOENT') {
        throw error;
      }
    }
  }
}

const getTranscript = (filepath) => {
  let transcript = fs.readFileSync(filepath, 'utf8')
  transcript = fixTranscript(transcript)
  return JSON.parse(transcript)

}

// whisper's transcript occasionally contains invalid JSON such as `NaN` values
// below removes those -- may need to expand if there are other use-cases besides "NaN"
const fixTranscript = (transcript) => {
  return transcript.replace(/NaN/g, 'null')
}

const containsSwearWords = (text) => {
  const pattern = swearJar.join('|');
  const regex = new RegExp(`\\b(?:${pattern})\\b`, 'i'); // 'i' flag for case-insensitive matching
  return regex.test(text);
}

module.exports = {
  getFilePaths,
  removeBuildFiles,
  getTranscript,
  fixTranscript,
  containsSwearWords
}