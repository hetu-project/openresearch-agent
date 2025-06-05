"""
数据库连接和管理
"""
import asyncio
from typing import Optional
from contextlib import asynccontextmanager
import asyncpg
from asyncpg import Pool
from configs.database_config import database_config
from utils.logger import get_logger

logger = get_logger(__name__)

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.pool: Optional[Pool] = None
        self._initialized = False
    
    async def initialize(self):
        """初始化数据库连接池"""
        if self._initialized:
            return
        
        try:
            logger.info("Initializing database connection pool")
            
            self.pool = await asyncpg.create_pool(
                host=database_config.host,
                port=database_config.port,
                database=database_config.database,
                user=database_config.username,
                password=database_config.password,
                min_size=database_config.min_connections,
                max_size=database_config.max_connections,
                command_timeout=database_config.connection_timeout
            )
            
            # 测试连接
            async with self.pool.acquire() as conn:
                await conn.execute("SELECT 1")
            
            self._initialized = True
            logger.info("Database connection pool initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize database connection pool", error=str(e))
            raise
    
    async def close(self):
        """关闭数据库连接池"""
        if self.pool:
            await self.pool.close()
            self._initialized = False
            logger.info("Database connection pool closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """获取数据库连接的上下文管理器"""
        if not self._initialized:
            await self.initialize()
        
        async with self.pool.acquire() as connection:
            yield connection
    
    async def execute_script(self, script: str):
        """执行SQL脚本"""
        async with self.get_connection() as conn:
            await conn.execute(script)
    
    async def _enable_uuid_extension(self):
        """启用UUID扩展"""
        async with self.get_connection() as conn:
            await conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
            logger.debug("UUID extension enabled")

    async def _create_conversations_table(self):
        """创建会话表"""
        create_conversations_sql = """
        CREATE TABLE IF NOT EXISTS conversations (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id VARCHAR(255) NOT NULL,
            title VARCHAR(500),
            context TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            message_count INTEGER DEFAULT 0,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        async with self.get_connection() as conn:
            await conn.execute(create_conversations_sql)
            logger.debug("Conversations table created")
    
    async def _create_messages_table(self):
        """创建消息表"""
        create_messages_sql = """
        CREATE TABLE IF NOT EXISTS messages (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
            content TEXT NOT NULL,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        async with self.get_connection() as conn:
            await conn.execute(create_messages_sql)
            logger.debug("Messages table created")
    
    async def _create_indexes(self):
        """创建索引"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at);",
            "CREATE INDEX IF NOT EXISTS idx_conversations_active ON conversations(is_active);",
            "CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);",
            "CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role);"
        ]
        
        async with self.get_connection() as conn:
            for index_sql in indexes:
                await conn.execute(index_sql)
                logger.debug(f"Index created: {index_sql}")

    async def _create_triggers(self):
        """创建触发器"""
        # 创建更新时间触发器函数
        trigger_function_sql = """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        """
        
        # 创建触发器
        trigger_sql = """
        DROP TRIGGER IF EXISTS update_conversations_updated_at ON conversations;
        CREATE TRIGGER update_conversations_updated_at
            BEFORE UPDATE ON conversations
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """
        
        async with self.get_connection() as conn:
            await conn.execute(trigger_function_sql)
            await conn.execute(trigger_sql)
            logger.debug("Triggers created")

    async def drop_tables(self):
        """删除所有表（用于测试或重置）"""
        drop_sql = """
        DROP TABLE IF EXISTS messages CASCADE;
        DROP TABLE IF EXISTS conversations CASCADE;
        DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
        """
        
        async with self.get_connection() as conn:
            await conn.execute(drop_sql)
            logger.info("Database tables dropped")

    async def create_tables(self):
        """创建数据表"""
        try:
            logger.info("Creating database tables...")
            
            # 1. 启用UUID扩展
            await self._enable_uuid_extension()
            
            # 2. 创建表
            await self._create_conversations_table()
            await self._create_messages_table()
            
            # 3. 创建索引
            await self._create_indexes()
            
            # 4. 创建触发器
            await self._create_triggers()
            
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error("Failed to create database tables", error=str(e))
            raise

    async def add_missing_columns(self):
        """添加缺失的列（用于数据库迁移）"""
        try:
            async with self.get_connection() as conn:
                # 检查并添加 message_count 列
                await conn.execute("""
                    ALTER TABLE conversations 
                    ADD COLUMN IF NOT EXISTS message_count INTEGER DEFAULT 0;
                """)
                
                # 检查并添加 is_active 列
                await conn.execute("""
                    ALTER TABLE conversations 
                    ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
                """)
                
                # 检查并添加 context 列
                await conn.execute("""
                    ALTER TABLE conversations 
                    ADD COLUMN IF NOT EXISTS context TEXT;
                """)
                
                # 检查并添加 metadata 列
                await conn.execute("""
                    ALTER TABLE conversations 
                    ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';
                """)
                
                logger.info("Missing columns added successfully")
                
        except Exception as e:
            logger.error("Failed to add missing columns", error=str(e))
            raise

# 全局数据库管理器实例
db_manager = DatabaseManager()
