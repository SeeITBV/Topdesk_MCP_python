"""Validation utilities for request processing."""

import re
import uuid
from typing import Optional, List
from .fiql import validate_fiql


class ValidationError(Exception):
    """Custom validation error."""
    pass


def ensure_uuid(value: str, field_name: str = "ID") -> str:
    """Validate and return a UUID string.
    
    Args:
        value: String that should be a valid UUID
        field_name: Name of the field for error messages
        
    Returns:
        Validated UUID string
        
    Raises:
        ValidationError: If the value is not a valid UUID
    """
    if not value:
        raise ValidationError(f"{field_name} cannot be empty")
    
    try:
        # This will raise ValueError if not a valid UUID
        uuid_obj = uuid.UUID(value)
        return str(uuid_obj)
    except ValueError:
        raise ValidationError(f"{field_name} must be a valid UUID: {value}")


def ensure_limit(value: int, max_limit: int = 25, field_name: str = "limit") -> int:
    """Validate and return a limit value.
    
    Args:
        value: Limit value to validate
        max_limit: Maximum allowed limit
        field_name: Name of the field for error messages
        
    Returns:
        Validated limit value
        
    Raises:
        ValidationError: If the limit is invalid
    """
    if value < 1:
        raise ValidationError(f"{field_name} must be at least 1")
    
    if value > max_limit:
        raise ValidationError(f"{field_name} cannot exceed {max_limit}")
    
    return value


def ensure_nonempty_fiql(query: str) -> str:
    """Validate that a FIQL query is not empty and appears valid.
    
    Args:
        query: FIQL query string to validate
        
    Returns:
        Validated FIQL query string
        
    Raises:
        ValidationError: If the query is invalid
    """
    if not query or not query.strip():
        raise ValidationError("FIQL query cannot be empty")
    
    query = query.strip()
    
    if not validate_fiql(query):
        raise ValidationError("FIQL query appears to be malformed")
    
    return query


def validate_incident_number(value: str) -> str:
    """Validate TOPdesk incident number format.
    
    Args:
        value: Incident number to validate
        
    Returns:
        Validated incident number
        
    Raises:
        ValidationError: If the incident number format is invalid
    """
    if not value:
        raise ValidationError("Incident number cannot be empty")
    
    # TOPdesk incident numbers typically follow pattern: I-YYMMDD-NNN
    pattern = r'^I-\d{6}-\d{3}$'
    if not re.match(pattern, value):
        raise ValidationError(f"Invalid incident number format: {value}. Expected format: I-YYMMDD-NNN")
    
    return value


def validate_tool_name(tool_name: str, allowed_tools: Optional[List[str]] = None) -> str:
    """Validate that a tool name is in the allowlist.
    
    Args:
        tool_name: Name of the tool to validate
        allowed_tools: List of allowed tool names
        
    Returns:
        Validated tool name
        
    Raises:
        ValidationError: If the tool is not allowed
    """
    if not tool_name:
        raise ValidationError("Tool name cannot be empty")
    
    if allowed_tools is None:
        # Default allowlist
        allowed_tools = [
            "search",
            "topdesk_get_incidents_by_fiql_query",
            "topdesk_get_person_by_query",
            "topdesk_get_operators_by_fiql_query",
            "topdesk_get_complete_incident_overview"
        ]
    
    if tool_name not in allowed_tools:
        raise ValidationError(f"Tool '{tool_name}' is not allowed. Allowed tools: {', '.join(allowed_tools)}")
    
    return tool_name


def validate_query_text(query: str, max_length: int = 1000) -> str:
    """Validate natural language query text.
    
    Args:
        query: Query text to validate
        max_length: Maximum allowed length
        
    Returns:
        Validated and cleaned query text
        
    Raises:
        ValidationError: If the query is invalid
    """
    if not query:
        raise ValidationError("Query cannot be empty")
    
    query = query.strip()
    
    if not query:
        raise ValidationError("Query cannot be empty after trimming whitespace")
    
    if len(query) > max_length:
        raise ValidationError(f"Query too long. Maximum length: {max_length} characters")
    
    # Check for potential injection attempts
    dangerous_patterns = [
        r'<script', r'javascript:', r'on\w+\s*=', r'eval\s*\(',
        r'document\.', r'window\.', r'alert\s*\('
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            raise ValidationError("Query contains potentially dangerous content")
    
    return query


def validate_person_name(name: str, field_name: str = "name") -> str:
    """Validate person name format.
    
    Args:
        name: Name to validate
        field_name: Name of the field for error messages
        
    Returns:
        Validated name
        
    Raises:
        ValidationError: If the name is invalid
    """
    if not name:
        raise ValidationError(f"{field_name} cannot be empty")
    
    name = name.strip()
    
    if not name:
        raise ValidationError(f"{field_name} cannot be empty after trimming")
    
    if len(name) > 100:
        raise ValidationError(f"{field_name} too long. Maximum length: 100 characters")
    
    # Check for reasonable name format (letters, spaces, hyphens, apostrophes)
    if not re.match(r"^[a-zA-Z\s\-'\.]+$", name):
        raise ValidationError(f"{field_name} contains invalid characters")
    
    return name


def validate_email(email: str) -> str:
    """Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        Validated email address
        
    Raises:
        ValidationError: If the email is invalid
    """
    if not email:
        raise ValidationError("Email cannot be empty")
    
    email = email.strip().lower()
    
    # Basic email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError(f"Invalid email format: {email}")
    
    return email


def sanitize_log_data(data: dict) -> dict:
    """Sanitize data for logging by removing PII.
    
    Args:
        data: Dictionary to sanitize
        
    Returns:
        Sanitized dictionary safe for logging
    """
    if not isinstance(data, dict):
        return data
    
    sanitized = {}
    
    # Fields to completely remove
    pii_fields = {
        'password', 'api_key', 'token', 'secret', 'credential',
        'email', 'phone', 'ssn', 'address', 'birthday'
    }
    
    # Fields to partially mask
    mask_fields = {
        'name', 'firstname', 'lastname', 'surname', 'caller', 'operator'
    }
    
    for key, value in data.items():
        key_lower = key.lower()
        
        # Skip PII fields entirely
        if any(pii in key_lower for pii in pii_fields):
            continue
        
        # Mask sensitive fields
        if any(mask in key_lower for mask in mask_fields) and isinstance(value, str):
            if len(value) > 2:
                sanitized[key] = value[:2] + '*' * (len(value) - 2)
            else:
                sanitized[key] = '*' * len(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_log_data(value)
        elif isinstance(value, list):
            sanitized[key] = [sanitize_log_data(item) if isinstance(item, dict) else item for item in value]
        else:
            sanitized[key] = value
    
    return sanitized