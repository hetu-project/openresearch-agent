"""
Data Access Layer Package - Unified Data Access Interface
"""

# Database Management
from .database import db_manager

# Data Models
from .models import Conversation, Message

# Data Access Layer
from .repositories.conversation_repository import conversation_repo
from .repositories.message_repository import message_repo

# Context Manager
from .context_manager import ContextManager

from configs.database_config import database_config
from utils.logger import get_logger

logger = get_logger(__name__)

# Create global context manager instance
context_manager = ContextManager()

__all__ = [
    # Database Management
    "db_manager",
    
    # Data Models
    "Conversation",
    "Message",
    
    # Data Access Layer
    "conversation_repo",
    "message_repo",
    
    # Context Management
    "ContextManager",
    "context_manager",
]

# Version Information
__version__ = "1.0.0-mvp"

# Data Layer Initialization Function
async def initialize_data_layer():
    """Initialize Data Access Layer"""
    try:
        # if database_config.skip_in_dev:
        #     logger.info("Skip database initialization in development environment")
        #     await context_manager.initialize_memory_only()
        #     return True

        # Initialize database connection
        await db_manager.initialize()
        
        # Create data tables
        await db_manager.create_tables()
        
        # Initialize context manager
        await context_manager.initialize()
        
        return True
        
    except Exception as e:
        logger.error("Failed to initialize data layer", error=str(e))
        return False

async def cleanup_data_layer():
    """Cleanup Data Access Layer Resources"""
    try:
        # Cleanup context manager
        await context_manager.cleanup()
        
        # Close database connection
        await db_manager.close()
        
        return True
        
    except Exception as e:
        print(f"Failed to cleanup data layer: {e}")
        return False