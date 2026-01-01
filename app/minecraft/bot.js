const mineflayer = require('mineflayer')
const readline = require('readline')
const { pathfinder, Movements, goals } = require('mineflayer-pathfinder')
const { GoalNear, GoalBlock, GoalFollow } = goals

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
})

let bot = null

function log(type, data) {
  console.log(JSON.stringify({ type, data }))
}

function processNaturalLanguageCommand(username, message, isVoice = false) {
    if (!bot) return

    // Normalize message: lowercase and remove punctuation
    const lowerMsg = message.toLowerCase().replace(/[^\w\s]/gi, '').trim()
    const target = bot.players[username] ? bot.players[username].entity : null
    
    // Check if message is directed at bot (contains "yazuki" or is a direct command)
    // If it comes from voice (IPC), it is always directed at the bot.
    const isDirected = isVoice || lowerMsg.includes('yazuki') || lowerMsg.includes('hey bot')
    
    // Helper to check for command phrases
    const hasPhrase = (phrases) => phrases.some(p => lowerMsg.includes(p))

    if (hasPhrase(['come here', 'come to me', 'come over'])) {
      if (!target) {
        bot.chat("I can't see you!")
        return
      }
      const p = target.position
      bot.pathfinder.setMovements(new Movements(bot))
      bot.pathfinder.setGoal(new GoalNear(p.x, p.y, p.z, 1))
      bot.chat("Coming!")
    }
    else if (hasPhrase(['stop', 'stay here', 'wait here']) && (isDirected || lowerMsg === 'stop')) {
      bot.pathfinder.setGoal(null)
      bot.chat("Stopped.")
    }
    else if (hasPhrase(['follow me', 'follow', 'come with me']) && (isDirected || lowerMsg === 'follow me')) {
      if (!target) {
        bot.chat("I can't see you!")
        return
      }
      bot.pathfinder.setMovements(new Movements(bot))
      bot.pathfinder.setGoal(new GoalFollow(target, 1), true)
      bot.chat("Following you!")
    }
    else if (lowerMsg.startsWith('goto ')) {
      const args = message.split(' ')
      if (args.length === 4) {
          const x = parseInt(args[1])
          const y = parseInt(args[2])
          const z = parseInt(args[3])
          
          if (!isNaN(x) && !isNaN(y) && !isNaN(z)) {
              bot.pathfinder.setMovements(new Movements(bot))
              bot.pathfinder.setGoal(new GoalBlock(x, y, z))
              bot.chat(`Going to ${x} ${y} ${z}`)
          }
      }
    }
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

    bot.loadPlugin(pathfinder)

    let hasSpawned = false
    bot.on('spawn', () => {
      log('status', 'Spawned')
      
      if (!hasSpawned) {
        hasSpawned = true
        log('info', 'Bot has spawned in the world.')
        
        // Apply skin if configured
        if (options.skin) {
            setTimeout(() => {
                log('info', `Applying skin: ${options.skin}`)
                if (options.skin.startsWith('http')) {
                    // URL skin (SkinRestorer format: /skin set web slim "URL" Name)
                    bot.chat(`/skin set web slim "${options.skin}" ${bot.username}`)
                }
            }, 2000) // Wait 2 seconds to ensure server is ready
        }
      }
    })

    bot.on('chat', (username, message) => {
      if (username === bot.username) return
      log('chat', { username, message })
      processNaturalLanguageCommand(username, message)
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
    } else if (msg.command === 'follow') {
        if (bot) {
            const target = bot.players[msg.username] ? bot.players[msg.username].entity : null
            if (target) {
                bot.pathfinder.setMovements(new Movements(bot))
                bot.pathfinder.setGoal(new GoalFollow(target, 1), true)
                bot.chat(`Following ${msg.username}`)
            } else {
                log('info', `Cannot follow ${msg.username}: Player not found/visible`)
            }
        }
    } else if (msg.command === 'stop') {
        if (bot) {
            bot.pathfinder.setGoal(null)
            bot.chat("Stopped moving.")
        }
    } else if (msg.command === 'come') {
        if (bot) {
            const target = bot.players[msg.username] ? bot.players[msg.username].entity : null
            if (target) {
                const p = target.position
                bot.pathfinder.setMovements(new Movements(bot))
                bot.pathfinder.setGoal(new GoalNear(p.x, p.y, p.z, 1))
                bot.chat(`Coming to ${msg.username}`)
            }
        }
    } else if (msg.command === 'voice') {
        if (bot) {
            processNaturalLanguageCommand(msg.username, msg.text, true)
        }
    }
  } catch (e) {
    // Ignore invalid JSON
  }
})

log('status', 'Ready')
