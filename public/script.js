/**
 * Player Manager Dashboard Frontend Script
 */

// WebSocket connection
let socket;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;
let reconnectInterval = 2000; // Start with 2 seconds
const maxReconnectInterval = 30000; // Max 30 seconds

// Voice channel IDs to channel names mapping
const VOICE_CHANNEL_MAP = {
  "1179321724785922088": {id: "1179321724785922088", name: "VC-1", domId: "vc-1-players", countId: "vc-1-count", cardClass: "vc-1-card"},
  "1182188218716790885": {id: "1182188218716790885", name: "VC-2", domId: "vc-2-players", countId: "vc-2-count", cardClass: "vc-2-card"},
  "1182188286232510605": {id: "1182188286232510605", name: "VC-3", domId: "vc-3-players", countId: "vc-3-count", cardClass: "vc-3-card"}
};

// Initialize Socket Connection
function showLoading() {
  document.getElementById('loading').classList.add('active');
}

function hideLoading() {
  document.getElementById('loading').classList.remove('active');
}

function connectWebSocket() {
  showLoading();
  // Get the correct websocket URL
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws`;
  
  socket = new WebSocket(wsUrl);
  
  socket.onopen = () => {
    console.log('WebSocket connected');
    // Reset reconnect attempts on successful connection
    reconnectAttempts = 0;
    reconnectInterval = 2000;
    
    // Update connection status
    updateConnectionStatus(true);
    hideLoading();
  };
  
  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'state') {
      // Update dashboard with bot state
      updateDashboard(data.data);
    } else if (data.type === 'error') {
      // Show error message
      console.error(`Server Error: ${data.message}`);
    }
  };
  
  socket.onclose = () => {
    console.log('WebSocket disconnected');
    updateConnectionStatus(false);
    
    // Attempt to reconnect with exponential backoff
    if (reconnectAttempts < maxReconnectAttempts) {
      setTimeout(() => {
        reconnectAttempts++;
        reconnectInterval = Math.min(reconnectInterval * 1.5, maxReconnectInterval);
        console.log(`Reconnecting... attempt ${reconnectAttempts}`);
        connectWebSocket();
      }, reconnectInterval);
    } else {
      console.error('Failed to reconnect after multiple attempts. Please refresh the page.');
    }
  };
  
  socket.onerror = (error) => {
    console.error('WebSocket error:', error);
  };
}

// Update Connection Status Indicator
function updateConnectionStatus(connected) {
  const statusIcon = document.getElementById('status-icon');
  const statusText = document.getElementById('status-text');
  
  if (connected) {
    statusIcon.className = 'status-icon online';
    statusText.textContent = 'Connected';
  } else {
    statusIcon.className = 'status-icon offline';
    statusText.textContent = 'Disconnected';
  }
}

// Update Dashboard with Bot State
function updateDashboard(state) {
  // Update connection status
  updateConnectionStatus(state.connected);
  
  if (state.connected) {
    // Clear all voice channel player displays
    clearVoiceChannels();
    
    // Update voice channels with players
    if (state.voiceChannels) {
      console.log('Updating voice channels:', state.voiceChannels);
      updateVoiceChannels(state.voiceChannels);
    }
    
    // Update player commands
    if (state.devilPlsCommands) {
      updatePlayerCommands(state.devilPlsCommands);
    }
  }
}

// Clear all voice channels
function clearVoiceChannels() {
  Object.values(VOICE_CHANNEL_MAP).forEach(channel => {
    const playerContainer = document.getElementById(channel.domId);
    
    // Clear previous players
    while (playerContainer.firstChild) {
      playerContainer.removeChild(playerContainer.firstChild);
    }
    
    // Reset player count
    document.getElementById(channel.countId).textContent = "0 Players";
    
    // Add empty state if no players
    const emptyState = document.createElement('div');
    emptyState.className = 'empty-state';
    emptyState.textContent = 'No players in this voice channel';
    playerContainer.appendChild(emptyState);
  });
}

// Update voice channels with players
function updateVoiceChannels(voiceChannels) {
  console.log('Updating voice channels with data:', voiceChannels);
  if (!voiceChannels) return;
  
  // Clear all channels first
  Object.values(VOICE_CHANNEL_MAP).forEach(({ domId, countId }) => {
    const container = document.getElementById(domId);
    if (container) {
      container.innerHTML = '';
      document.getElementById(countId).textContent = '0 Players';
    }
  });
  
  // Process each voice channel
  for (const [channelId, channelData] of Object.entries(voiceChannels)) {
    console.log('Processing channel:', channelId, channelData);
    
    // Skip if channel not in our map
    if (!VOICE_CHANNEL_MAP[channelId]) {
      console.log(`Skipping unknown channel: ${channelId}`);
      continue;
    }
    
    // Get players array from channel data
    const players = channelData?.players || [];
    console.log(`Players in channel ${channelId}:`, players);
    
    const { players } = channelData;
    const { domId, countId, cardClass } = VOICE_CHANNEL_MAP[channelId];
    
    // Get container
    const playerContainer = document.getElementById(domId);
    
    // Handle no players case
    if (!players || players.length === 0) {
      const emptyState = document.createElement('div');
      emptyState.className = 'empty-state';
      emptyState.textContent = 'No players in this voice channel';
      playerContainer.appendChild(emptyState);
      continue;
    }
    
    // Update player count
    document.getElementById(countId).textContent = `${players.length} Player${players.length !== 1 ? 's' : ''}`;
    
    // Clear container
    playerContainer.innerHTML = '';
    
    // Create a card for each player
    if (players && players.length > 0) {
      players.forEach(player => {
        if (!player || !player.minecraftUsername) {
          console.warn('Invalid player data:', player);
          return;
        }
        
        console.log('Creating card for player:', player);
        const playerCard = createPlayerCard(player, cardClass);
        if (playerCard) {
          playerContainer.appendChild(playerCard);
          console.log('Player card added to container');
        }
      });
      
      // Update player count
      document.getElementById(countId).textContent = `${players.length} Player${players.length !== 1 ? 's' : ''}`;
    } else {
      // Show empty state
      const emptyState = document.createElement('div');
      emptyState.className = 'empty-state';
      emptyState.textContent = 'No players in this voice channel';
      playerContainer.appendChild(emptyState);
    }
  }
}

// Update player commands
function updatePlayerCommands(playerCommands) {
  if (!playerCommands) return;
  
  // For each player with commands, find their card and update
  for (const [discordId, commandData] of Object.entries(playerCommands)) {
    const playerCards = document.querySelectorAll(`[data-discord-id="${discordId}"]`);
    
    playerCards.forEach(card => {
      const commandsContainer = card.querySelector('.player-commands');
      if (!commandsContainer) return;
      
      // Clear previous commands
      while (commandsContainer.firstChild) {
        commandsContainer.removeChild(commandsContainer.firstChild);
      }
      
      // Add new commands
      if (commandData.commands && commandData.commands.length > 0) {
        commandData.commands.forEach(cmd => {
          const commandItem = document.createElement('div');
          commandItem.className = 'command-item';
          
          const message = document.createElement('div');
          message.className = 'command-message';
          
          // Display subcommand if available, otherwise use the full message
          message.textContent = cmd.subcommand || cmd.fullMessage || cmd.message;
          
          commandItem.appendChild(message);
          
          const timestamp = document.createElement('div');
          timestamp.className = 'command-timestamp';
          timestamp.textContent = formatTimestamp(cmd.timestamp);
          commandItem.appendChild(timestamp);
          
          commandsContainer.appendChild(commandItem);
        });
      } else {
        // No commands
        const emptyCommands = document.createElement('div');
        emptyCommands.className = 'command-empty';
        emptyCommands.textContent = 'No recent commands';
        commandsContainer.appendChild(emptyCommands);
      }
    });
  }
}

// Create a player card
function createPlayerCard(player, cardClass) {
  if (!player || !player.minecraftUsername) return null;
  
  const discordId = player.discordId || 'Unknown';
  const minecraftUsername = player.minecraftUsername;
  const avatar = player.avatar || '/images/default-avatar.svg';
  
  const card = document.createElement('div');
  card.className = `player-card ${cardClass}`;
  card.setAttribute('data-discord-id', discordId);
  
  // Card header
  const cardHeader = document.createElement('div');
  cardHeader.className = 'player-card-header';
  
  // Avatar
  const avatarContainer = document.createElement('div');
  avatarContainer.className = 'player-avatar';
  const avatarImg = document.createElement('img');
  avatarImg.src = avatar || '/images/default-avatar.png';
  avatarImg.alt = minecraftUsername;
  avatarContainer.appendChild(avatarImg);
  cardHeader.appendChild(avatarContainer);
  
  // Player info
  const playerInfo = document.createElement('div');
  playerInfo.className = 'player-info';
  
  const username = document.createElement('div');
  username.className = 'player-username';
  username.textContent = minecraftUsername;
  playerInfo.appendChild(username);
  
  const playerIds = document.createElement('div');
  playerIds.className = 'player-ids';
  playerIds.innerHTML = `
    <span>Discord ID: ${discordId}</span>
    <span>MC Username: ${minecraftUsername}</span>
  `;
  playerInfo.appendChild(playerIds);
  
  cardHeader.appendChild(playerInfo);
  card.appendChild(cardHeader);
  
  // Card body
  const cardBody = document.createElement('div');
  cardBody.className = 'player-card-body';
  
  // Commands section
  const commandsTitle = document.createElement('h4');
  commandsTitle.textContent = 'Recent "devil pls" Commands';
  commandsTitle.style.marginBottom = '10px';
  cardBody.appendChild(commandsTitle);
  
  const commandsContainer = document.createElement('div');
  commandsContainer.className = 'player-commands';
  
  // Empty placeholder (will be populated later)
  const emptyCommands = document.createElement('div');
  emptyCommands.className = 'command-empty';
  emptyCommands.textContent = 'No recent commands';
  commandsContainer.appendChild(emptyCommands);
  
  cardBody.appendChild(commandsContainer);
  card.appendChild(cardBody);
  
  return card;
}

// Format timestamp
function formatTimestamp(timestamp) {
  if (!timestamp) return '';
  
  const date = new Date(timestamp);
  return date.toLocaleString();
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  // Connect to WebSocket
  connectWebSocket();
});