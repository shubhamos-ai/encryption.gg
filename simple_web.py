from flask import Flask
import threading
import logging

# Configure logging - minimal output for cleaner console
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler()]
)

# Silence verbose loggers
for logger_name in ['werkzeug', 'discord', 'urllib3', 'asyncio', 'urllib3.connectionpool']:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

app = Flask(__name__)

# Global variable to track bot status
bot_started = False

@app.route('/')
def index():
    if bot_started:
        status = "running"
    else:
        status = "initializing"
    return f'<html><body><h1>Discord Bot Status</h1><p>Bot is {status}!</p></body></html>'

# Simple web server for 24/7 uptime
def start_flask():
    """Start the Flask web server"""
    # Set log level to ERROR to reduce console noise
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=5000, debug=False)

def run_bot():
    """Run the bot and Flask in a thread (for use with gunicorn)"""
    global bot_started
    
    # Import here to avoid circular imports
    from bot_helpers import set_bot_instance
    
    try:
        # Import Discord modules
        import discord
        from bot import ModerationBot
        
        # Read token
        token = None
        try:
            with open("token.txt", "r") as f:
                token = f.read().strip()
                if not token:
                    print("ERROR: Empty token.txt. Add your Discord bot token to this file.")
        except FileNotFoundError:
            print("ERROR: token.txt not found. Create this file with your Discord bot token.")
            return
            
        if not token:
            return
            
        # Set up Discord bot
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.presences = True
        
        # Create and start bot
        print("Starting Discord bot...")
        bot = ModerationBot(intents)
        set_bot_instance(bot)
        
        # Start the bot in a thread so it doesn't block gunicorn
        def start_bot():
            global bot_started
            bot.run(token)
            bot_started = False  # Bot has stopped
            
        bot_thread = threading.Thread(target=start_bot)
        bot_thread.daemon = True
        bot_thread.start()
        
        # Mark bot as started
        bot_started = True
        
    except Exception as e:
        print(f"Error starting bot: {e}")
        
# Start the bot when this module is imported (for gunicorn)
if __name__ != "__main__":  # When imported by gunicorn
    run_bot()