"""
ID Generator Utils - MVP Version
"""
import uuid

def generate_conversation_id() -> str:
    """Generate conversation ID - using standard UUID format"""
    return str(uuid.uuid4())

def generate_message_id() -> str:
    """Generate message ID - using standard UUID format"""
    return str(uuid.uuid4())

def generate_task_id() -> str:
    """Generate task ID"""
    return f"task_{uuid.uuid4().hex[:12]}"