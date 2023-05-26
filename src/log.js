const chalk = require('chalk')

const error = (message, optionalMessage = '') => {
  console.log(chalk.red(message), optionalMessage)
}

const success = (message, optionalMessage = '') => {
  console.log(chalk.green(message), optionalMessage)
}

const warn = (message, optionalMessage = '') => {
  console.log(chalk.yellow(message), optionalMessage)
}

const info = (message, optionalMessage = '') => {
  console.log(chalk.cyan(message), optionalMessage)
}

const debug = (message, optionalMessage = '') => {
  if (process.env.DEBUG === true) console.log(`[DEBUG] ${message}`, optionalMessage)
}

const notice = (message, optionalMessage = '') => {
  console.log(message, optionalMessage)
}

module.exports = {
  error, success, warn, info, debug, notice
}
