"""
Conversation Service - Database Version
"""
import uuid
import structlog
from typing import Dict, Any, List, Optional
from datetime import datetime

# API Models
from models.conversation import (
    Conversation as ApiConversation, 
    Message as ApiMessage, 
    MessageRole, 
    ConversationWithMessages,
    CreateConversationDTO, 
    CreateMessageDTO
)

# Data Models
from data.models.conversation import Conversation as DataConversation
from data.models.message import Message as DataMessage

from data.repositories.conversation_repository import conversation_repo
from data.repositories.message_repository import message_repo
from utils.id_generator import generate_conversation_id, generate_message_id

logger = structlog.get_logger()

class ConversationService:
    """Conversation Service - Database Version"""
    
    def __init__(self):
        # Using database storage, no longer need memory storage
        pass
    
    def _convert_data_to_api_conversation(self, data_conv: DataConversation) -> ApiConversation:
        """Convert data model to API model"""
        return ApiConversation(
            id=data_conv.id,
            user_id=data_conv.user_id,
            title=data_conv.title,
            context=data_conv.context,
            is_active=data_conv.is_active,
            created_at=data_conv.created_at,
            updated_at=data_conv.updated_at,
            message_count=data_conv.message_count,
            metadata=data_conv.metadata
        )
    
    def _convert_data_to_api_message(self, data_msg: DataMessage) -> ApiMessage:
        """Convert data model to API model"""
        return ApiMessage(
            id=data_msg.id,
            conversation_id=data_msg.conversation_id,
            role=MessageRole(data_msg.role),
            content=data_msg.content,
            created_at=data_msg.created_at,
            metadata=data_msg.metadata
        )
    
    async def create_conversation(self, dto: CreateConversationDTO, user_id: str) -> ApiConversation:
        """Create new conversation"""
        try:
            # Generate conversation ID
            conversation_id = generate_conversation_id()
            
            # Create data model object
            data_conversation = DataConversation(
                id=conversation_id,
                user_id=user_id,
                title=dto.title or "New Conversation",
                context=getattr(dto, 'context', None),
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                message_count=0,
                metadata={}
            )
            
            # Save to database
            await conversation_repo.create(data_conversation)
            
            # If there's an initial message, add it
            if dto.initial_message:
                await self.add_message(CreateMessageDTO(
                    conversation_id=conversation_id,
                    role=MessageRole.USER,
                    content=dto.initial_message
                ))
                # Retrieve updated conversation (including message count)
                data_conversation = await conversation_repo.get_by_id(conversation_id)
            
            logger.info(
                "Conversation created successfully",
                conversation_id=conversation_id,
                title=data_conversation.title,
                user_id=user_id
            )
            
            # Convert to API model and return
            return self._convert_data_to_api_conversation(data_conversation)
            
        except Exception as e:
            logger.error("Failed to create conversation", error=str(e))
            raise
    
    async def get_conversation(self, conversation_id: str) -> Optional[ApiConversation]:
        """Get conversation information"""
        try:
            data_conversation = await conversation_repo.get_by_id(conversation_id)
            if not data_conversation:
                return None
                
            # Convert to API model
            return self._convert_data_to_api_conversation(data_conversation)
        except Exception as e:
            logger.error("Failed to get conversation", conversation_id=conversation_id, error=str(e))
            return None
    
    async def get_conversation_with_messages(self, conversation_id: str) -> Optional[ConversationWithMessages]:
        """Get complete conversation including messages"""
        try:
            api_conversation = await self.get_conversation(conversation_id)
            if not api_conversation:
                return None
            
            data_messages = await message_repo.get_by_conversation_id(conversation_id)
            
            # Convert messages to API model
            api_messages = [self._convert_data_to_api_message(data_msg) for data_msg in data_messages]
            
            return ConversationWithMessages(
                conversation=api_conversation,
                messages=api_messages
            )
        except Exception as e:
            logger.error("Failed to get conversation with messages", conversation_id=conversation_id, error=str(e))
            return None
    
    async def list_conversations(self, user_id: str, limit: int = 20, offset: int = 0) -> List[ApiConversation]:
        """Get user's conversation list"""
        try:
            data_conversations = await conversation_repo.get_by_user_id(user_id, limit, offset)
            
            api_conversations = []
            for data_conv in data_conversations:
                # If no title, generate from first user message
                if not data_conv.title or data_conv.title == "New Conversation":
                    first_messages = await message_repo.get_by_conversation_id(data_conv.id, limit=5)
                    first_user_message = next((msg for msg in first_messages if msg.role == "user"), None)
                    if first_user_message:
                        new_title = first_user_message.content[:20] + ("..." if len(first_user_message.content) > 20 else "")
                        data_conv.title = new_title
                        await conversation_repo.update(data_conv)
                
                # Convert to API model
                api_conversations.append(self._convert_data_to_api_conversation(data_conv))
            
            return api_conversations
            
        except Exception as e:
            logger.error("Failed to list conversations", user_id=user_id, error=str(e))
            return []
    
    async def add_message(self, dto: CreateMessageDTO) -> ApiMessage:
        """Add message"""
        try:
            # Check if conversation exists
            data_conversation = await conversation_repo.get_by_id(dto.conversation_id)
            if not data_conversation:
                raise ValueError(f"Conversation {dto.conversation_id} not found")
            
            # Generate message ID
            message_id = generate_message_id()
            
            # Ensure role is string
            role_str = dto.role.value if hasattr(dto.role, 'value') else str(dto.role)
            
            # Create data model object
            data_message = DataMessage(
                id=message_id,
                conversation_id=dto.conversation_id,
                role=role_str,
                content=dto.content,
                created_at=datetime.now(),
                metadata={}
            )
            
            # Save message to database
            await message_repo.create(data_message)
            
            # Update conversation statistics
            data_conversation.message_count += 1
            data_conversation.updated_at = datetime.now()
            
            # Update conversation title (if it's first user message and no custom title)
            if (role_str == "user" and 
                data_conversation.message_count == 1 and 
                (not data_conversation.title or data_conversation.title == "New Conversation")):
                data_conversation.title = dto.content[:20] + ("..." if len(dto.content) > 20 else "")
            
            await conversation_repo.update(data_conversation)
            
            logger.info(
                "Message added successfully",
                message_id=message_id,
                conversation_id=dto.conversation_id,
                role=role_str
            )
            
            # Convert to API model and return
            return self._convert_data_to_api_message(data_message)
            
        except Exception as e:
            logger.error("Failed to add message", error=str(e))
            raise
    
    async def get_messages(self, conversation_id: str, 
                          limit: int = 50, offset: int = 0) -> List[ApiMessage]:
        """Get conversation messages"""
        try:
            data_messages = await message_repo.get_by_conversation_id(conversation_id, limit, offset)
            return [self._convert_data_to_api_message(data_msg) for data_msg in data_messages]
        except Exception as e:
            logger.error("Failed to get messages", conversation_id=conversation_id, error=str(e))
            return []
    
    async def get_recent_messages(self, conversation_id: str, 
                                 count: int = 10) -> List[ApiMessage]:
        """Get recent messages"""
        try:
            messages = await self.get_messages(conversation_id, limit=count)
            return messages[-count:] if messages else []
        except Exception as e:
            logger.error("Failed to get recent messages", conversation_id=conversation_id, error=str(e))
            return []
    
    async def update_conversation_title(self, conversation_id: str, title: str) -> bool:
        """Update conversation title"""
        try:
            data_conversation = await conversation_repo.get_by_id(conversation_id)
            if not data_conversation:
                return False
            
            data_conversation.title = title
            data_conversation.updated_at = datetime.now()
            await conversation_repo.update(data_conversation)
            
            logger.info(
                "Conversation title updated",
                conversation_id=conversation_id,
                new_title=title
            )
            
            return True
            
        except Exception as e:
            logger.error("Failed to update conversation title", error=str(e))
            return False
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation"""
        try:
            # Delete conversation messages
            await message_repo.delete_by_conversation_id(conversation_id)
            
            # Soft delete conversation
            success = await conversation_repo.delete(conversation_id)
            
            if success:
                logger.info("Conversation deleted successfully", conversation_id=conversation_id)
            
            return success
            
        except Exception as e:
            logger.error("Failed to delete conversation", conversation_id=conversation_id, error=str(e))
            return False
    
    async def get_conversation_history_for_llm(self, conversation_id: str, 
                                             max_messages: int = 10) -> List[Dict[str, str]]:
        """Get conversation history format for LLM"""
        try:
            messages = await self.get_recent_messages(conversation_id, max_messages)
            
            # Convert to LLM format
            llm_messages = []
            for message in messages:
                role = "user" if message.role == MessageRole.USER else "assistant"
                llm_messages.append({
                    "role": role,
                    "content": message.content
                })
            
            return llm_messages
            
        except Exception as e:
            logger.error("Failed to get conversation history for LLM", error=str(e))
            return []
    
    async def search_conversations(self, user_id: str, query: str, limit: int = 10) -> List[ApiConversation]:
        """Search conversations"""
        try:
            # Simple implementation: get all user conversations, then search in memory
            # Production environment should implement full-text search at database level
            all_conversations = await self.list_conversations(user_id, limit=100)
            
            results = []
            query_lower = query.lower()
            
            for conversation in all_conversations:
                # Search title
                if conversation.title and query_lower in conversation.title.lower():
                    results.append(conversation)
                    continue
                
                # Search message content
                messages = await self.get_messages(conversation.id, limit=50)
                for message in messages:
                    if query_lower in message.content.lower():
                        results.append(conversation)
                        break
            
            return results[:limit]
            
        except Exception as e:
            logger.error("Failed to search conversations", error=str(e))
            return []
    
    async def get_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get user statistics"""
        try:
            conversations = await self.list_conversations(user_id, limit=1000)
            total_conversations = len(conversations)
            
            total_messages = 0
            for conversation in conversations:
                messages = await self.get_messages(conversation.id)
                total_messages += len(messages)
            
            # Calculate average message count
            avg_messages = total_messages / total_conversations if total_conversations > 0 else 0
            
            return {
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "avg_messages_per_conversation": round(avg_messages, 2)
            }
            
        except Exception as e:
            logger.error("Failed to get statistics", error=str(e))
            return {}


conversation_service = ConversationService()