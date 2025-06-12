"""
Chat related API routes
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Optional

from models.request import ChatRequest
from models.response import ChatResponse
from models.conversation import CreateConversationDTO, CreateMessageDTO, MessageRole
from services.conversation_service import conversation_service
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, req: Request) -> ChatResponse:
    """Handle chat request"""
    try:
        agent = req.app.state.agent
        logger.info("Received chat request", 
                   user_id=request.user_id,
                   conversation_id=request.conversation_id)
        
        # Create new conversation if conversation_id is not provided
        conversation_id = request.conversation_id
        if not conversation_id:
            conversation_dto = CreateConversationDTO(
                title=None,  # Will be auto-generated based on first message
                initial_message=request.message
            )
            conversation = await conversation_service.create_conversation(
                dto=conversation_dto,
                user_id=request.user_id
            )
            conversation_id = conversation.id
        else:
            # Check if conversation exists, create if not
            existing_conversation = await conversation_service.get_conversation(conversation_id)
            if not existing_conversation:
                logger.info("Conversation not found, creating new one", conversation_id=conversation_id)
                conversation_dto = CreateConversationDTO(
                    title=None,
                    initial_message=request.message
                )
                conversation = await conversation_service.create_conversation(
                    dto=conversation_dto,
                    user_id=request.user_id
                )
                conversation_id = conversation.id
            else:
                # Add user message to existing conversation
                await conversation_service.add_message(CreateMessageDTO(
                    conversation_id=conversation_id,
                    role=MessageRole.USER,
                    content=request.message
                ))
        
        # Process query using agent
        result = await agent.process_query(
            query=request.message,
            conversation_id=conversation_id,
            user_id=request.user_id
        )
        
        # Add AI response to conversation
        await conversation_service.add_message(CreateMessageDTO(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=result["content"]
        ))
        
        return ChatResponse(
            message=result["content"],
            conversation_id=conversation_id,
            query_id=result.get("query_id"),
            metadata=result.get("metadata", {}),
            processing_time=result.get("processing_time", 0)
        )
        
    except Exception as e:
        logger.error("Chat request failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, req: Request):
    """Streaming chat response (future extension)"""
    logger.info("Stream chat request received but not implemented", 
               conversation_id=request.conversation_id)
    
    raise HTTPException(
        status_code=501, 
        detail="Streaming chat not implemented yet. Please use /chat endpoint instead."
    )
