import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

DB_FILE = 'spam_shield.db'

def init_db():
    """Initialize all tables"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            warning_count INTEGER DEFAULT 0,
            is_banned BOOLEAN DEFAULT FALSE,
            banned_until TIMESTAMP,
            reputation_score INTEGER DEFAULT 0
        )
    ''')
    
    # Messages table (for flood detection)
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            chat_id INTEGER,
            message_text TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Settings table (per group)
    c.execute('''
        CREATE TABLE IF NOT EXISTS group_settings (
            chat_id INTEGER PRIMARY KEY,
            is_logging BOOLEAN DEFAULT TRUE,
            auto_ban BOOLEAN DEFAULT TRUE,
            welcome_enabled BOOLEAN DEFAULT TRUE,
            welcome_message TEXT,
            spam_keywords TEXT
        )
    ''')
    
    # Reports table
    c.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reported_user_id INTEGER,
            reported_by INTEGER,
            reason TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved BOOLEAN DEFAULT FALSE
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")

# ===== USER FUNCTIONS =====

def add_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None):
    """Add or update user"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO users 
        (user_id, username, first_name, last_name, join_date)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (user_id, username, first_name, last_name))
    conn.commit()
    conn.close()

def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user data"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            'user_id': row[0],
            'username': row[1],
            'first_name': row[2],
            'last_name': row[3],
            'join_date': row[4],
            'warning_count': row[5],
            'is_banned': row[6],
            'banned_until': row[7],
            'reputation_score': row[8]
        }
    return None

def update_warning(user_id: int):
    """Increment warning count"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        UPDATE users 
        SET warning_count = warning_count + 1 
        WHERE user_id = ?
    ''', (user_id,))
    conn.commit()
    conn.close()

def ban_user(user_id: int, duration_hours: int = 24):
    """Ban user for X hours"""
    banned_until = datetime.now() + timedelta(hours=duration_hours)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        UPDATE users 
        SET is_banned = TRUE, banned_until = ? 
        WHERE user_id = ?
    ''', (banned_until.isoformat(), user_id))
    conn.commit()
    conn.close()

def unban_user(user_id: int):
    """Unban user"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        UPDATE users 
        SET is_banned = FALSE, banned_until = NULL 
        WHERE user_id = ?
    ''', (user_id,))
    conn.commit()
    conn.close()

def update_reputation(user_id: int, delta: int):
    """Update reputation score"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        UPDATE users 
        SET reputation_score = reputation_score + ? 
        WHERE user_id = ?
    ''', (delta, user_id))
    conn.commit()
    conn.close()

# ===== MESSAGE FUNCTIONS =====

def add_message(user_id: int, chat_id: int, message_text: str):
    """Add message to database"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO messages (user_id, chat_id, message_text)
        VALUES (?, ?, ?)
    ''', (user_id, chat_id, message_text))
    conn.commit()
    conn.close()

def get_recent_messages(user_id: int, seconds: int = 5) -> List[Dict[str, Any]]:
    """Get recent messages from user"""
    cutoff = datetime.now() - timedelta(seconds=seconds)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        SELECT message_text, timestamp 
        FROM messages 
        WHERE user_id = ? AND timestamp > ?
        ORDER BY timestamp DESC
    ''', (user_id, cutoff.isoformat()))
    rows = c.fetchall()
    conn.close()
    return [{'text': r[0], 'timestamp': r[1]} for r in rows]

def clear_old_messages(days: int = 7):
    """Clear messages older than X days"""
    cutoff = datetime.now() - timedelta(days=days)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM messages WHERE timestamp < ?', (cutoff.isoformat(),))
    conn.commit()
    conn.close()

# ===== GROUP SETTINGS =====

def get_group_settings(chat_id: int) -> Dict[str, Any]:
    """Get group settings"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM group_settings WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return {
            'chat_id': row[0],
            'is_logging': row[1],
            'auto_ban': row[2],
            'welcome_enabled': row[3],
            'welcome_message': row[4],
            'spam_keywords': row[5]
        }
    
    # Default settings
    return {
        'chat_id': chat_id,
        'is_logging': True,
        'auto_ban': True,
        'welcome_enabled': True,
        'welcome_message': None,
        'spam_keywords': None
    }

def update_group_settings(chat_id: int, **kwargs):
    """Update group settings"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Check if exists
    c.execute('SELECT chat_id FROM group_settings WHERE chat_id = ?', (chat_id,))
    exists = c.fetchone()
    
    if exists:
        query = 'UPDATE group_settings SET '
        query += ', '.join([f'{k} = ?' for k in kwargs.keys()])
        query += ' WHERE chat_id = ?'
        c.execute(query, list(kwargs.values()) + [chat_id])
    else:
        keys = ', '.join(kwargs.keys())
        placeholders = ', '.join(['?'] * len(kwargs))
        query = f'INSERT INTO group_settings (chat_id, {keys}) VALUES (?, {placeholders})'
        c.execute(query, [chat_id] + list(kwargs.values()))
    
    conn.commit()
    conn.close()

# ===== REPORTS =====

def add_report(reported_user_id: int, reported_by: int, reason: str):
    """Add spam report"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO reports (reported_user_id, reported_by, reason)
        VALUES (?, ?, ?)
    ''', (reported_user_id, reported_by, reason))
    conn.commit()
    conn.close()

def get_reports(user_id: int = None) -> List[Dict[str, Any]]:
    """Get reports (all or for specific user)"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    if user_id:
        c.execute('''
            SELECT id, reported_user_id, reported_by, reason, timestamp, resolved
            FROM reports 
            WHERE reported_user_id = ? AND resolved = FALSE
            ORDER BY timestamp DESC
        ''', (user_id,))
    else:
        c.execute('''
            SELECT id, reported_user_id, reported_by, reason, timestamp, resolved
            FROM reports 
            WHERE resolved = FALSE
            ORDER BY timestamp DESC
        ''')
    
    rows = c.fetchall()
    conn.close()
    return [{
        'id': r[0],
        'reported_user_id': r[1],
        'reported_by': r[2],
        'reason': r[3],
        'timestamp': r[4],
        'resolved': r[5]
    } for r in rows]

def resolve_report(report_id: int):
    """Mark report as resolved"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('UPDATE reports SET resolved = TRUE WHERE id = ?', (report_id,))
    conn.commit()
    conn.close()
