const fs = require('fs').promises;
const path = require('path');
const { clearPlayerData } = require('./db-manager');
const { getPlayerVoiceChannel, VOICE_CHANNEL_LABELS } = require('./db-manager');

const DATA_FOLDER = path.join(process.cwd(), 'data');

// Test data for simulation
const players = [
  { 
    discordId: '635399541742632960', 
    minecraftUsername: 'DEVILKINGS_07',
    voiceChannel: '1179321724785922088' 
  },
  { 
    discordId: '987654321098765432', 
    minecraftUsername: 'TestPlayer1',
    voiceChannel: '1182188218716790885' 
  }
];

// Test the player data clearing functionality
async function testClearPlayerData() {
  console.log('\n=== Testing player data clearing functionality ===');
  
  const player = players[1]; // Use test player, not DEVILKINGS_07
  
  try {
    console.log(`Clearing data for player ${player.minecraftUsername} (${player.discordId})...`);
    const result = await clearPlayerData(player.discordId, player.minecraftUsername);
    
    if (result) {
      console.log(`✅ Successfully cleared data for player ${player.minecraftUsername}`);
    } else {
      console.log(`❌ Failed to clear data for player ${player.minecraftUsername}`);
    }
  } catch (err) {
    console.error(`❌ Error clearing player data:`, err);
  }
}

// Test the voice channel label functionality
async function testVoiceChannelLabels() {
  console.log('\n=== Testing voice channel label functionality ===');
  
  try {
    console.log('Voice channel labels map:');
    for (const [channelId, label] of Object.entries(VOICE_CHANNEL_LABELS)) {
      console.log(`${channelId} -> ${label}`);
    }
    
    // Test label formatting
    for (const player of players) {
      const label = VOICE_CHANNEL_LABELS[player.voiceChannel] || player.voiceChannel;
      console.log(`Player ${player.minecraftUsername} in channel ${player.voiceChannel} -> Label: ${label}`);
      console.log(`Message would be: "You are Connected To ${label}"`);
    }
  } catch (err) {
    console.error(`❌ Error testing voice channel labels:`, err);
  }
}

// Test getting a player's voice channel
async function testGetPlayerVoiceChannel() {
  console.log('\n=== Testing getPlayerVoiceChannel functionality ===');
  
  for (const player of players) {
    try {
      console.log(`Getting voice channel for ${player.minecraftUsername} (${player.discordId})...`);
      const channelId = await getPlayerVoiceChannel(player.discordId);
      
      if (channelId) {
        const label = VOICE_CHANNEL_LABELS[channelId] || channelId;
        console.log(`✅ Player ${player.minecraftUsername} is in voice channel: ${channelId} (${label})`);
        console.log(`Message would be: "You are Connected To ${label}"`);
      } else {
        console.log(`❓ Player ${player.minecraftUsername} is not in any voice channel`);
        console.log('Starting countdown would begin');
      }
    } catch (err) {
      console.error(`❌ Error getting player voice channel:`, err);
    }
  }
}

// Run the test suite
async function runTests() {
  try {
    console.log('====== Starting MongoDB Voice Channel Bot Tests ======');
    
    // Make sure data folder exists
    await fs.mkdir(DATA_FOLDER, { recursive: true });
    
    // Run tests
    await testVoiceChannelLabels();
    await testGetPlayerVoiceChannel();
    await testClearPlayerData();
    
    console.log('\n====== All tests completed ======');
  } catch (err) {
    console.error('Error during tests:', err);
  }
}

// Run the tests
runTests();
