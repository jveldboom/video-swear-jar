const path = require('path')
const { spawn } = require('child_process')
const log = require('./log')

const getFilePaths = (inputFile) => {
  const paths = path.parse(inputFile)
  const filePaths = {
    inputFile,
    transcript: `${paths.name}.json`, // automatically output by whisper in <video-file>.json
    cut: `${paths.name}-cut.txt`,
    cutVideo: paths.base, // location in cut file - ffmpeg requires video to be in same dir as cut file
    cutWords: `${paths.name}-cut-words.txt`,
    outputVideo: `${paths.name}-output${paths.ext}`
  }

  log.debug(`file paths: ${JSON.stringify(filePaths)}`)
  return filePaths
}

const asyncSpawn = async (command, args = []) => {
  return new Promise((resolve, reject) => {
    log.debug(`running command: ${command} ${args.join(' ')}`)
    const process = spawn(command, args)

    let stdout = ''
    let stderr = ''

    process.stdout.on('data', (data) => {
      console.log(data.toString())
      stdout += data
    })

    process.stderr.on('data', (data) => {
      console.log(data.toString())
      stderr += data
    })

    process.on('close', (code) => {
      if (code === 0) {
        resolve({ stdout, stderr })
      } else {
        const error = new Error(`Command "${command}" exited with code ${code}`)
        error.code = code
        error.stdout = stdout
        error.stderr = stderr
        reject(error)
      }
    })

    process.on('error', (error) => {
      reject(error)
    })
  })
}

module.exports = {
  getFilePaths,
  asyncSpawn
}
