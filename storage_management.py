import json
import os
import time
import datetime
from typing import Union, Dict, Any, List, Optional

from pymongo import MongoClient


class JsonFileManager:
    """ JsonFileManager class handles basic saving and loading of a json based settings file """
    def __init__(self):
        self.file_path = ""
        self.settings = None

    async def init(self) -> None:
        """ Checks if the file exists, loads if it does, creates if it doesn't """
        if await self.file_exists():
            await self.load()
        else:
            await self.create_file()

    async def create_file(self) -> None:
        """ Create an empty JSON file, usually overwritten to provide config structure and defaults """
        self.settings = {}
        await self.write_file_to_disk()

    async def file_exists(self) -> bool:
        """ Checks if the file exists """
        try:
            open(self.file_path, "r")
            return True
        except FileNotFoundError:
            return False

    async def load(self) -> None:
        """ Loads the json file from disk into self.settings """
        self.settings = await self.load_local()

    async def load_local(self) -> dict:
        """ Returns the contents of the json file from disk, doesn't overwrite the stored settings. USE FOR READING VALUES ONLY! """
        with open(self.file_path, "r") as r:
            settings = json.load(r)
            r.close()
            return settings

    async def write_file_to_disk(self) -> None:
        """ Saves the contents of self.settings to disk """
        with open(self.file_path, "w+") as w:
            json.dump(self.settings, w, indent=4)
            w.close()


class MongoDBManager:
    """ MongoDB manager class handles basic operations with MongoDB database """
    def __init__(self):
        # Connect to MongoDB using the provided connection string - now using MongoDB exclusively
        mongo_uri = "mongodb+srv://sanmod:RCL9JLVL@san-mod.ocfuqyn.mongodb.net/?retryWrites=true&w=majority&appName=san-mod"
        self.client = MongoClient(mongo_uri)
        self.db = self.client['devil_smp_db']
        
        # Main data collections
        self.guilds = self.db['guilds']
        self.users = self.db['users']
        self.moderation = self.db['moderation']  # Collection for moderation actions
        self.temporary_actions = self.db['temporary_actions']  # Collection for temporary data like anti-raid
        self.curse_words = self.db['curse_words']  # Collection for curse words
        self.user_profiles = self.db['user_profiles']  # Collection for user profiles
        
        # Additional collections for enhanced functionality
        self.bot_metrics = self.db['bot_metrics']  # Collection for bot usage statistics
        self.user_preferences = self.db['user_preferences']  # Collection for user settings
        self.dm_logs = self.db['dm_logs']  # Collection for tracking DM communications
        
        # For backward compatibility with existing code
        self.settings = {"guilds": {}}
        
        print("MongoDB initialized - Using MongoDB exclusively for all data storage")
        
    async def init_db(self) -> None:
        """ Initialize the database """
        # No need to explicitly create collections in MongoDB
        # Load all guilds into the settings object for backward compatibility
        guilds = list(self.guilds.find({}))
        for guild in guilds:
            self.settings["guilds"][guild["_id"]] = guild
            
        # Set up TTL index for temporary actions to auto-delete after expiry
        # This is crucial for memory management, especially for raid detection
        try:
            self.temporary_actions.create_index(
                "expires_at", 
                expireAfterSeconds=0  # Delete when expires_at time is reached
            )
        except Exception as e:
            print(f"Error creating TTL index for temporary_actions: {e}")
            
        # Make sure curse.txt file exists by calling get_curse_words
        await self.get_curse_words()
        
    async def get_guild(self, guild_id: str) -> Dict[str, Any]:
        """ Get a guild from the database """
        guild_id = str(guild_id)
        guild = self.guilds.find_one({"_id": guild_id})
        
        # If guild doesn't exist, create it
        if not guild:
            print(f"Guild {guild_id} not found in database in get_guild, creating it")
            await self.add_guild(guild_id)
            guild = self.guilds.find_one({"_id": guild_id})
            
            # If still None after creation attempt, return a default guild dict
            if not guild:
                print(f"Warning: Failed to create or retrieve guild {guild_id}")
                guild = {
                    "_id": guild_id,
                    "muted_role_id": 0,
                    "log_channel_id": 0,
                    "mod_roles": [],
                    "muted_users": {},
                    "banned_users": {},
                    "warning_users": {}
                }
        
        # For backward compatibility, add it to the settings
        if "guilds" not in self.settings:
            self.settings["guilds"] = {}
            
        self.settings["guilds"][guild_id] = guild
            
        return guild
        
    async def update_guild(self, guild_id: str, update_data: Dict[str, Any]) -> None:
        """ Update a guild in the database """
        guild_id = str(guild_id)
        
        # Update in MongoDB
        self.guilds.update_one(
            {"_id": guild_id}, 
            {"$set": update_data}, 
            upsert=True
        )
        
        # Update in memory settings for backward compatibility
        if guild_id in self.settings["guilds"]:
            for key, value in update_data.items():
                self.settings["guilds"][guild_id][key] = value
        else:
            # Get the full updated document
            updated_guild = self.guilds.find_one({"_id": guild_id})
            if updated_guild:
                self.settings["guilds"][guild_id] = updated_guild
                
    async def get_curse_words(self) -> List[str]:
        """ Get all curse words from the MongoDB curse_words collection """
        # Check if curse words collection has any entries
        count = self.curse_words.count_documents({})
        
        if count == 0:
            # No curse words in DB, add default ones
            default_words = [
                {"word": "fuck", "severity": "high", "added_at": datetime.datetime.utcnow()},
                {"word": "bitch", "severity": "medium", "added_at": datetime.datetime.utcnow()},
                {"word": "asshole", "severity": "medium", "added_at": datetime.datetime.utcnow()},
                {"word": "cunt", "severity": "high", "added_at": datetime.datetime.utcnow()},
                {"word": "dick", "severity": "medium", "added_at": datetime.datetime.utcnow()},
                {"word": "niger", "severity": "high", "added_at": datetime.datetime.utcnow()},
                {"word": "nigga", "severity": "high", "added_at": datetime.datetime.utcnow()},
                {"word": "b1tch", "severity": "medium", "added_at": datetime.datetime.utcnow()},
                {"word": "pussy", "severity": "medium", "added_at": datetime.datetime.utcnow()},
                {"word": "cock", "severity": "medium", "added_at": datetime.datetime.utcnow()},
                {"word": "motherfucker", "severity": "high", "added_at": datetime.datetime.utcnow()},
                {"word": "whore", "severity": "medium", "added_at": datetime.datetime.utcnow()},
                {"word": "slut", "severity": "medium", "added_at": datetime.datetime.utcnow()},
                {"word": "bastard", "severity": "low", "added_at": datetime.datetime.utcnow()}
            ]
            
            self.curse_words.insert_many(default_words)
            
            # Migrate existing words from curse.txt if it exists
            try:
                with open("curse.txt", "r") as f:
                    file_words = [line.strip().lower() for line in f if line.strip()]
                
                # Add any words from file that aren't in the default list
                for word in file_words:
                    if word not in [w["word"] for w in default_words]:
                        self.curse_words.insert_one({
                            "word": word, 
                            "severity": "medium", 
                            "added_at": datetime.datetime.utcnow()
                        })
            except FileNotFoundError:
                # File doesn't exist, just use the defaults
                pass
                
        # Return all words from the collection
        cursor = self.curse_words.find({})
        return [doc["word"] for doc in cursor]
        
    async def add_curse_word(self, word: str, severity: str = "medium") -> None:
        """ Add a curse word to the MongoDB curse_words collection """
        word = word.lower().strip()
        
        # Check if word already exists
        existing = self.curse_words.find_one({"word": word})
        if not existing:
            # Add new word
            self.curse_words.insert_one({
                "word": word,
                "severity": severity,
                "added_at": datetime.datetime.utcnow()
            })
        
    async def remove_curse_word(self, word: str) -> None:
        """ Remove a curse word from the MongoDB curse_words collection """
        word = word.lower().strip()
        self.curse_words.delete_one({"word": word})
        
    async def is_curse_word(self, word: str) -> bool:
        """ Check if a word is a curse word """
        word = word.lower().strip()
        return self.curse_words.find_one({"word": word}) is not None
        
    async def get_curse_word_details(self, word: str) -> Optional[Dict[str, Any]]:
        """ Get details for a specific curse word including severity """
        word = word.lower().strip()
        return self.curse_words.find_one({"word": word})
        
    async def add_warning(self, guild_id: str, user_id: str, curse_word: str) -> int:
        """ Add a warning for a user """
        guild_id = str(guild_id)
        user_id = str(user_id)
        
        # Get the guild
        guild = await self.get_guild(guild_id)
        if not guild:
            # Guild doesn't exist, create it
            await self.add_guild(guild_id)
            guild = await self.get_guild(guild_id)
            
        # Initialize or get warning_users
        warning_users = guild.get("warning_users", {})
        
        # Add or update user warnings
        if user_id not in warning_users:
            warning_users[user_id] = {
                "count": 1,
                "last_curse": curse_word,
                "last_warning_time": int(time.time()),
                "curse_words": [curse_word]
            }
        else:
            warning_users[user_id]["count"] += 1
            warning_users[user_id]["last_curse"] = curse_word
            warning_users[user_id]["last_warning_time"] = int(time.time())
            warning_users[user_id]["curse_words"].append(curse_word)
            
        # Update guild in database
        await self.update_guild(guild_id, {"warning_users": warning_users})
        
        # Return warning count
        return warning_users[user_id]["count"]
        
    async def reset_warnings(self, guild_id: str, user_id: str) -> None:
        """ Reset warnings for a user """
        guild_id = str(guild_id)
        user_id = str(user_id)
        
        # Get the guild
        guild = await self.get_guild(guild_id)
        if not guild:
            return
            
        # Get warning_users
        warning_users = guild.get("warning_users", {})
        
        # Remove user warnings if they exist
        if user_id in warning_users:
            del warning_users[user_id]
            await self.update_guild(guild_id, {"warning_users": warning_users})
        
    async def get_timeout_duration(self, warning_count: int) -> int:
        """ Get timeout duration based on warning count """
        # Map warning count to timeout duration in seconds
        durations = {
            1: 0,        # No timeout for first warning
            2: 60,       # 1 minute
            3: 1800,     # 30 minutes
            4: 3600,     # 1 hour
            5: 7200,     # 2 hours
            6: 10800,    # 3 hours
        }
        return durations.get(warning_count, 10800)  # Default to 3 hours for counts over 6
            
    async def get_warnings(self, guild_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """ Get warnings for a user """
        guild_id = str(guild_id)
        user_id = str(user_id)
        
        # Get the guild
        guild = await self.get_guild(guild_id)
        if not guild:
            return None
            
        # Get warning_users
        warning_users = guild.get("warning_users", {})
        
        # Return user warnings if they exist
        return warning_users.get(user_id)
        
    async def log_moderation_action(self, action_type: str, guild_id: str, user_id: str, 
                                     moderator_id: str, reason: str = None, 
                                     duration: int = None, extra_data: Dict[str, Any] = None) -> str:
        """ Log a moderation action in the moderation collection
        
        Args:
            action_type: Type of action (ban, kick, mute, unmute, timeout, warning, etc.)
            guild_id: Guild ID where action occurred
            user_id: User ID who received the action
            moderator_id: Moderator ID who performed the action
            reason: Reason for the action
            duration: Duration of the action in seconds (if applicable)
            extra_data: Additional data related to the action
            
        Returns:
            The ID of the logged action
        """
        # Convert IDs to strings for consistency
        guild_id = str(guild_id)
        user_id = str(user_id)
        moderator_id = str(moderator_id)
        
        # Create action document
        action = {
            "action_type": action_type,
            "guild_id": guild_id,
            "user_id": user_id,
            "moderator_id": moderator_id,
            "reason": reason or "No reason provided",
            "timestamp": datetime.datetime.utcnow(),
            "duration": duration
        }
        
        # Add extra data if provided
        if extra_data:
            action.update(extra_data)
            
        # Insert into moderation collection
        result = self.moderation.insert_one(action)
        
        # Return the ID of the inserted document
        return str(result.inserted_id)
        
    async def get_user_moderation_history(self, guild_id: str, user_id: str) -> List[Dict[str, Any]]:
        """ Get all moderation actions for a user in a guild
        
        Args:
            guild_id: Guild ID to search in
            user_id: User ID to get history for
            
        Returns:
            List of moderation actions for the user
        """
        guild_id = str(guild_id)
        user_id = str(user_id)
        
        # Query moderation collection
        cursor = self.moderation.find({
            "guild_id": guild_id,
            "user_id": user_id
        }).sort("timestamp", -1)  # Sort by timestamp descending (newest first)
        
        # Convert cursor to list
        return list(cursor)
        
    # === User Profile Management ===
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user's profile from MongoDB
        
        Args:
            user_id: The Discord user ID
            
        Returns:
            The user profile data if found, None otherwise
        """
        user_id = str(user_id)
        return self.user_profiles.find_one({"_id": user_id})
        
    async def create_user_profile(self, user_id: str, username: str, avatar_url: str = None) -> Dict[str, Any]:
        """Create a new user profile in MongoDB
        
        Args:
            user_id: The Discord user ID
            username: The Discord username
            avatar_url: URL to the user's avatar (optional)
            
        Returns:
            The newly created user profile
        """
        user_id = str(user_id)
        
        # Check if profile already exists
        existing = await self.get_user_profile(user_id)
        if existing:
            return existing
            
        # Create new profile with default values
        profile = {
            "_id": user_id,
            "username": username,
            "avatar_url": avatar_url,
            "created_at": datetime.datetime.utcnow(),
            "updated_at": datetime.datetime.utcnow(),
            "bio": "",
            "preferences": {
                "dm_notifications": True,
                "theme": "dark",
                "language": "en"
            },
            "stats": {
                "messages_sent": 0,
                "commands_used": 0,
                "warnings_received": 0,
                "last_active": datetime.datetime.utcnow()
            },
            "badges": [],
            "custom_fields": {}
        }
        
        # Insert into MongoDB
        self.user_profiles.insert_one(profile)
        return profile
        
    async def update_user_profile(self, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a user's profile in MongoDB
        
        Args:
            user_id: The Discord user ID
            update_data: Dictionary of fields to update
            
        Returns:
            The updated user profile or None if not found
        """
        user_id = str(user_id)
        
        # Add updated_at timestamp
        update_data["updated_at"] = datetime.datetime.utcnow()
        
        # Update in MongoDB
        result = self.user_profiles.update_one(
            {"_id": user_id},
            {"$set": update_data}
        )
        
        if result.matched_count > 0:
            return self.user_profiles.find_one({"_id": user_id})
        else:
            return None
            
    async def increment_user_stat(self, user_id: str, stat_name: str, amount: int = 1) -> None:
        """Increment a user's statistic in their profile
        
        Args:
            user_id: The Discord user ID
            stat_name: The name of the stat to increment (e.g., 'messages_sent')
            amount: The amount to increment by (default: 1)
        """
        user_id = str(user_id)
        
        # Update the specific stat using MongoDB's $inc operator
        self.user_profiles.update_one(
            {"_id": user_id},
            {
                "$inc": {f"stats.{stat_name}": amount},
                "$set": {"stats.last_active": datetime.datetime.utcnow(), "updated_at": datetime.datetime.utcnow()}
            }
        )
        
    async def add_user_badge(self, user_id: str, badge_name: str, badge_icon: str = None) -> None:
        """Add a badge to a user's profile
        
        Args:
            user_id: The Discord user ID
            badge_name: The name of the badge
            badge_icon: The emoji or icon for the badge (optional)
        """
        user_id = str(user_id)
        
        # Create badge object
        badge = {
            "name": badge_name,
            "icon": badge_icon,
            "awarded_at": datetime.datetime.utcnow()
        }
        
        # Add badge to user's profile
        self.user_profiles.update_one(
            {"_id": user_id},
            {
                "$push": {"badges": badge},
                "$set": {"updated_at": datetime.datetime.utcnow()}
            }
        )
        
    async def remove_user_badge(self, user_id: str, badge_name: str) -> None:
        """Remove a badge from a user's profile
        
        Args:
            user_id: The Discord user ID
            badge_name: The name of the badge to remove
        """
        user_id = str(user_id)
        
        # Remove badge from user's profile
        self.user_profiles.update_one(
            {"_id": user_id},
            {
                "$pull": {"badges": {"name": badge_name}},
                "$set": {"updated_at": datetime.datetime.utcnow()}
            }
        )
        
    async def set_user_preference(self, user_id: str, preference_name: str, preference_value: Any) -> None:
        """Set a user preference
        
        Args:
            user_id: The Discord user ID
            preference_name: The name of the preference to set
            preference_value: The value to set for the preference
        """
        user_id = str(user_id)
        
        # Set the preference
        self.user_profiles.update_one(
            {"_id": user_id},
            {
                "$set": {f"preferences.{preference_name}": preference_value, "updated_at": datetime.datetime.utcnow()}
            }
        )
        
    async def get_top_users(self, stat_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top users by a particular statistic
        
        Args:
            stat_name: The statistic to sort by (e.g., 'messages_sent')
            limit: Maximum number of users to return
            
        Returns:
            List of user profiles sorted by the specified statistic
        """
        cursor = self.user_profiles.find({}).sort(f"stats.{stat_name}", -1).limit(limit)
        return list(cursor)


class StorageManagement(MongoDBManager):
    def __init__(self):
        # Initialize MongoDBManager first
        super().__init__()
        
        # Ensure the guilds dictionary exists in settings
        if not hasattr(self, 'settings'):
            self.settings = {}
        
        if 'guilds' not in self.settings:
            self.settings['guilds'] = {}
        
    async def init(self) -> None:
        """ Initialize storage """
        await self.init_db()
        
    async def create_file(self) -> None:
        """ Legacy method for compatibility """
        pass
        
    async def has_guild(self, guild_id) -> bool:
        """ Check if a guild exists in the database """
        guild_id = str(guild_id)
        return self.guilds.find_one({"_id": guild_id}) is not None
        
    async def add_guild(self, guild_id) -> None:
        """ Add a guild to the database """
        guild_id = str(guild_id)
        if not await self.has_guild(guild_id):
            guild_data = {
                "_id": guild_id,
                "muted_role_id": 0,
                "log_channel_id": 1249380931781791855,  # Use the specific channel ID for logging
                "mod_roles": [],
                "muted_users": {},
                "banned_users": {},
                "warning_users": {}
            }
            
            try:
                # Insert into MongoDB
                self.guilds.insert_one(guild_data)
                
                # Make sure the guilds dict exists in settings
                if "guilds" not in self.settings:
                    self.settings["guilds"] = {}
                
                # Update in memory settings
                self.settings["guilds"][guild_id] = guild_data
                
                print(f"Added guild {guild_id} to MongoDB database")
            except Exception as e:
                print(f"Error adding guild to MongoDB: {e}")
                # Create a basic entry anyway to prevent further errors
                if "guilds" not in self.settings:
                    self.settings["guilds"] = {}
                
                self.settings["guilds"][guild_id] = guild_data
        
    async def write_file_to_disk(self) -> None:
        """ For backward compatibility - updates MongoDB with changes from settings """
        for guild_id, guild_data in self.settings["guilds"].items():
            # Remove _id if it exists to avoid update errors
            if "_id" in guild_data:
                guild_data_copy = guild_data.copy()
                del guild_data_copy["_id"]
                await self.update_guild(guild_id, guild_data_copy)
            else:
                await self.update_guild(guild_id, guild_data)


class ConfigManagement(JsonFileManager):
    """ Example custom config class to handle non guild-specific settings for customized features of the bot """
    def __init__(self):
        __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        self.file_path = os.path.join(__location__, "custom_config.json")
        self.settings = None

    async def create_file(self) -> None:
        self.settings = {
            "some_key": "some_value"
        }
        await self.write_file_to_disk()

    async def get_value(self, some_key) -> Union[str, None]:
        """ Example function loading a key from the config file """
        await self.load()
        return self.settings.get(some_key)

    async def set_value(self, some_key, some_value) -> None:
        """ Example function setting a value to the config file and saving it to disk """
        self.settings[some_key] = some_value
        await self.write_file_to_disk()
