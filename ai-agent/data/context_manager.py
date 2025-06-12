"""
Simplified Context Manager - Based on PostgreSQL
"""
import uuid
from typing import Optional, List
from data.models.conversation import Conversation
from data.models.message import Message
from .repositories.conversation_repository import conversation_repo
from .repositories.message_repository import message_repo
from data.database import db_manager
from configs.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

class ContextManager:
    """Context Manager"""
    
    async def initialize(self):
        """Initialize context manager"""
        try:
            # Initialize database
            await db_manager.initialize()
            
            # Create database tables
            await db_manager.create_tables()
            
            logger.info("Context manager initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize context manager", error=str(e))
            raise
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation and its messages"""
        try:
            # Get basic conversation information
            conversation = await conversation_repo.get_by_id(conversation_id)
            if not conversation:
                return None
            
            # Get conversation messages - directly use settings configuration
            messages = await message_repo.get_by_conversation_id(
                conversation_id, 
                limit=settings.max_conversation_length
            )
            
            # Add messages to conversation object (need to extend Conversation model)
            conversation.messages = messages
            
            return conversation
            
        except Exception as e:
            logger.error("Failed to get conversation", conversation_id=conversation_id, error=str(e))
            return None
    
    async def create_conversation(self, user_id: str, conversation_id: Optional[str] = None) -> Conversation:
        """Create new conversation"""
        try:
            # If conversation_id is provided, check if it already exists
            if conversation_id:
                existing = await conversation_repo.get_by_id(conversation_id)
                if existing:
                    logger.warning("Conversation already exists", conversation_id=conversation_id)
                    return existing
            
            conversation = Conversation(
                id=conversation_id or str(uuid.uuid4()),
                user_id=user_id
            )
            
            await conversation_repo.create(conversation)
            conversation.messages = []  # Initialize empty message list
            
            logger.info("New conversation created", conversation_id=conversation.id, user_id=user_id)
            return conversation
            
        except Exception as e:
            logger.error("Failed to create conversation", user_id=user_id, error=str(e))
            raise
    
    async def update_conversation(self, conversation: Conversation):
        """Update conversation"""
        try:
            # Update basic conversation information
            await conversation_repo.update(conversation)
            
            # If there are new messages, save them
            if hasattr(conversation, 'messages') and conversation.messages:
                # Get number of existing messages
                existing_messages = await message_repo.get_by_conversation_id(conversation.id)
                existing_count = len(existing_messages)
                
                # Only save new messages
                new_messages = conversation.messages[existing_count:]
                for message in new_messages:
                    message.conversation_id = conversation.id
                    await message_repo.create(message)
            
            logger.debug("Conversation updated", conversation_id=conversation.id)
            
        except Exception as e:
            logger.error("Failed to update conversation", conversation_id=conversation.id, error=str(e))
            raise
    
    async def add_message(self, conversation_id: str, role: str, content: str, metadata: dict = None) -> Message:
        """Add message to conversation"""
        try:
            message = Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                metadata=metadata or {}
            )
            
            await message_repo.create(message)
            
            # Update conversation's update time
            conversation = await conversation_repo.get_by_id(conversation_id)
            if conversation:
                await conversation_repo.update(conversation)
            
            logger.debug("Message added", conversation_id=conversation_id, role=role)
            return message
            
        except Exception as e:
            logger.error("Failed to add message", conversation_id=conversation_id, error=str(e))
            raise
    
    async def get_user_conversations(self, user_id: str, limit: int = 50) -> List[Conversation]:
        """Get user's conversation list"""
        try:
            conversations = await conversation_repo.get_by_user_id(user_id, limit)
            
            # Load recent messages for each conversation as preview
            for conversation in conversations:
                messages = await message_repo.get_by_conversation_id(conversation.id, limit=5)
                conversation.messages = messages
                
                # If no title, generate from first user message
                if not conversation.title and messages:
                    first_user_message = next((msg for msg in messages if msg.role == "user"), None)
                    if first_user_message:
                        conversation.update_title_from_first_message(first_user_message.content)
                        await conversation_repo.update(conversation)
            
            return conversations
            
        except Exception as e:
            logger.error("Failed to get user conversations", user_id=user_id, error=str(e))
            raise
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation"""
        try:
            # Delete conversation messages
            await message_repo.delete_by_conversation_id(conversation_id)
            
            # Soft delete conversation
            success = await conversation_repo.delete(conversation_id)
            
            if success:
                logger.info("Conversation deleted", conversation_id=conversation_id)
            
            return success
            
        except Exception as e:
            logger.error("Failed to delete conversation", conversation_id=conversation_id, error=str(e))
            return False
    
    async def cleanup_old_conversations(self, days: int = 30) -> int:
        """Clean up old conversations"""
        try:
            cleaned_count = await conversation_repo.cleanup_old_conversations(days)
            logger.info("Old conversations cleanup completed", cleaned_count=cleaned_count)
            return cleaned_count
            
        except Exception as e:
            logger.error("Failed to cleanup old conversations", error=str(e))
            return 0
    
    async def get_conversation_stats(self, user_id: str) -> dict:
        """Get user conversation statistics"""
        try:
            conversations = await conversation_repo.get_by_user_id(user_id, limit=1000)
            
            total_conversations = len(conversations)
            total_messages = 0
            
            for conversation in conversations:
                messages = await message_repo.get_by_conversation_id(conversation.id)
                total_messages += len(messages)
            
            return {
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "average_messages_per_conversation": total_messages / total_conversations if total_conversations > 0 else 0
            }
            
        except Exception as e:
            logger.error("Failed to get conversation stats", user_id=user_id, error=str(e))
            return {}
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            await db_manager.close()
            logger.info("Context manager cleanup completed")
            
        except Exception as e:
            logger.error("Error during context manager cleanup", error=str(e))

context_manager = ContextManager()
