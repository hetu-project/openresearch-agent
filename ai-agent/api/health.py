"""
Health check API routes - MVP version
"""
from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any
import asyncio
import time
from datetime import datetime

from services.conversation_service import conversation_service
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy", 
        "service": "ai-agent",
        "version": "1.0.0-mvp",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/health/detailed")
async def detailed_health_check(req: Request):
    """Detailed health check"""
    start_time = time.time()
    health_details = {
        "status": "healthy",
        "service": "ai-agent",
        "version": "1.0.0-mvp",
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    try:
        # Check Agent status
        agent_status = await _check_agent_health(req)
        health_details["checks"]["agent"] = agent_status
        
        # Check ConversationService status
        conversation_status = await _check_conversation_service_health()
        health_details["checks"]["conversation_service"] = conversation_status
        
        # Check memory usage
        memory_status = await _check_memory_health()
        health_details["checks"]["memory"] = memory_status
        
        # Calculate overall health status
        all_healthy = all(
            check.get("status") == "healthy" 
            for check in health_details["checks"].values()
        )
        
        if not all_healthy:
            health_details["status"] = "degraded"
        
        # Add response time
        health_details["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
        
        return health_details
        
    except Exception as e:
        logger.error("Detailed health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "service": "ai-agent",
            "version": "1.0.0-mvp",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "response_time_ms": round((time.time() - start_time) * 1000, 2)
        }

@router.get("/health/readiness")
async def readiness_check(req: Request):
    """Readiness check - for K8s readiness probe"""
    try:
        # Check if key components are ready
        checks = []
        
        # Check if Agent is available
        if hasattr(req.app.state, 'agent') and req.app.state.agent:
            try:
                # Simple agent call test
                await asyncio.wait_for(
                    _test_agent_basic_function(req.app.state.agent), 
                    timeout=5.0
                )
                checks.append(("agent", True))
            except Exception as e:
                logger.warning("Agent readiness check failed", error=str(e))
                checks.append(("agent", False))
        else:
            checks.append(("agent", False))
        
        # Check if ConversationService is available
        try:
            await asyncio.wait_for(
                _test_conversation_service_basic_function(),
                timeout=3.0
            )
            checks.append(("conversation_service", True))
        except Exception as e:
            logger.warning("ConversationService readiness check failed", error=str(e))
            checks.append(("conversation_service", False))
        
        # Return success only if all key components are ready
        all_ready = all(status for _, status in checks)
        
        if all_ready:
            return {
                "status": "ready",
                "service": "ai-agent",
                "checks": dict(checks)
            }
        else:
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "not_ready",
                    "service": "ai-agent", 
                    "checks": dict(checks)
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "service": "ai-agent",
                "error": str(e)
            }
        )

@router.get("/health/liveness")
async def liveness_check():
    """Liveness check - for K8s liveness probe"""
    try:
        # Simple liveness check to ensure process is running
        current_time = datetime.now()
        
        return {
            "status": "alive",
            "service": "ai-agent",
            "timestamp": current_time.isoformat(),
            "uptime_check": "ok"
        }
        
    except Exception as e:
        logger.error("Liveness check failed", error=str(e))
        raise HTTPException(
            status_code=503,
            detail={
                "status": "dead",
                "service": "ai-agent",
                "error": str(e)
            }
        )

# Helper functions
async def _check_agent_health(req: Request) -> Dict[str, Any]:
    """Check Agent health status"""
    try:
        if not hasattr(req.app.state, 'agent') or not req.app.state.agent:
            return {
                "status": "unhealthy",
                "error": "Agent not initialized"
            }
        
        agent = req.app.state.agent
        
        # Try to get agent status
        if hasattr(agent, 'get_agent_status'):
            agent_status = await agent.get_agent_status()
            return {
                "status": "healthy",
                "details": agent_status
            }
        else:
            # Perform basic check if get_agent_status method is not available
            return {
                "status": "healthy",
                "details": {
                    "type": type(agent).__name__,
                    "initialized": True
                }
            }
            
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

async def _check_conversation_service_health() -> Dict[str, Any]:
    """Check ConversationService health status"""
    try:
        # Get statistics to verify service status
        stats = await conversation_service.get_statistics()
        
        return {
            "status": "healthy",
            "details": {
                "total_conversations": stats.get("total_conversations", 0),
                "total_messages": stats.get("total_messages", 0),
                "service_type": "in_memory_storage"
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

async def _check_memory_health() -> Dict[str, Any]:
    """Check memory usage"""
    try:
        import psutil
        import os
        
        # Get memory usage of current process
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        # Set memory usage warning thresholds
        warning_threshold = 80.0  # 80%
        critical_threshold = 95.0  # 95%
        
        status = "healthy"
        if memory_percent > critical_threshold:
            status = "critical"
        elif memory_percent > warning_threshold:
            status = "warning"
        
        return {
            "status": status,
            "details": {
                "memory_usage_mb": round(memory_info.rss / 1024 / 1024, 2),
                "memory_percent": round(memory_percent, 2),
                "warning_threshold": warning_threshold,
                "critical_threshold": critical_threshold
            }
        }
        
    except ImportError:
        # Return basic info if psutil is not available
        return {
            "status": "unknown",
            "details": {
                "error": "psutil not available for memory monitoring"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

async def _test_agent_basic_function(agent) -> bool:
    """Test Agent basic functionality"""
    try:
        required_methods = ['process_query']
        for method in required_methods:
            if not hasattr(agent, method):
                raise Exception(f"Agent missing required method: {method}")
        
        return True
        
    except Exception as e:
        logger.error("Agent basic function test failed", error=str(e))
        raise

async def _test_conversation_service_basic_function() -> bool:
    """Test ConversationService basic functionality"""
    try:
        # Test basic statistics functionality
        await conversation_service.get_statistics()
        return True
        
    except Exception as e:
        logger.error("ConversationService basic function test failed", error=str(e))
        raise