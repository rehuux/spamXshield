import re
import time
from datetime import datetime
from typing import List, Tuple
import config
from database import get_recent_messages, update_reputation

# Common spam patterns
SPAM_PATTERNS = [
    r'https?://\S+',  # URLs
    r't\.me/\S+',     # Telegram links
    r'@\S+',          # Mentions
    r'\b(buy|sell|free|offer|discount|giveaway)\b',  # Keywords
    r'\b(click here|subscribe|follow|like|share)\b',  # Action words
    r'\d{10,}',       # Phone numbers
    r'\$\d+',         # Money amounts
]

def is_spam(text: str) -> Tuple[bool, str]:
    """
    Check if message is spam
    Returns: (is_spam, reason)
    """
    text_lower = text.lower()
    
    # Check for URL patterns
    url_pattern = r'https?://\S+|t\.me/\S+'
    if re.search(url_pattern, text_lower):
        return True, "URL/Telegram link detected"
    
    # Check for spam keywords
    for pattern in SPAM_PATTERNS:
        if re.search(pattern, text_lower):
            return True, f"Suspicious keyword pattern detected"
    
    # Check for excessive caps (more than 70% uppercase)
    caps_count = sum(1 for c in text if c.isupper())
    if caps_count > len(text) * 0.7 and len(text) > 10:
        return True, "Excessive CAPS detected"
    
    # Check for repeated characters
    if re.search(r'(.)\1{4,}', text):
        return True, "Repeated characters detected"
    
    return False, "Clean"

def is_flooding(user_id: int, chat_id: int) -> Tuple[bool, int]:
    """
    Check if user is flooding
    Returns: (is_flooding, message_count)
    """
    recent_msgs = get_recent_messages(user_id, config.FLOOD_WINDOW)
    count = len(recent_msgs)
    
    if count >= config.FLOOD_LIMIT:
        return True, count
    
    return False, count

def calculate_spam_score(text: str) -> int:
    """
    Calculate spam score (0-100)
    Higher = more likely spam
    """
    score = 0
    text_lower = text.lower()
    
    # Check URLs
    if re.search(r'https?://', text_lower):
        score += 20
    if re.search(r't\.me/', text_lower):
        score += 15
    
    # Check spam keywords
    for keyword in config.SPAM_KEYWORDS:
        if keyword in text_lower:
            score += 10
    
    # Check caps
    caps_percent = sum(1 for c in text if c.isupper()) / max(len(text), 1) * 100
    if caps_percent > 70:
        score += 15
    
    # Check repeated chars
    if re.search(r'(.)\1{4,}', text):
        score += 10
    
    # Check length
    if len(text) < 3:
        score += 5
    
    return min(score, 100)

def is_spam_detected(text: str, user_id: int, chat_id: int) -> Tuple[bool, str, int]:
    """
    Comprehensive spam detection
    Returns: (is_spam, reason, spam_score)
    """
    reasons = []
    score = 0
    
    # Check spam content
    is_spam_msg, reason = is_spam(text)
    if is_spam_msg:
        reasons.append(reason)
        score += 30
    
    # Calculate spam score
    score += calculate_spam_score(text)
    
    # Check flooding
    is_flood, count = is_flooding(user_id, chat_id)
    if is_flood:
        reasons.append(f"Flood detected ({count} messages in {config.FLOOD_WINDOW}s)")
        score += 20
    
    # Check reputation score
    from database import get_user
    user = get_user(user_id)
    if user and user['reputation_score'] < -5:
        reasons.append("Low reputation score")
        score += 15
    
    # Determine if spam
    is_spam = score >= config.SPAM_CONFIDENCE_THRESHOLD * 100
    reason = ' | '.join(reasons) if reasons else 'Clean'
    
    return is_spam, reason, score
