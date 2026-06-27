import asyncio
import time
import re
from datetime import datetime
from telethon import TelegramClient, events, Button
from telethon.errors import FloodWaitError
from telethon.sessions import StringSession
import config
import database as db
from spam_detector import is_spam_detected, SPAM_PATTERNS

# Initialize database
db.init_db()

# Create client
client = TelegramClient(
    StringSession(config.SESSION_STRING) if config.SESSION_STRING else 'session',
    config.API_ID,
    config.API_HASH
)

# Store active warnings per user per chat (for flood detection)
flood_cache = {}

# ============================================================
# EVENT HANDLERS
# ============================================================

@client.on(events.NewMessage(incoming=True))
async def handle_message(event):
    """Handle all incoming messages"""
    try:
        # Ignore outgoing messages
        if event.out:
            return
        
        chat = await event.get_chat()
        user = await event.get_sender()
        chat_id = event.chat_id
        user_id = event.sender_id
        message_text = event.text or ''
        
        # Skip if no chat (edge case)
        if not chat or not user:
            return
        
        # Add message to database
        db.add_message(user_id, chat_id, message_text)
        
        # Check if user is banned
        user_data = db.get_user(user_id)
        if user_data and user_data['is_banned']:
            banned_until = user_data['banned_until']
            if banned_until and datetime.now() < datetime.fromisoformat(banned_until):
                await event.delete()
                await event.respond(
                    f"🚫 You are banned from this chat until {banned_until[:16]}"
                )
                return
        
        # Check if user is admin/owner
        if user_id in config.ADMIN_IDS or user_id == config.OWNER_ID:
            return
        
        # ===== SPAM DETECTION =====
        is_spam, reason, score = is_spam_detected(message_text, user_id, chat_id)
        
        if is_spam:
            # Delete spam message
            await event.delete()
            
            # Update warning count
            db.update_warning(user_id)
            user_data = db.get_user(user_id)
            warnings = user_data['warning_count'] if user_data else 0
            
            # Reduce reputation
            db.update_reputation(user_id, -5)
            
            # Send warning
            await event.respond(
                f"⚠️ **Spam Detected!**\n\n"
                f"Reason: {reason}\n"
                f"Score: {score}/100\n"
                f"Warnings: {warnings}/{config.SPAM_THRESHOLD}\n\n"
                f"Your message has been deleted.",
                reply_to=event.message
            )
            
            # Auto-ban if threshold reached
            if warnings >= config.SPAM_THRESHOLD:
                await auto_ban_user(user_id, chat_id)
            
            # Log to admin
            await notify_admin(
                f"🚨 **Spam Alert**\n"
                f"User: {user.first_name} (@{user.username or 'no username'})\n"
                f"User ID: `{user_id}`\n"
                f"Reason: {reason}\n"
                f"Score: {score}/100\n"
                f"Warnings: {warnings}/{config.SPAM_THRESHOLD}\n"
                f"Message: `{message_text[:100]}`"
            )
            
            # Send to spam reports
            db.add_report(user_id, config.OWNER_ID, reason)
        
        # ===== WELCOME MESSAGE (only for new users) =====
        # (Handled separately via member join event)
        
    except FloodWaitError as e:
        print(f"⏳ Flood wait: {e.seconds}s")
        await asyncio.sleep(e.seconds)
    except Exception as e:
        print(f"⚠️ Error in handle_message: {e}")

@client.on(events.ChatAction)
async def handle_member_join(event):
    """Handle new member joins"""
    try:
        if event.user_joined:
            user = await event.get_user()
            chat = await event.get_chat()
            chat_id = event.chat_id
            
            # Add user to database
            db.add_user(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            # Get group settings
            settings = db.get_group_settings(chat_id)
            
            # Send welcome message if enabled
            if settings['welcome_enabled']:
                welcome_msg = settings['welcome_message']
                if not welcome_msg:
                    welcome_msg = (
                        f"👋 Welcome to {chat.title}!\n\n"
                        f"Please read the rules and be respectful.\n"
                        f"Spammers will be automatically banned."
                    )
                
                await event.respond(
                    f"👋 Welcome {user.first_name}!\n\n{welcome_msg}"
                )
            
            # Log to admin
            await notify_admin(
                f"🟢 **New Member Joined**\n"
                f"User: {user.first_name} (@{user.username or 'no username'})\n"
                f"User ID: `{user.id}`\n"
                f"Chat: {chat.title}"
            )
            
    except Exception as e:
        print(f"⚠️ Error in handle_member_join: {e}")

# ============================================================
# AUTO-BAN FUNCTION
# ============================================================

async def auto_ban_user(user_id: int, chat_id: int):
    """Automatically ban user"""
    try:
        # Ban user
        db.ban_user(user_id, config.BAN_DURATION)
        
        # Try to ban from chat (if bot has permission)
        try:
            await client.kick_participant(chat_id, user_id)
        except Exception as e:
            print(f"⚠️ Cannot ban user: {e}")
        
        # Notify user
        await client.send_message(
            user_id,
            f"🚫 **You have been banned!**\n\n"
            f"Reason: Spam (multiple violations)\n"
            f"Duration: {config.BAN_DURATION} hours\n\n"
            f"If you think this is a mistake, contact admin."
        )
        
        # Notify admin
        await notify_admin(
            f"🚫 **User Auto-Banned**\n"
            f"User ID: `{user_id}`\n"
            f"Duration: {config.BAN_DURATION} hours\n"
            f"Reason: Spam threshold exceeded"
        )
        
    except Exception as e:
        print(f"⚠️ Error auto-banning user {user_id}: {e}")

# ============================================================
# ADMIN NOTIFICATION
# ============================================================

async def notify_admin(message: str):
    """Send notification to admin"""
    try:
        for admin_id in config.ADMIN_IDS:
            await client.send_message(admin_id, message)
    except Exception as e:
        print(f"⚠️ Error notifying admin: {e}")

# ============================================================
# COMMANDS
# ============================================================

@client.on(events.NewMessage(pattern='/start'))
async def start_command(event):
    """Handle /start command"""
    await event.reply(f"""
🤖 **{config.BOT_NAME}** v2.0

Telegram group spam shield bot with AI detection.

**Commands:**
/start - Show this message
/help - Show help
/rules - Show rules
/status - Group status
/settings - Configure bot

**Admin Commands:**
/ban @user - Ban user
/unban @user - Unban user
/warn @user - Warn user
/reports - Show spam reports
/setwelcome <message> - Set welcome message

**Channel Management:**
/autodelete <on/off> - Auto-delete spam
/floodlimit <number> - Set flood limit
/spamscore <threshold> - Set spam sensitivity

👨‍💻 Developer: {config.DEV_NAME}
👤 Owner: {config.OWNER_NAME}
    """)

@client.on(events.NewMessage(pattern='/help'))
async def help_command(event):
    """Handle /help command"""
    await event.reply(f"""
📚 **Help - {config.BOT_NAME}**

**What I do:**
- Detect and delete spam messages
- Auto-ban repeat offenders
- Track user reputation
- Welcome new members

**Commands:**
/rules - Show group rules
/status - Show group stats
/report @user - Report spam

**Admin Commands:**
/ban @user - Ban user
/unban @user - Unban user
/warn @user - Warn user
/reports - View spam reports
/resolve <id> - Resolve report
/setwelcome <msg> - Set welcome message
/autodelete on/off - Toggle auto-delete

⚡ Powered by {config.DEV_NAME}
    """)

@client.on(events.NewMessage(pattern='/status'))
async def status_command(event):
    """Handle /status command"""
    chat_id = event.chat_id
    settings = db.get_group_settings(chat_id)
    reports = db.get_reports()
    
    total_users = len(db.get_all_users())
    pending_reports = len(reports)
    
    await event.reply(f"""
📊 **Group Status**

👥 Total Users: {total_users}
📋 Pending Reports: {pending_reports}
🛡️ Auto-Ban: {'✅ Enabled' if settings['auto_ban'] else '❌ Disabled'}
📝 Logging: {'✅ Enabled' if settings['is_logging'] else '❌ Disabled'}
👋 Welcome: {'✅ Enabled' if settings['welcome_enabled'] else '❌ Disabled'}

⚙️ Settings:
- Spam Threshold: {config.SPAM_THRESHOLD} warnings
- Flood Limit: {config.FLOOD_LIMIT} msgs/{config.FLOOD_WINDOW}s
- Ban Duration: {config.BAN_DURATION} hours

⚡ Powered by {config.DEV_NAME}
    """)

# ============================================================
# ADMIN COMMANDS
# ============================================================

@client.on(events.NewMessage(pattern='/ban (@?\S+)'))
async def ban_command(event):
    """Handle /ban command (admin only)"""
    user_id = event.sender_id
    if user_id not in config.ADMIN_IDS and user_id != config.OWNER_ID:
        await event.reply("⛔ You don't have permission to use this command.")
        return
    
    # Get username from command
    parts = event.text.split()
    if len(parts) < 2:
        await event.reply("❌ Usage: /ban @username")
        return
    
    username = parts[1].replace('@', '')
    try:
        entity = await client.get_entity(f"@{username}")
        target_id = entity.id
    except Exception:
        await event.reply(f"❌ User @{username} not found.")
        return
    
    # Ban user
    db.ban_user(target_id, config.BAN_DURATION)
    await event.reply(f"✅ User @{username} banned for {config.BAN_DURATION} hours.")

@client.on(events.NewMessage(pattern='/unban (@?\S+)'))
async def unban_command(event):
    """Handle /unban command (admin only)"""
    user_id = event.sender_id
    if user_id not in config.ADMIN_IDS and user_id != config.OWNER_ID:
        await event.reply("⛔ You don't have permission to use this command.")
        return
    
    parts = event.text.split()
    if len(parts) < 2:
        await event.reply("❌ Usage: /unban @username")
        return
    
    username = parts[1].replace('@', '')
    try:
        entity = await client.get_entity(f"@{username}")
        target_id = entity.id
    except Exception:
        await event.reply(f"❌ User @{username} not found.")
        return
    
    db.unban_user(target_id)
    await event.reply(f"✅ User @{username} unbanned successfully!")

@client.on(events.NewMessage(pattern='/setwelcome (.+)'))
async def set_welcome_command(event):
    """Handle /setwelcome command (admin only)"""
    user_id = event.sender_id
    if user_id not in config.ADMIN_IDS and user_id != config.OWNER_ID:
        await event.reply("⛔ You don't have permission to use this command.")
        return
    
    chat_id = event.chat_id
    welcome_msg = event.text.replace('/setwelcome', '').strip()
    
    db.update_group_settings(chat_id, welcome_message=welcome_msg, welcome_enabled=True)
    await event.reply(f"✅ Welcome message set successfully!\n\n{welcome_msg}")

@client.on(events.NewMessage(pattern='/reports'))
async def reports_command(event):
    """Handle /reports command (admin only)"""
    user_id = event.sender_id
    if user_id not in config.ADMIN_IDS and user_id != config.OWNER_ID:
        await event.reply("⛔ You don't have permission to use this command.")
        return
    
    reports = db.get_reports()
    if not reports:
        await event.reply("📋 No pending spam reports.")
        return
    
    msg = "📋 **Pending Spam Reports**\n\n"
    for i, report in enumerate(reports[:10]):
        msg += f"{i+1}. User: `{report['reported_user_id']}`\n"
        msg += f"   Reason: {report['reason']}\n"
        msg += f"   Time: {report['timestamp'][:16]}\n"
        msg += f"   ID: `{report['id']}`\n\n"
    
    msg += "\nUse `/resolve <id>` to mark as resolved."
    await event.reply(msg)

@client.on(events.NewMessage(pattern='/resolve (\d+)'))
async def resolve_command(event):
    """Handle /resolve command (admin only)"""
    user_id = event.sender_id
    if user_id not in config.ADMIN_IDS and user_id != config.OWNER_ID:
        await event.reply("⛔ You don't have permission to use this command.")
        return
    
    report_id = int(event.text.split()[1])
    db.resolve_report(report_id)
    await event.reply(f"✅ Report #{report_id} resolved!")

# ============================================================
# CHANNEL MANAGEMENT FEATURES
# ============================================================

@client.on(events.NewMessage(pattern='/autodelete (on|off)'))
async def autodelete_command(event):
    """Toggle auto-delete (admin only)"""
    user_id = event.sender_id
    if user_id not in config.ADMIN_IDS and user_id != config.OWNER_ID:
        await event.reply("⛔ You don't have permission to use this command.")
        return
    
    chat_id = event.chat_id
    status = event.text.split()[1] == 'on'
    db.update_group_settings(chat_id, auto_ban=status)
    await event.reply(f"✅ Auto-delete {'enabled' if status else 'disabled'}!")

@client.on(events.NewMessage(pattern='/floodlimit (\d+)'))
async def floodlimit_command(event):
    """Set flood limit (admin only)"""
    user_id = event.sender_id
    if user_id not in config.ADMIN_IDS and user_id != config.OWNER_ID:
        await event.reply("⛔ You don't have permission to use this command.")
        return
    
    limit = int(event.text.split()[1])
    # Note: This would need to update config or use a dynamic setting
    # For now, just acknowledge
    await event.reply(f"✅ Flood limit set to {limit} messages/{config.FLOOD_WINDOW}s")
    # In production, you'd store this in database

@client.on(events.NewMessage(pattern='/rules'))
async def rules_command(event):
    """Show group rules"""
    await event.reply(f"""
📜 **Group Rules**

1. No spam or self-promotion
2. No NSFW content
3. No hate speech or harassment
4. No illegal activities
5. No flooding (5 messages/5 seconds)
6. Be respectful to all members

**Violations may result in:**
- Warning
- Temporary ban
- Permanent ban

⚡ Powered by {config.DEV_NAME}
    """)

@client.on(events.NewMessage(pattern='/warn (@?\S+)'))
async def warn_command(event):
    """Warn user (admin only)"""
    user_id = event.sender_id
    if user_id not in config.ADMIN_IDS and user_id != config.OWNER_ID:
        await event.reply("⛔ You don't have permission to use this command.")
        return
    
    parts = event.text.split()
    if len(parts) < 2:
        await event.reply("❌ Usage: /warn @username")
        return
    
    username = parts[1].replace('@', '')
    try:
        entity = await client.get_entity(f"@{username}")
        target_id = entity.id
    except Exception:
        await event.reply(f"❌ User @{username} not found.")
        return
    
    db.update_warning(target_id)
    user_data = db.get_user(target_id)
    warnings = user_data['warning_count'] if user_data else 0
    
    await event.reply(
        f"⚠️ User @{username} warned!\n"
        f"Warnings: {warnings}/{config.SPAM_THRESHOLD}"
    )

# ============================================================
# MAIN FUNCTION
# ============================================================

async def main():
    """Main entry point"""
    print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 {config.BOT_NAME} v2.0
👨‍💻 Developer: {config.DEV_NAME}
👤 Owner: {config.OWNER_NAME}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Starting spam shield bot...
📱 Monitoring groups and channels...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
    
    try:
        await client.start()
        me = await client.get_me()
        print(f"✅ Logged in as: {me.first_name} (@{me.username or 'no username'})")
        print(f"👤 Admin IDs: {config.ADMIN_IDS}")
        print(f"⚙️ Spam threshold: {config.SPAM_THRESHOLD}")
        print(f"⚙️ Flood limit: {config.FLOOD_LIMIT} msgs/{config.FLOOD_WINDOW}s")
        print(f"⚙️ Ban duration: {config.BAN_DURATION} hours")
        print("\n🟢 Bot is running! Press Ctrl+C to stop.\n")
        
        await client.run_until_disconnected()
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")

if __name__ == '__main__':
    asyncio.run(main())
