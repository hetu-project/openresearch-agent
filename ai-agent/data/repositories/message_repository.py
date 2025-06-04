"""
消息数据访问层
"""
import json
from typing import List, Optional
from data.database import db_manager
from data.models.message import Message
from utils.logger import get_logger

logger = get_logger(__name__)

class MessageRepository:
    """消息数据访问类"""
    
    async def create(self, message: Message) -> Message:
        """创建新消息"""
        try:
            async with db_manager.get_connection() as conn:
                await conn.execute(
                    """
                    INSERT INTO messages (id, conversation_id, role, content, metadata, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    message.id,
                    message.conversation_id,
                    message.role,
                    message.content,
                    json.dumps(message.metadata),
                    message.created_at
                )
            
            logger.debug("Message created", message_id=message.id, conversation_id=message.conversation_id)
            return message
            
        except Exception as e:
            logger.error("Failed to create message", error=str(e))
            raise
    
    async def get_by_conversation_id(self, conversation_id: str, limit: int = 100) -> List[Message]:
        """获取会话的消息列表"""
        try:
            async with db_manager.get_connection() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, conversation_id, role, content, metadata, created_at
                    FROM messages
                    WHERE conversation_id = $1
                    ORDER BY created_at ASC
                    LIMIT $2
                    """,
                    conversation_id,
                    limit
                )
            
            messages = []
            for row in rows:
                messages.append(Message(
                    id=row["id"],
                    conversation_id=row["conversation_id"],
                    role=row["role"],
                    content=row["content"],
                    metadata=row["metadata"] or {},
                    created_at=row["created_at"]
                ))
            
            return messages
            
        except Exception as e:
            logger.error("Failed to get messages", conversation_id=conversation_id, error=str(e))
            raise
    
    async def delete_by_conversation_id(self, conversation_id: str) -> int:
        """删除会话的所有消息"""
        try:
            async with db_manager.get_connection() as conn:
                result = await conn.execute(
                    """
                    DELETE FROM messages
                    WHERE conversation_id = $1
                    """,
                    conversation_id
                )
            
            deleted_count = int(result.split()[-1])
            logger.info("Messages deleted", conversation_id=conversation_id, count=deleted_count)
            
            return deleted_count
            
        except Exception as e:
            logger.error("Failed to delete messages", conversation_id=conversation_id, error=str(e))
            raise

message_repo = MessageRepository()
