const mineflayer = require('mineflayer')
const readline = require('readline')

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
})

let bot = null

function log(type, data) {
  console.log(JSON.stringify({ type, data }))
}

function createBot(options) {
  if (bot) {
    try {
        bot.quit()
    } catch (e) {}
  }

  try {
    log('info', `Connecting to ${options.host}:${options.port} as ${options.username}...`)
    
    bot = mineflayer.createBot({
      host: options.host,
      port: parseInt(options.port),
      username: options.username,
      auth: options.auth || 'offline',
      version: options.version === 'auto' ? false : options.version
    })

    bot.on('spawn', () => {
      log('status', 'Spawned')
      log('info', 'Bot has spawned in the world.')
    })

    bot.on('chat', (username, message) => {
      if (username === bot.username) return
      log('chat', { username, message })
    })

    bot.on('error', (err) => {
      log('error', err.message)
    })

    bot.on('end', () => {
      log('status', 'Disconnected')
    })
    
    bot.on('kicked', (reason) => {
        log('error', 'Kicked: ' + reason)
    })

  } catch (err) {
    log('error', err.message)
  }
}

rl.on('line', (line) => {
  try {
    const msg = JSON.parse(line)
    
    if (msg.command === 'connect') {
      createBot(msg.options)
    } else if (msg.command === 'chat') {
      if (bot) bot.chat(msg.message)
    } else if (msg.command === 'quit') {
      if (bot) bot.quit()
    }
  } catch (e) {
    // Ignore invalid JSON
  }
})

log('status', 'Ready')
