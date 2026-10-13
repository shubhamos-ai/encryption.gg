/**
 * Minecraft Bot API
 * Defines routes and functions for controlling the Minecraft bot
 */

const express = require('express');
const router = express.Router();

// Bot actions map
const botActions = {
  // Movement controls
  '/forward': (bot) => {
    bot.setControlState('forward', true);
    setTimeout(() => bot.setControlState('forward', false), 1000);
    return 'Moving forward';
  },
  '/back': (bot) => {
    bot.setControlState('back', true);
    setTimeout(() => bot.setControlState('back', false), 1000);
    return 'Moving backward';
  },
  '/left': (bot) => {
    bot.setControlState('left', true);
    setTimeout(() => bot.setControlState('left', false), 1000);
    return 'Moving left';
  },
  '/right': (bot) => {
    bot.setControlState('right', true);
    setTimeout(() => bot.setControlState('right', false), 1000);
    return 'Moving right';
  },
  '/jump': (bot) => {
    bot.setControlState('jump', true);
    setTimeout(() => bot.setControlState('jump', false), 500);
    return 'Jumping';
  },
  '/attack': (bot) => {
    // Look at entity in front of bot and attack
    const entity = bot.nearestEntity();
    if (entity) {
      bot.lookAt(entity.position);
      bot.attack(entity);
      return `Attacking ${entity.name || 'entity'}`;
    }
    // Just swing arm if no entity found
    bot.swingArm();
    return 'Attacking';
  },
  '/use': (bot) => {
    // Use item in hand or block in front
    bot.activateItem();
    return 'Using item/block';
  },
  '/sneak': (bot) => {
    // Toggle sneaking
    const isSneaking = bot.getControlState('sneak');
    bot.setControlState('sneak', !isSneaking);
    return isSneaking ? 'Stopped sneaking' : 'Started sneaking';
  },
  '/sprint': (bot) => {
    // Toggle sprinting
    const isSprinting = bot.getControlState('sprint');
    bot.setControlState('sprint', !isSprinting);
    return isSprinting ? 'Stopped sprinting' : 'Started sprinting';
  },
  '/login': (bot) => {
    // Perform login
    bot.chat('/login RCL9JLVL');
    return 'Logging in...';
  },
  '/stop': (bot) => {
    // Stop all movement
    bot.clearControlStates();
    return 'Stopped all movement';
  },
  '/look': (bot, args) => {
    // Look in a specific direction or at coordinates
    if (args && args.length >= 2) {
      const yaw = parseFloat(args[0]);
      const pitch = parseFloat(args[1]);
      if (!isNaN(yaw) && !isNaN(pitch)) {
        bot.look(yaw, pitch);
        return `Looking with yaw: ${yaw}, pitch: ${pitch}`;
      }
    }
    return 'Invalid look parameters';
  }
};

// Get bot instance helper
function getBotInstance() {
  const bot = global.minecraftBot;
  if (!bot) {
    throw new Error('Bot is not connected');
  }
  return bot;
}

// Helper to process special commands starting with '/'
function processSpecialCommand(command) {
  // Check if it's a special command
  if (command.startsWith('/')) {
    const parts = command.split(' ');
    const actionName = parts[0].toLowerCase();
    const args = parts.slice(1);
    
    const action = botActions[actionName];
    if (action) {
      try {
        const bot = getBotInstance();
        const result = action(bot, args);
        return {
          success: true,
          processed: true,
          message: result
        };
      } catch (err) {
        return {
          success: false,
          processed: true,
          message: err.message
        };
      }
    }
  }
  
  // Not a special command or not recognized
  return {
    success: true,
    processed: false
  };
}

// Routes

// Execute a command
router.post('/command', (req, res) => {
  const { command } = req.body;
  
  if (!command) {
    return res.status(400).json({ success: false, message: 'Command is required' });
  }
  
  try {
    // First check if it's a special command
    const specialResult = processSpecialCommand(command);
    
    if (specialResult.processed) {
      return res.json({
        success: specialResult.success,
        message: specialResult.message
      });
    }
    
    // If not special, send as regular chat message
    const bot = getBotInstance();
    bot.chat(command);
    
    return res.json({
      success: true,
      message: 'Command sent'
    });
  } catch (err) {
    console.error('[Bot API] Error executing command:', err);
    return res.status(500).json({
      success: false,
      message: err.message
    });
  }
});

// Get bot status and data
router.get('/status', (req, res) => {
  try {
    const bot = getBotInstance();
    
    // Build status object with bot data
    const status = {
      connected: !!bot.entity,
      username: bot.username,
      health: bot.health || 0,
      food: bot.food || 0,
      position: bot.entity ? {
        x: Math.round(bot.entity.position.x * 100) / 100,
        y: Math.round(bot.entity.position.y * 100) / 100,
        z: Math.round(bot.entity.position.z * 100) / 100
      } : null,
      yaw: bot.entity ? bot.entity.yaw : null,
      pitch: bot.entity ? bot.entity.pitch : null,
      onGround: bot.entity ? bot.entity.onGround : null
    };
    
    return res.json({
      success: true,
      status
    });
  } catch (err) {
    console.error('[Bot API] Error getting bot status:', err);
    return res.status(500).json({
      success: false,
      message: err.message
    });
  }
});

// Get nearby players
router.get('/players', (req, res) => {
  try {
    const bot = getBotInstance();
    
    const players = Object.values(bot.players)
      .filter(player => player.entity && player.username !== bot.username)
      .map(player => ({
        username: player.username,
        position: player.entity ? {
          x: Math.round(player.entity.position.x * 100) / 100,
          y: Math.round(player.entity.position.y * 100) / 100,
          z: Math.round(player.entity.position.z * 100) / 100
        } : null,
        distance: player.entity ? 
          Math.round(Math.sqrt(
            Math.pow(player.entity.position.x - bot.entity.position.x, 2) +
            Math.pow(player.entity.position.y - bot.entity.position.y, 2) +
            Math.pow(player.entity.position.z - bot.entity.position.z, 2)
          ) * 10) / 10 : null
      }));
    
    return res.json({
      success: true,
      players
    });
  } catch (err) {
    console.error('[Bot API] Error getting nearby players:', err);
    return res.status(500).json({
      success: false,
      message: err.message
    });
  }
});

// Get inventory
router.get('/inventory', (req, res) => {
  try {
    const bot = getBotInstance();
    
    const inventory = bot.inventory.slots
      .filter(item => item !== null)
      .map(item => ({
        name: item.name,
        displayName: item.displayName,
        count: item.count,
        slot: item.slot,
        type: item.type
      }));
    
    return res.json({
      success: true,
      inventory
    });
  } catch (err) {
    console.error('[Bot API] Error getting inventory:', err);
    return res.status(500).json({
      success: false,
      message: err.message
    });
  }
});

// Export the router and utility functions
module.exports = {
    router,
    processSpecialCommand,
    getBotInstance
};