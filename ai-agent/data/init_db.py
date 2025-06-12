"""
Database initialization script
"""
import asyncio
from data.database import db_manager
from utils.logger import get_logger

logger = get_logger(__name__)

async def init_database():
    """Initialize database"""
    try:
        logger.info("Starting database initialization")
        
        # Initialize connection pool
        await db_manager.initialize()
        
        # Create tables
        await db_manager.create_tables()
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        raise
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(init_database())