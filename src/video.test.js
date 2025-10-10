/* eslint-env jest */
const utils = require('./utils')
const fs = require('fs')

const video = require('./video')

jest.spyOn(utils, 'asyncSpawn')
jest.spyOn(fs, 'writeFileSync')

describe('video', () => {
  afterEach(() => {
    jest.resetAllMocks()
  })

  describe('transcribe()', () => {
    it('should attempt to transcribe video with minimal inputs', () => {
      utils.asyncSpawn.mockImplementation()
      video.transcribe({ inputFile: 'test.mp4' })
      expect(utils.asyncSpawn).toBeCalledWith('whisper-ctranslate2', [
        'test.mp4',
        '--model', 'tiny.en',
        '--model_dir', '/app/.whisper',
        '--language', 'en',
        '--output_format', 'json',
        '--output_dir', '.',
        '--compute_type', 'int8'
      ])
    })

    it('should attempt to transcribe video with all inputs', () => {
      utils.asyncSpawn.mockImplementation()
      video.transcribe({
        engine: 'whisper',
        inputFile: 'test.mp4',
        model: 'small.en',
        language: 'es',
        outputDir: '/foo'
      })
      expect(utils.asyncSpawn).toBeCalledWith('whisper', [
        'test.mp4',
        '--model', 'small.en',
        '--model_dir', '/app/.whisper',
        '--language', 'es',
        '--output_format', 'json',
        '--output_dir', '/foo',
        '--fp16', 'False'
      ])
    })
  })

  describe('cut()', () => {
    it('should attempt to cut video', () => {
      utils.asyncSpawn.mockImplementation()
      video.cut({ cutFile: 'timestamps.txt', outputFile: 'output.mp4' })
      expect(utils.asyncSpawn).toBeCalledWith('ffmpeg', [
        '-loglevel', 'error',
        '-f', 'concat',
        '-safe', '0',
        '-i', 'timestamps.txt',
        '-c', 'copy',
        'output.mp4'
      ])
    })
  })

  describe('createCutFile()', () => {
    it('should attempt to create ffmpeg cut file', () => {
      const transcript = [
        { start: 0.0, end: 2.0, text: 'Foo' },
        { start: 10.0, end: 20.0, text: 'Bar' }
      ]

      const cutFileExpected = `file '/foo/cut-words.txt'
inpoint 0
outpoint 0
file '/foo/cut-words.txt'
inpoint 2
outpoint 10
file '/foo/cut-words.txt'
inpoint 20`
      fs.writeFileSync.mockImplementation()
      video.createCutFile({
        transcript,
        paths: {
          cutVideo: '/foo/cut-words.txt',
          cutWords: 'cut-words.txt',
          cut: 'cut-file.txt'
        }
      })
      expect(fs.writeFileSync).toHaveBeenNthCalledWith(1, 'cut-file.txt', cutFileExpected)
      expect(fs.writeFileSync).toBeCalledTimes(2)
    })

    it('should not save cut words file', () => {
      const transcript = [
        { start: 0.0, end: 2.0, text: 'Foo' }
      ]

      fs.writeFileSync.mockImplementation()
      video.createCutFile({
        transcript,
        paths: {
          cutVideo: '/foo/cut-words.txt',
          cut: 'cut-file.txt'
        }
      })
      expect(fs.writeFileSync).toBeCalledTimes(1)
    })
  })

  describe('formatTime()', () => {
    it('should return formatting time', () => {
      const time = video.formatTime(12010)
      expect(time).toBe('03:20:10')
    })
  })
})
