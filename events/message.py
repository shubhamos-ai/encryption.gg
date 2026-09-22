import inspect
import sys
import asyncio
import time
import datetime
import re
import json
import requests
import os

import discord
from discord.ext import commands

from bot import ModerationBot
from helpers.embed_builder import EmbedBuilder
from events.base import EventHandler


class MessageEvent(EventHandler):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.client = client_instance
        self.event = "on_message"
        # Anti-raid configuration (message tracking is now done transiently)
        self.raid_threshold = 5  # Number of messages in short time to trigger anti-raid
        self.raid_timeframe = 5  # Time window in seconds to consider for raid detection
        
        # Constants for spam detection
        self.spam_threshold = 5  # Number of similar messages to trigger spam warning
        self.spam_timeframe = 30  # Timeframe in seconds for spam detection
        
        # Constants for message content moderation
        self.max_mentions = 5  # Maximum mentions allowed in a message
        self.max_emoji_percent = 40  # Maximum percentage of message that can be emojis
        self.max_caps_percent = 70  # Maximum percentage of message that can be caps

    async def handle(self, message: discord.Message, *args, **kwargs) -> None:
        # Get the user from the message
        user = message.author
        guild_id = str(message.guild.id) if message.guild else None
        
        # Ignore messages from bots or if the message has no text or if not in a guild
        if user.bot or not message.content or not guild_id:
            return
        
        # Process command messages with the prefix first for faster response
        # Only process commands for messages with the prefix
        if message.content.lower().startswith(self.client.prefix.lower()):
            # Message starts with our prefix, extract the command and arguments
            command_text = message.content[len(self.client.prefix):].strip()
            
            if not command_text:
                await message.channel.send(f"Please specify a command after `{self.client.prefix}`")
                return
                
            # Split the command text into the command and arguments
            command_parts = command_text.split()
            cmd = command_parts[0].lower()
            
            # All other commands have been removed; only "manage" is available
            if cmd != "manage":
                await message.channel.send(f"⚠️ Unknown command. Please use `{self.client.prefix}manage @user` for all moderation actions.")
                return
                
            # Special handling for 'devil manage user' format
            if len(command_parts) >= 2 and command_parts[1].lower() == "user":
                # Don't respond to incorrect format
                print(f"Ignoring incorrect command format: {message.content}")
                return
                
            # Check if this is a reply to another message and has mentions
            has_mentions = len(message.mentions) > 0
            is_reply = message.reference is not None
            
            # If it's a reply to another message, we'll handle it intelligently
            if is_reply and not has_mentions:
                try:
                    # Get the original message that was replied to
                    reply_msg = None
                    if message.reference.resolved:
                        reply_msg = message.reference.resolved
                    else:
                        # Fetch the message if not already resolved
                        reply_channel = self.client.get_channel(message.reference.channel_id)
                        if reply_channel:
                            reply_msg = await reply_channel.fetch_message(message.reference.message_id)
                    
                    if reply_msg and reply_msg.author:
                        # Add the author of the original message as a mentioned user
                        message.mentions.append(reply_msg.author)
                        has_mentions = True
                except Exception as e:
                    print(f"Error resolving replied message: {e}")
            
            # If no user mentions after all our checks, prompt for correct usage
            if not has_mentions and cmd == "manage":
                await message.channel.send(f"Please mention a user with `{self.client.prefix}manage @user` or reply to their message")
                return
                
            # Get the command handler and execute it
            command_instance = self.client.registry.get_command(cmd)
            if command_instance is not None:
                args = command_parts[1:] if len(command_parts) > 1 else []
                
                # Add a flag to the message to prevent duplicate execution
                # Using a unique attribute name that's unlikely to conflict with Discord.py
                if not hasattr(message, '_devil_cmd_processed'):
                    setattr(message, '_devil_cmd_processed', True)
                    
                    # Execute the command immediately
                    try:
                        # Print info for debugging (only once)
                        print(f"Executing command: {cmd} with args: {args}")
                        # Execute the command
                        await command_instance.execute(message, args=args)
                    except Exception as e:
                        print(f"Error in command execution: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        # Reply to the original message with the error
                        await message.reply(f"Error executing command. Please try again or contact an administrator.", mention_author=False)
                else:
                    print(f"Prevented duplicate execution of command: {cmd}")
            else:
                await message.reply(f"**Command unavailable.** Please use `{self.client.prefix}manage @user` for moderation.", mention_author=False)
                
            # After command handling, do moderation checks in the background
            asyncio.create_task(self.run_moderation_checks(message))
        else:
            # For non-command messages, check content moderation directly
            # Check for content moderation warnings even for non-prefix messages
            # These don't delete messages, just warn users about content issues
            await self.check_for_mass_mentions(message)
            await self.check_for_spam(message)
            await self.check_for_mass_emoji(message)
            await self.check_for_excessive_caps(message)
            
    async def run_moderation_checks(self, message: discord.Message) -> None:
        """Run moderation checks in the background after command processing"""
        # For messages with the prefix, check for curse words and raid activity
        # Check for curse words first (before command processing)
        if await self.check_for_curse_words(message):
            return
            
        # Check for potential raid activity
        if await self.check_for_raid_activity(message):
            return
            
        # Run other checks
        await self.check_for_mass_mentions(message)
        await self.check_for_spam(message)
        await self.check_for_mass_emoji(message)
        await self.check_for_excessive_caps(message)
            
    async def check_for_curse_words(self, message: discord.Message) -> bool:
        """
        Check if the message contains curse words, delete message and warn user if it does
        Returns True if message contained curse words, False otherwise
        Uses only the local curse.txt file for word filtering with advanced detection methods
        """
        # Get message content
        content = message.content.lower()
        
        # Initialize curse word detection
        curse_words = []
        
        # Load curse words from curse.txt directly
        try:
            with open("curse.txt", "r") as f:
                local_curse_words = [line.strip().lower() for line in f.readlines()]
            
            # Method 1: Simple word matching
            words = re.findall(r'\b\w+\b', content)
            for word in words:
                if word.lower() in local_curse_words and word not in curse_words:
                    curse_words.append(word)
            
            # Method 2: Check for leetspeak/character replacements (if no direct matches found)
            if not curse_words:
                # Convert common leetspeak characters to regular letters
                leet_map = {
                    '0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', 
                    '6': 'g', '7': 't', '8': 'b', '@': 'a', '$': 's'
                }
                
                normalized_content = content
                for leet_char, normal_char in leet_map.items():
                    normalized_content = normalized_content.replace(leet_char, normal_char)
                
                # Split normalized content into words
                normalized_words = re.findall(r'\b\w+\b', normalized_content)
                
                # Check each word against curse list
                for word in normalized_words:
                    if word.lower() in local_curse_words and word not in curse_words:
                        # Get the original word from content that matched after normalization
                        original_index = words.index(word) if word in words else -1
                        if original_index >= 0:
                            curse_words.append(words[original_index])
                        else:
                            curse_words.append(word)
            
            # Method 3: Check for deliberate word breaks with spacing or characters
            if not curse_words:
                # Join all content without spaces and check for curse words
                no_spaces = content.replace(" ", "").replace("-", "").replace("_", "").replace(".", "")
                for curse_word in local_curse_words:
                    if curse_word in no_spaces and curse_word not in curse_words:
                        curse_words.append(curse_word)
                        
            # Method 4: Check for partially obfuscated words (e.g., f*ck)
            if not curse_words:
                for curse_word in local_curse_words:
                    if len(curse_word) > 3:  # Only check longer words
                        # Create pattern like f.{1}ck or fu.{1}k
                        first_char = curse_word[0]
                        last_char = curse_word[-1]
                        middle_len = len(curse_word) - 2
                        pattern = f"{first_char}.{{{1,{middle_len}}}}?{last_char}"
                        
                        # Search for pattern
                        matches = re.findall(pattern, content)
                        if matches:
                            for match in matches:
                                # Verify the match is likely to be a curse word
                                if len(match) >= len(curse_word) * 0.7:
                                    curse_words.append(curse_word)
                                    break
                                    
        except Exception as e:
            print(f"Error in advanced curse word detection: {e}")
        
        # If no curse words from either source, return False
        if not curse_words:
            return False
        
        # If there are curse words, delete the message
        try:
            await message.delete()
        except Exception as e:
            print(f"Error deleting message with curse words: {e}")
            return False
            
        # Get curse word count for user
        warning_count = await self.client.storage.add_warning(
            str(message.guild.id), 
            str(message.author.id), 
            curse_words[0]  # Store first found curse word
        )
        
        # Create fancy warning message with emoji and better formatting
        warning_embed = discord.Embed(
            title="⚠️ Message Deleted - Inappropriate Content",
            description=f"{message.author.mention}'s message violated server rules.",
            color=0xFF0000  # Red color
        )
        warning_embed.add_field(name="Banned Word", value=f"||{curse_words[0]}||", inline=True)  # Spoiler tag to hide the word
        warning_embed.add_field(name="Warning Count", value=f"#{warning_count}", inline=True)
        warning_embed.set_footer(text="This message will auto-delete in 5 seconds • DevilSMP Moderation")
        
        # Send the fancy embed instead of plain text
        warning_message = await message.channel.send(embed=warning_embed)
        
        # Schedule message deletion after 5 seconds
        await asyncio.sleep(5)
        try:
            await warning_message.delete()
        except:
            pass
        
        # Check if we need to timeout the user based on warning count
        timeout_duration = await self.client.storage.get_timeout_duration(warning_count)
        
        if timeout_duration > 0:
            # Apply timeout
            try:
                # Max warning reached (6 or more warnings)
                if warning_count >= 6:
                    # Remove role "1076153405929689218" and add role "993569461841965188"
                    target_role = discord.utils.get(message.guild.roles, id=1076153405929689218)
                    penalty_role = discord.utils.get(message.guild.roles, id=993569461841965188)
                    
                    if target_role and penalty_role:
                        await message.author.remove_roles(target_role, reason="Exceeded maximum warnings")
                        await message.author.add_roles(penalty_role, reason="Exceeded maximum warnings")
                        
                        # Send public message about role change
                        await message.channel.send(
                            f"**{message.author.mention} has been demoted for repeatedly using banned words after multiple warnings.**"
                        )
                    else:
                        # Apply timeout if roles can't be found
                        until = discord.utils.utcnow() + datetime.timedelta(seconds=timeout_duration)
                        await message.author.timeout(until, reason=f"Automatic timeout after {warning_count} curse word warnings")
                        
                        # Get human-readable duration
                        if timeout_duration == 60:
                            duration_text = "1 minute"
                        elif timeout_duration == 1800:
                            duration_text = "30 minutes"
                        elif timeout_duration == 3600:
                            duration_text = "1 hour"
                        elif timeout_duration == 7200:
                            duration_text = "2 hours"
                        elif timeout_duration == 10800:
                            duration_text = "3 hours"
                        else:
                            duration_text = f"{timeout_duration} seconds"
                            
                        # Send public message about timeout
                        await message.channel.send(
                            f"**{message.author.mention} has been timed out for {duration_text} after receiving {warning_count} warnings.**"
                        )
                
                # Apply timeout for warnings 2-5
                elif warning_count >= 2:
                    until = discord.utils.utcnow() + datetime.timedelta(seconds=timeout_duration)
                    await message.author.timeout(until, reason=f"Automatic timeout after {warning_count} curse word warnings")
                    
                    # Get human-readable duration
                    if timeout_duration == 60:
                        duration_text = "1 minute"
                    elif timeout_duration == 1800:
                        duration_text = "30 minutes"
                    elif timeout_duration == 3600:
                        duration_text = "1 hour"
                    elif timeout_duration == 7200:
                        duration_text = "2 hours"
                    else:
                        duration_text = f"{timeout_duration} seconds"
                        
                    # Send public message about timeout
                    await message.channel.send(
                        f"**{message.author.mention} has been timed out for {duration_text} after receiving {warning_count} warnings.**"
                    )
                    
                # Log the action to MongoDB
                extra_data = {
                    "curse_word": curse_words[0],
                    "warning_count": warning_count,
                    "timeout_duration": timeout_duration
                }
                
                # Track roles that might have been modified
                target_role = discord.utils.get(message.guild.roles, id=1076153405929689218)
                penalty_role = discord.utils.get(message.guild.roles, id=993569461841965188)
                
                # If role changes were applied
                if warning_count >= 6 and target_role and penalty_role:
                    extra_data["role_removed"] = str(target_role.id)
                    extra_data["role_added"] = str(penalty_role.id)
                
                await self.client.storage.log_moderation_action(
                    action_type="auto_moderation",
                    guild_id=str(message.guild.id),
                    user_id=str(message.author.id),
                    moderator_id=str(self.client.user.id),  # Bot is the moderator
                    reason=f"Curse word detected: {curse_words[0]} (Warning {warning_count})",
                    duration=timeout_duration,
                    extra_data=extra_data
                )
                
                # Also create Discord embed for the log channel
                embed_builder = EmbedBuilder(event="auto_moderation")
                await embed_builder.add_field(name="**Action**", value=f"`Curse word detected`")
                await embed_builder.add_field(name="**User**", value=f"`{message.author.name}`")
                await embed_builder.add_field(name="**Word**", value=f"`{curse_words[0]}`")
                await embed_builder.add_field(name="**Warning Count**", value=f"`{warning_count}`")
                
                if timeout_duration > 0:
                    await embed_builder.add_field(name="**Timeout Duration**", value=f"`{timeout_duration} seconds`")
                    
                embed = await embed_builder.get_embed()
                
                # Use hard-coded log channel ID
                log_channel = message.guild.get_channel(1249380931781791855)
                
                if log_channel:
                    await log_channel.send(embed=embed)
                    
            except Exception as e:
                print(f"Error applying timeout for curse words: {e}")
                
        return True
        
    async def check_for_mass_mentions(self, message: discord.Message) -> None:
        """
        Check if a message contains too many mentions and warn the user
        Does not delete the message, only warns the user
        """
        mention_count = len(message.mentions) + len(message.role_mentions)
        
        if mention_count > self.max_mentions:
            # Don't delete message, just warn
            warning_message = await message.channel.send(
                f"**{message.author.mention} Please avoid mass mentions. Your message contained {mention_count} mentions.**"
            )
            
            # Add this warning to MongoDB for tracking
            warning_count = await self.client.storage.add_warning(
                str(message.guild.id),
                str(message.author.id),
                "mass_mentions"
            )
            
            # Log to moderation channel
            embed_builder = EmbedBuilder(event="auto_moderation")
            await embed_builder.add_field(name="**Action**", value=f"`Mass mentions warning`")
            await embed_builder.add_field(name="**User**", value=f"`{message.author.name}`")
            await embed_builder.add_field(name="**Mention Count**", value=f"`{mention_count}`")
            await embed_builder.add_field(name="**Warning Count**", value=f"`{warning_count}`")
            embed = await embed_builder.get_embed()
                
            # Use hard-coded log channel ID
            log_channel = message.guild.get_channel(1249380931781791855)
            
            if log_channel:
                await log_channel.send(embed=embed)
                
            # Delete warning after 5 seconds
            await asyncio.sleep(5)
            try:
                await warning_message.delete()
            except:
                pass
            
            # Apply timeouts for repeated offenses
            if warning_count >= 5:
                # Get timeout duration based on warning count
                timeout_duration = await self.client.storage.get_timeout_duration(warning_count)
                if timeout_duration > 0:
                    try:
                        until = discord.utils.utcnow() + datetime.timedelta(seconds=timeout_duration)
                        await message.author.timeout(until, reason=f"Automatic timeout after {warning_count} mass mentions warnings")
                        
                        # Get human-readable duration
                        if timeout_duration == 60:
                            duration_text = "1 minute"
                        elif timeout_duration == 1800:
                            duration_text = "30 minutes"
                        elif timeout_duration == 3600:
                            duration_text = "1 hour"
                        elif timeout_duration == 7200:
                            duration_text = "2 hours"
                        elif timeout_duration == 10800:
                            duration_text = "3 hours"
                        else:
                            duration_text = f"{timeout_duration} seconds"
                            
                        # Send public message about timeout
                        await message.channel.send(
                            f"**{message.author.mention} has been timed out for {duration_text} after receiving {warning_count} warnings.**"
                        )
                    except Exception as e:
                        print(f"Error applying timeout for mass mentions: {e}")
    
    async def check_for_spam(self, message: discord.Message) -> None:
        """
        Check if the message is part of a spam pattern and warn the user
        Does not delete the message, only warns the user after 5+ similar messages
        """
        # Get user and guild IDs
        user_id = str(message.author.id)
        guild_id = str(message.guild.id)
        content_hash = hash(message.content.lower())
        
        # Record this message in the database for spam detection
        current_time = time.time()
        
        # Get user's recent message timestamps from temporary actions collection
        collection = self.client.storage.db.temporary_actions
        
        # Add current message with content hash - no await needed for insert_one
        collection.insert_one({
            "guild_id": guild_id,
            "user_id": user_id,
            "action_type": "spam_check",
            "content_hash": content_hash,
            "timestamp": current_time,
            "expires_at": current_time + self.spam_timeframe  # TTL field
        })
        
        # Count similar messages in timeframe - no await needed for count_documents
        similar_count = collection.count_documents({
            "guild_id": guild_id,
            "user_id": user_id,
            "action_type": "spam_check",
            "content_hash": content_hash,
            "timestamp": {"$gte": current_time - self.spam_timeframe}
        })
        
        # If 5 or more similar messages, issue a warning
        if similar_count >= self.spam_threshold:
            # Don't delete message, just warn
            warning_message = await message.channel.send(
                f"**{message.author.mention} Please stop spamming similar messages ({similar_count} detected).**"
            )
            
            # Add this warning to MongoDB for tracking
            warning_count = await self.client.storage.add_warning(
                str(message.guild.id),
                str(message.author.id),
                "spam"
            )
            
            # Log to moderation channel
            embed_builder = EmbedBuilder(event="auto_moderation")
            await embed_builder.add_field(name="**Action**", value=f"`Spam warning`")
            await embed_builder.add_field(name="**User**", value=f"`{message.author.name}`")
            await embed_builder.add_field(name="**Similar Messages**", value=f"`{similar_count}`")
            await embed_builder.add_field(name="**Warning Count**", value=f"`{warning_count}`")
            embed = await embed_builder.get_embed()
                
            # Use hard-coded log channel ID
            log_channel = message.guild.get_channel(1249380931781791855)
            
            if log_channel:
                await log_channel.send(embed=embed)
                
            # Delete warning after 5 seconds
            await asyncio.sleep(5)
            try:
                await warning_message.delete()
            except:
                pass
            
            # Apply timeouts for repeated offenses
            if warning_count >= 5:
                # Get timeout duration based on warning count
                timeout_duration = await self.client.storage.get_timeout_duration(warning_count)
                if timeout_duration > 0:
                    try:
                        until = discord.utils.utcnow() + datetime.timedelta(seconds=timeout_duration)
                        await message.author.timeout(until, reason=f"Automatic timeout after {warning_count} spam warnings")
                        
                        # Get human-readable duration
                        if timeout_duration == 60:
                            duration_text = "1 minute"
                        elif timeout_duration == 1800:
                            duration_text = "30 minutes"
                        elif timeout_duration == 3600:
                            duration_text = "1 hour"
                        elif timeout_duration == 7200:
                            duration_text = "2 hours"
                        elif timeout_duration == 10800:
                            duration_text = "3 hours"
                        else:
                            duration_text = f"{timeout_duration} seconds"
                            
                        # Send public message about timeout
                        await message.channel.send(
                            f"**{message.author.mention} has been timed out for {duration_text} after receiving {warning_count} warnings.**"
                        )
                    except Exception as e:
                        print(f"Error applying timeout for spam: {e}")
        
    async def check_for_mass_emoji(self, message: discord.Message) -> None:
        """
        Check if a message contains too many emojis and warn the user
        Does not delete the message, only warns the user
        """
        # Count emojis in the message using regex
        emoji_pattern = re.compile(r'<a?:\w+:\d+>|[\U00010000-\U0010ffff]')
        emojis = emoji_pattern.findall(message.content)
        emoji_count = len(emojis)
        
        # Calculate percentage of message that is emojis
        if len(message.content) == 0:
            emoji_percent = 0
        else:
            emoji_chars = sum(len(e) for e in emojis)
            emoji_percent = (emoji_chars / len(message.content)) * 100
        
        if emoji_percent > self.max_emoji_percent:
            # Don't delete message, just warn
            warning_message = await message.channel.send(
                f"**{message.author.mention} Please avoid using too many emojis in your messages. Your message was {emoji_percent:.1f}% emojis.**"
            )
            
            # Add this warning to MongoDB for tracking
            warning_count = await self.client.storage.add_warning(
                str(message.guild.id),
                str(message.author.id),
                "emoji_spam"
            )
            
            # Log to moderation channel
            embed_builder = EmbedBuilder(event="auto_moderation")
            await embed_builder.add_field(name="**Action**", value=f"`Emoji spam warning`")
            await embed_builder.add_field(name="**User**", value=f"`{message.author.name}`")
            await embed_builder.add_field(name="**Emoji Percentage**", value=f"`{emoji_percent:.1f}%`")
            await embed_builder.add_field(name="**Warning Count**", value=f"`{warning_count}`")
            embed = await embed_builder.get_embed()
                
            # Use hard-coded log channel ID
            log_channel = message.guild.get_channel(1249380931781791855)
            
            if log_channel:
                await log_channel.send(embed=embed)
                
            # Delete warning after 5 seconds
            await asyncio.sleep(5)
            try:
                await warning_message.delete()
            except:
                pass
            
            # Apply timeouts for repeated offenses
            if warning_count >= 5:
                # Get timeout duration based on warning count
                timeout_duration = await self.client.storage.get_timeout_duration(warning_count)
                if timeout_duration > 0:
                    try:
                        until = discord.utils.utcnow() + datetime.timedelta(seconds=timeout_duration)
                        await message.author.timeout(until, reason=f"Automatic timeout after {warning_count} emoji spam warnings")
                        
                        # Get human-readable duration
                        if timeout_duration == 60:
                            duration_text = "1 minute"
                        elif timeout_duration == 1800:
                            duration_text = "30 minutes"
                        elif timeout_duration == 3600:
                            duration_text = "1 hour"
                        elif timeout_duration == 7200:
                            duration_text = "2 hours"
                        elif timeout_duration == 10800:
                            duration_text = "3 hours"
                        else:
                            duration_text = f"{timeout_duration} seconds"
                            
                        # Send public message about timeout
                        await message.channel.send(
                            f"**{message.author.mention} has been timed out for {duration_text} after receiving {warning_count} warnings.**"
                        )
                    except Exception as e:
                        print(f"Error applying timeout for emoji spam: {e}")
                        
    async def check_for_excessive_caps(self, message: discord.Message) -> None:
        """
        Check if a message contains too many capital letters and warn the user
        Does not delete the message, only warns the user
        """
        if len(message.content) < 10:  # Ignore short messages
            return
            
        # Count uppercase letters
        uppercase_count = sum(1 for c in message.content if c.isupper())
        letter_count = sum(1 for c in message.content if c.isalpha())
        
        if letter_count == 0:  # Avoid division by zero
            return
            
        caps_percent = (uppercase_count / letter_count) * 100
        
        if caps_percent > self.max_caps_percent:
            # Don't delete message, just warn
            warning_message = await message.channel.send(
                f"**{message.author.mention} Please avoid using excessive caps in your messages. Your message was {caps_percent:.1f}% capital letters.**"
            )
            
            # Add this warning to MongoDB for tracking
            warning_count = await self.client.storage.add_warning(
                str(message.guild.id),
                str(message.author.id),
                "caps_spam"
            )
            
            # Log to moderation channel
            embed_builder = EmbedBuilder(event="auto_moderation")
            await embed_builder.add_field(name="**Action**", value=f"`Excessive caps warning`")
            await embed_builder.add_field(name="**User**", value=f"`{message.author.name}`")
            await embed_builder.add_field(name="**Caps Percentage**", value=f"`{caps_percent:.1f}%`")
            await embed_builder.add_field(name="**Warning Count**", value=f"`{warning_count}`")
            embed = await embed_builder.get_embed()
                
            # Use hard-coded log channel ID
            log_channel = message.guild.get_channel(1249380931781791855)
            
            if log_channel:
                await log_channel.send(embed=embed)
                
            # Delete warning after 5 seconds
            await asyncio.sleep(5)
            try:
                await warning_message.delete()
            except:
                pass
            
            # Apply timeouts for repeated offenses
            if warning_count >= 5:
                # Get timeout duration based on warning count
                timeout_duration = await self.client.storage.get_timeout_duration(warning_count)
                if timeout_duration > 0:
                    try:
                        until = discord.utils.utcnow() + datetime.timedelta(seconds=timeout_duration)
                        await message.author.timeout(until, reason=f"Automatic timeout after {warning_count} excessive caps warnings")
                        
                        # Get human-readable duration
                        if timeout_duration == 60:
                            duration_text = "1 minute"
                        elif timeout_duration == 1800:
                            duration_text = "30 minutes"
                        elif timeout_duration == 3600:
                            duration_text = "1 hour"
                        elif timeout_duration == 7200:
                            duration_text = "2 hours"
                        elif timeout_duration == 10800:
                            duration_text = "3 hours"
                        else:
                            duration_text = f"{timeout_duration} seconds"
                            
                        # Send public message about timeout
                        await message.channel.send(
                            f"**{message.author.mention} has been timed out for {duration_text} after receiving {warning_count} warnings.**"
                        )
                    except Exception as e:
                        print(f"Error applying timeout for excessive caps: {e}")
    
    async def check_for_raid_activity(self, message: discord.Message) -> bool:
        """
        Check if the message is part of a raid (many messages in short time from same user)
        Returns True if raid detected, False otherwise
        """
        # Get user and guild IDs
        user_id = str(message.author.id)
        guild_id = str(message.guild.id)
        
        # Record this message in the database for raid detection
        current_time = time.time()
        
        # Get user's recent message timestamps from temporary actions collection
        collection = self.client.storage.db.temporary_actions
        
        # First, delete any outdated temporary message records (cleanup)
        cutoff_time = current_time - self.raid_timeframe
        # No await needed for delete_many
        collection.delete_many({
            "guild_id": guild_id,
            "user_id": user_id,
            "action_type": "message",
            "timestamp": {"$lt": cutoff_time}
        })
        
        # Add current message - no await needed for insert_one
        collection.insert_one({
            "guild_id": guild_id,
            "user_id": user_id,
            "action_type": "message",
            "timestamp": current_time,
            "expires_at": current_time + self.raid_timeframe  # TTL field
        })
        
        # Count recent messages - no await needed for count_documents
        message_count = collection.count_documents({
            "guild_id": guild_id,
            "user_id": user_id,
            "action_type": "message",
            "timestamp": {"$gte": cutoff_time}
        })
        
        # Check if there are too many messages in the timeframe
        if message_count >= self.raid_threshold:
            # Potential raid detected, timeout user for 5 minutes
            try:
                # Apply timeout
                until = discord.utils.utcnow() + datetime.timedelta(minutes=5)
                await message.author.timeout(until, reason="Anti-raid protection - too many messages")
                
                # Send notification
                await message.channel.send(
                    f"**{message.author.mention} has been timed out for 5 minutes for sending too many messages too quickly (anti-raid protection).**"
                )
                
                # Log the action to MongoDB
                timeout_duration = 5 * 60  # 5 minutes in seconds
                extra_data = {
                    "message_count": message_count,
                    "timeframe": self.raid_timeframe,
                    "threshold": self.raid_threshold
                }
                
                await self.client.storage.log_moderation_action(
                    action_type="anti_raid_timeout",
                    guild_id=str(message.guild.id),
                    user_id=str(message.author.id),
                    moderator_id=str(self.client.user.id),  # Bot is the moderator
                    reason=f"Anti-raid protection - {self.raid_threshold} messages in {self.raid_timeframe} seconds",
                    duration=timeout_duration,
                    extra_data=extra_data
                )
                
                # Also create Discord embed for the log channel
                embed_builder = EmbedBuilder(event="auto_moderation")
                await embed_builder.add_field(name="**Action**", value=f"`Anti-raid timeout`")
                await embed_builder.add_field(name="**User**", value=f"`{message.author.name}`")
                await embed_builder.add_field(name="**Reason**", value=f"`{self.raid_threshold} messages in {self.raid_timeframe} seconds`")
                await embed_builder.add_field(name="**Timeout Duration**", value="`5 minutes`")
                embed = await embed_builder.get_embed()
                
                # Use hard-coded log channel ID
                log_channel = message.guild.get_channel(1249380931781791855)
                
                if log_channel:
                    await log_channel.send(embed=embed)
                    
                return True
                
            except Exception as e:
                print(f"Error applying anti-raid timeout: {e}")
                
        return False


class MessageDeleteEvent(EventHandler):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.client = client_instance
        self.event = "on_message_delete"

    async def handle(self, message: discord.Message, *args, **kwargs) -> None:
        # Ignore deletes of bot messages or messages from ourselves
        if message.author == self.client.user or message.author.bot:
            return
            
        # Only log messages that start with the bot prefix
        if not message.content.lower().startswith(self.client.prefix.lower()):
            return
            
        # Build an embed that will log the deleted message
        embed_builder = EmbedBuilder(event="delete")
        await embed_builder.add_field(name="**Channel**", value=f"`#{message.channel.name}`")
        await embed_builder.add_field(name="**Author**", value=f"`{message.author.name}`")
        await embed_builder.add_field(name="**Message**", value=f"`{message.content}`")
        await embed_builder.add_field(name="**Created at**", value=f"`{message.created_at}`")
        embed = await embed_builder.get_embed()

        # Message the log channel the embed of the deleted message
        guild_id = str(message.guild.id)
        # Use hard-coded log channel ID
        log_channel = discord.utils.get(message.guild.text_channels, id=1249380931781791855)
        if log_channel is not None:
            await log_channel.send(embed=embed)
        else:
            print("No log channel found with that ID")


# Collects a list of classes in the file
classes = inspect.getmembers(sys.modules[__name__], lambda member: inspect.isclass(member) and member.__module__ == __name__)
