"""
Logging middleware
"""
import time
import uuid
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from utils.logger import get_logger

logger = get_logger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Request logging middleware"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Record request start time
        start_time = time.time()
        
        # Record request information
        logger.info(
            "Request started",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Record response information
            logger.info(
                "Request completed",
                request_id=request_id,
                status_code=response.status_code,
                process_time=f"{process_time:.3f}s"
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as exc:
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Record exception information
            logger.error(
                "Request failed",
                request_id=request_id,
                error=str(exc),
                process_time=f"{process_time:.3f}s",
                exc_info=True
            )
            
            raise exc

def add_logging_middleware(app: FastAPI):
    """Add logging middleware"""
    app.add_middleware(LoggingMiddleware)