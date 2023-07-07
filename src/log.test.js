/* eslint-env jest */
const chalk = require('chalk')
const log = require('./log')

jest.spyOn(console, 'log').mockImplementation()

describe('log', () => {
  beforeEach(() => {

  })

  afterEach(() => {
    jest.resetAllMocks()
    delete process.env.DEBUG
  })

  const levels = [
    { level: 'error', color: 'red' },
    { level: 'success', color: 'green' },
    { level: 'warn', color: 'yellow' },
    { level: 'info', color: 'cyan' },
    { level: 'notice', color: 'white' }
  ]

  for (const test of levels) {
    describe(`${test.level}()`, () => {
      it(`should output ${test.level} message`, () => {
        log[test.level]('test')
        expect(console.log).toBeCalledWith(chalk[test.color]('test'), '')
      })
      it(`should output ${test.level} with optional message`, () => {
        log[test.level]('test', { msg: 'testing' })
        expect(console.log).toBeCalledWith(chalk[test.color]('test'), { msg: 'testing' })
      })
    })
  }

  // separate test since it uses an env variable
  describe('debug()', () => {
    it('should not output debug message', () => {
      log.debug('test')
      expect(console.log).toBeCalledTimes(0)
    })
    it('should not output debug with optional message', () => {
      log.debug('test', { msg: 'testing' })
      expect(console.log).toBeCalledTimes(0)
    })

    it('should output debug message', () => {
      process.env.DEBUG = true
      log.debug('test')
      expect(console.log).toBeCalledWith('[DEBUG] test', '')
    })
    it('should output debug with optional message', () => {
      process.env.DEBUG = true
      log.debug('test', { msg: 'testing' })
      expect(console.log).toBeCalledWith('[DEBUG] test', { msg: 'testing' })
    })
  })
})
