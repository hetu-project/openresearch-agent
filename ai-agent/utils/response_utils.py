"""
Response Tools - MVP Version
"""
from typing import Any, Dict
from fastapi import HTTPException
from utils.time_utils import now_ms

def success_response(data: Any = None, message: str = "Operation successful") -> Dict[str, Any]:
    """Success response"""
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": now_ms()
    }

def error_response(message: str, code: str = "ERROR") -> Dict[str, Any]:
    """Error response"""
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message
        },
        "timestamp": now_ms()
    }

def not_found_error(resource: str = "Resource"):
    """404 error"""
    raise HTTPException(
        status_code=404,
        detail=f"{resource} not found"
    )

def validation_error(message: str):
    """Validation error"""
    raise HTTPException(
        status_code=422,
        detail=message
    )

def internal_error(message: str = "Internal server error"):
    """500 error"""
    raise HTTPException(
        status_code=500,
        detail=message
    )
