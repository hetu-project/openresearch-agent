"""
Conversation Management API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import List, Optional

from models.response import ConversationResponse, ConversationListResponse
from services.conversation_service import conversation_service
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.get("/conversations", response_model=ConversationListResponse)
async def get_user_conversations(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(20, description="Return limit"),
    offset: int = Query(0, description="Offset")
) -> ConversationListResponse:
    """Get user's conversation list"""
    try:
        logger.info("Getting user conversations", user_id=user_id, limit=limit, offset=offset)
        
        conversations = await conversation_service.list_conversations(
            user_id=user_id, 
            limit=limit, 
            offset=offset
        )
        
        return ConversationListResponse(
            conversations=conversations,
            total=len(conversations)
        )
        
    except Exception as e:
        logger.error("Failed to get user conversations", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    include_messages: bool = Query(True, description="Whether to include message list")
) -> ConversationResponse:
    """Get conversation details"""
    try:
        logger.info("Getting conversation", conversation_id=conversation_id, include_messages=include_messages)
        
        if include_messages:
            conversation_with_messages = await conversation_service.get_conversation_with_messages(conversation_id)
            if not conversation_with_messages:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            return ConversationResponse(
                conversation=conversation_with_messages.conversation,
                messages=conversation_with_messages.messages
            )
        else:
            conversation = await conversation_service.get_conversation(conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            return ConversationResponse(conversation=conversation)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get conversation", conversation_id=conversation_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str
):
    """Delete conversation"""
    try:
        logger.info("Deleting conversation", conversation_id=conversation_id)
        
        success = await conversation_service.delete_conversation(conversation_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {"message": "Conversation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete conversation", conversation_id=conversation_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/conversations/{conversation_id}/title")
async def update_conversation_title(
    conversation_id: str,
    title: str = Query(..., description="New conversation title")
):
    """Update conversation title"""
    try:
        logger.info("Updating conversation title", conversation_id=conversation_id, title=title)
        
        success = await conversation_service.update_conversation_title(conversation_id, title)
        
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {"message": "Conversation title updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update conversation title", conversation_id=conversation_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    limit: int = Query(50, description="Message return limit"),
    offset: int = Query(0, description="Offset")
):
    """Get conversation message list"""
    try:
        logger.info("Getting conversation messages", 
                   conversation_id=conversation_id, 
                   limit=limit, 
                   offset=offset)
        
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        messages = await conversation_service.get_messages(
            conversation_id=conversation_id,
            limit=limit,
            offset=offset
        )
        
        return {
            "messages": messages,
            "total": len(messages),
            "conversation_id": conversation_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get conversation messages", 
                    conversation_id=conversation_id, 
                    error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/search")
async def search_conversations(
    user_id: str = Query(..., description="User ID"),
    query: str = Query(..., description="Search keyword"),
    limit: int = Query(10, description="Return limit")
):
    """Search user conversations"""
    try:
        logger.info("Searching conversations", user_id=user_id, query=query, limit=limit)
        
        conversations = await conversation_service.search_conversations(
            user_id=user_id,
            query=query,
            limit=limit
        )
        
        return {
            "conversations": conversations,
            "total": len(conversations),
            "query": query
        }
        
    except Exception as e:
        logger.error("Failed to search conversations", 
                    user_id=user_id, 
                    query=query, 
                    error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/statistics")
async def get_conversation_statistics(
    user_id: str = Query(..., description="User ID")
):
    """Get user conversation statistics"""
    try:
        logger.info("Getting conversation statistics", user_id=user_id)
        
        statistics = await conversation_service.get_statistics(user_id)
        
        return {
            "user_id": user_id,
            "statistics": statistics
        }
        
    except Exception as e:
        logger.error("Failed to get conversation statistics", 
                    user_id=user_id, 
                    error=str(e))
        raise HTTPException(status_code=500, detail=str(e))