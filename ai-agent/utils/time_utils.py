"""
Time utilities - MVP version
"""
import time
from datetime import datetime, timezone

def now() -> datetime:
    """Get current UTC time"""
    return datetime.now(timezone.utc)

def now_ms() -> int:
    """Get current timestamp in milliseconds"""
    return int(time.time() * 1000)