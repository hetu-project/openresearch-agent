import asyncio
from data.database import db_manager

async def migrate():
    try:
        print("Starting database migration...")
        await db_manager.initialize()
        await db_manager.add_missing_columns()
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(migrate())