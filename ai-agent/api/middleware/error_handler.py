"""
Error handling middleware
"""
from fastapi import FastAPI, HTTPException
from utils.exceptions import (
    BusinessError, 
    business_error_handler,
    http_error_handler,
    general_error_handler
)

def add_error_handlers(app: FastAPI):
    """Add error handlers"""
    
    # Business error handling (including AgentError subclasses)
    app.add_exception_handler(BusinessError, business_error_handler)
    
    # HTTP error handling
    app.add_exception_handler(HTTPException, http_error_handler)
    
    # General error handling
    app.add_exception_handler(Exception, general_error_handler)
