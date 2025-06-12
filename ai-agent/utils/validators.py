"""
Validation tools
"""

class ValidationError(Exception):
    """Validation error"""
    pass

def validate_not_empty(value: str, field_name: str = "Field"):
    """Validate non-empty"""
    if not value or not value.strip():
        raise ValidationError(f"{field_name} cannot be empty")

def validate_max_length(value: str, max_length: int, field_name: str = "Field"):
    """Validate maximum length"""
    if len(value) > max_length:
        raise ValidationError(f"{field_name} length cannot exceed {max_length} characters")

def validate_chat_message(message: str):
    """Validate chat message"""
    validate_not_empty(message, "Message content")
    validate_max_length(message, 5000, "Message content")

def validate_conversation_id(conversation_id: str):
    """Validate conversation ID"""
    validate_not_empty(conversation_id, "Conversation ID")
    if not conversation_id.startswith("conv_"):
        raise ValidationError("Conversation ID format is incorrect")