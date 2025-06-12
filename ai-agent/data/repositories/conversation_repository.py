"""
Conversation Data Access Layer
"""
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from data.database import db_manager
from data.models.conversation import Conversation  # Use data.models.conversation
from utils.logger import get_logger

logger = get_logger(__name__)

class ConversationRepository:
    """Conversation Data Access Class"""
    
    def _parse_metadata(self, metadata_value: Any) -> Dict[str, Any]:
        """Parse metadata field"""
        if metadata_value is None:
            return {}
        if isinstance(metadata_value, dict):
            return metadata_value
        if isinstance(metadata_value, str):
            try:
                return json.loads(metadata_value)
            except (json.JSONDecodeError, TypeError):
                logger.warning("Failed to parse metadata JSON", metadata=metadata_value)
                return {}
        return {}
    
    async def create(self, conversation: Conversation) -> Conversation:
        """Create new conversation"""
        try:
            async with db_manager.get_connection() as conn:
                await conn.execute(
                    """
                    INSERT INTO conversations (id, user_id, title, context, created_at, updated_at, is_active, message_count, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                    conversation.id,
                    conversation.user_id,
                    conversation.title,
                    conversation.context,
                    conversation.created_at,
                    conversation.updated_at,
                    conversation.is_active,
                    conversation.message_count,
                    json.dumps(conversation.metadata)
                )
            
            logger.info("Conversation created", conversation_id=conversation.id)
            return conversation
            
        except Exception as e:
            logger.error("Failed to create conversation", error=str(e))
            raise
    
    async def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        try:
            async with db_manager.get_connection() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT id, user_id, title, context, created_at, updated_at, is_active, message_count, metadata
                    FROM conversations
                    WHERE id = $1 AND is_active = TRUE
                    """,
                    conversation_id
                )
            
            if row:
                return Conversation(
                    id=str(row["id"]),
                    user_id=row["user_id"],
                    title=row["title"],
                    context=row["context"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    is_active=row["is_active"],
                    message_count=row["message_count"] or 0,
                    metadata=self._parse_metadata(row["metadata"])  # Fix here
                )
            
            return None
            
        except Exception as e:
            logger.error("Failed to get conversation", conversation_id=conversation_id, error=str(e))
            raise
    
    async def get_by_user_id(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Conversation]:
        """Get user's conversation list"""
        try:
            async with db_manager.get_connection() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, user_id, title, context, created_at, updated_at, is_active, message_count, metadata
                    FROM conversations
                    WHERE user_id = $1 AND is_active = TRUE
                    ORDER BY updated_at DESC
                    LIMIT $2 OFFSET $3
                    """,
                    user_id,
                    limit,
                    offset
                )
            
            conversations = []
            for row in rows:
                conversations.append(Conversation(
                    id=str(row["id"]),
                    user_id=row["user_id"],
                    title=row["title"],
                    context=row["context"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    is_active=row["is_active"],
                    message_count=row["message_count"] or 0,
                    metadata=self._parse_metadata(row["metadata"])  # Fix here
                ))
            
            return conversations
            
        except Exception as e:
            logger.error("Failed to get user conversations", user_id=user_id, error=str(e))
            raise
    
    async def update(self, conversation: Conversation) -> Conversation:
        """Update conversation"""
        try:
            conversation.updated_at = datetime.now()
            
            async with db_manager.get_connection() as conn:
                result = await conn.execute(
                    """
                    UPDATE conversations
                    SET title = $2, context = $3, updated_at = $4, message_count = $5, metadata = $6
                    WHERE id = $1
                    """,
                    conversation.id,
                    conversation.title,
                    conversation.context,
                    conversation.updated_at,
                    conversation.message_count,
                    json.dumps(conversation.metadata)
                )
            
            logger.debug("Conversation updated", conversation_id=conversation.id)
            return conversation
            
        except Exception as e:
            logger.error("Failed to update conversation", conversation_id=conversation.id, error=str(e))
            raise
    
    async def delete(self, conversation_id: str) -> bool:
        """Delete conversation (soft delete)"""
        try:
            async with db_manager.get_connection() as conn:
                result = await conn.execute(
                    """
                    UPDATE conversations
                    SET is_active = FALSE, updated_at = NOW()
                    WHERE id = $1
                    """,
                    conversation_id
                )
            
            # Check if records were updated
            rows_affected = int(result.split()[-1]) if result.split() else 0
            success = rows_affected > 0
            
            if success:
                logger.info("Conversation deleted", conversation_id=conversation_id)
            
            return success
            
        except Exception as e:
            logger.error("Failed to delete conversation", conversation_id=conversation_id, error=str(e))
            raise
    
    async def cleanup_old_conversations(self, days: int = 30) -> int:
        """Clean up old conversations"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            async with db_manager.get_connection() as conn:
                result = await conn.execute(
                    """
                    UPDATE conversations
                    SET is_active = FALSE
                    WHERE updated_at < $1 AND is_active = TRUE
                    """,
                    cutoff_date
                )
            
            # Parse number of updated rows
            rows_affected = int(result.split()[-1]) if result.split() else 0
            logger.info("Old conversations cleaned up", count=rows_affected, days=days)
            
            return rows_affected
            
        except Exception as e:
            logger.error("Failed to cleanup old conversations", error=str(e))
            raise


conversation_repo = ConversationRepository()