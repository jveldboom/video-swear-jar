/* eslint-env jest */
const utils = require('./utils')

jest.spyOn(console, 'log').mockImplementation()

describe('utils', () => {
  afterEach(() => {
    jest.resetAllMocks()
  })

  describe('getFilePaths()', () => {
    it('should return object of file paths', () => {
      const paths = utils.getFilePaths('/foo/bar.mp4')
      expect(paths).toEqual({
        cut: 'bar-cut.txt',
        cutVideo: 'bar.mp4',
        cutWords: 'bar-cut-words.txt',
        inputFile: '/foo/bar.mp4',
        outputVideo: 'bar-output.mp4',
        transcript: 'bar.json'
      })
    })
  })

  describe('asyncSpawn()', () => {
    it('should return stdout', async () => {
      const res = await utils.asyncSpawn('printf', ['test'])
      expect(res).toEqual({
        stderr: '',
        stdout: 'test'
      })
    })

    it('should handle command error', async () => {
      try {
        await utils.asyncSpawn('ls', ['-z'])
      } catch (err) {
        // error code differs on mac (1) & linux (2)
        expect(err.message).toMatch(/^Command "ls -z" exited with code/)
        expect(err.code).toBeGreaterThan(0)
        expect(err.stderr.length).toBeGreaterThan(10)
      }
    })

    it('should handle invalid command error', async () => {
      try {
        await utils.asyncSpawn('invalid-command')
      } catch (err) {
        expect(err.message).toEqual('spawn invalid-command ENOENT')
      }
    })
  })
})
