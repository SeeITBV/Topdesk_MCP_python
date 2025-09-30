"""FIQL query building utilities for TOPdesk API."""

import re
from datetime import datetime, timedelta
from typing import List, Optional, Union
from urllib.parse import quote


def quote_value(value: str) -> str:
    """Quote and escape a FIQL value properly.
    
    Args:
        value: The value to quote and escape
        
    Returns:
        Properly quoted and escaped value
    """
    if not value:
        return "''"
    
    # Escape backslashes first
    escaped = value.replace('\\', '\\\\')
    
    # Escape single quotes
    escaped = escaped.replace("'", "\\'")
    
    # Quote the value
    return f"'{escaped}'"


def iso_utc(dt: datetime) -> str:
    """Convert datetime to ISO 8601 UTC format for FIQL.
    
    Args:
        dt: Datetime object to convert
        
    Returns:
        ISO 8601 formatted string
    """
    if dt.tzinfo is None:
        # Assume UTC if no timezone info
        dt = dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
    
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')


def days_ago(days: int) -> str:
    """Get ISO timestamp for N days ago.
    
    Args:
        days: Number of days to subtract from now
        
    Returns:
        ISO 8601 formatted timestamp
    """
    dt = datetime.utcnow() - timedelta(days=days)
    return iso_utc(dt)


def and_join(*parts: str) -> str:
    """Join FIQL query parts with AND (semicolon).
    
    Args:
        *parts: FIQL query parts to join
        
    Returns:
        Joined FIQL query string
    """
    # Filter out empty/None parts
    valid_parts = [part for part in parts if part and part.strip()]
    return ';'.join(valid_parts)


def or_join(*parts: str) -> str:
    """Join FIQL query parts with OR (comma).
    
    Args:
        *parts: FIQL query parts to join
        
    Returns:
        Joined FIQL query string
    """
    # Filter out empty/None parts
    valid_parts = [part for part in parts if part and part.strip()]
    return ','.join(valid_parts)


def in_list(field: str, values: List[str]) -> str:
    """Create FIQL 'in' query for a field with multiple values.
    
    Args:
        field: Field name
        values: List of values to match
        
    Returns:
        FIQL 'in' query string
    """
    if not values:
        return ""
    
    # Quote each value
    quoted_values = [quote_value(str(v)) for v in values]
    values_str = ','.join(quoted_values)
    return f"{field}=in=({values_str})"


def equals(field: str, value: str) -> str:
    """Create FIQL equals query.
    
    Args:
        field: Field name
        value: Value to match exactly
        
    Returns:
        FIQL equals query string
    """
    return f"{field}=={quote_value(str(value))}"


def not_equals(field: str, value: str) -> str:
    """Create FIQL not equals query.
    
    Args:
        field: Field name
        value: Value to not match
        
    Returns:
        FIQL not equals query string
    """
    return f"{field}!={quote_value(str(value))}"


def starts_with(field: str, value: str) -> str:
    """Create FIQL starts with query.
    
    Args:
        field: Field name
        value: Value prefix to match
        
    Returns:
        FIQL starts with query string
    """
    return f"{field}=sw={quote_value(str(value))}"


def greater_equal(field: str, value: Union[str, datetime]) -> str:
    """Create FIQL greater than or equal query.
    
    Args:
        field: Field name
        value: Value to compare (string or datetime)
        
    Returns:
        FIQL greater than or equal query string
    """
    if isinstance(value, datetime):
        value = iso_utc(value)
    return f"{field}=ge={value}"


def less_than(field: str, value: Union[str, datetime]) -> str:
    """Create FIQL less than query.
    
    Args:
        field: Field name
        value: Value to compare (string or datetime)
        
    Returns:
        FIQL less than query string
    """
    if isinstance(value, datetime):
        value = iso_utc(value)
    return f"{field}=lt={value}"


def build_person_query(first_name: Optional[str] = None, last_name: Optional[str] = None, 
                      email: Optional[str] = None) -> str:
    """Build FIQL query for person lookup.
    
    Args:
        first_name: First name to search for
        last_name: Last name to search for  
        email: Email to search for
        
    Returns:
        FIQL query string for person search
    """
    parts = []
    
    if first_name:
        parts.append(equals("firstName", first_name))
    
    if last_name:
        parts.append(equals("surname", last_name))
        
    if email:
        parts.append(equals("email", email))
    
    return and_join(*parts)


def build_operator_query(name: Optional[str] = None, exact: bool = True) -> str:
    """Build FIQL query for operator lookup.
    
    Args:
        name: Operator name to search for
        exact: Whether to do exact match or starts with
        
    Returns:
        FIQL query string for operator search
    """
    if not name:
        return ""
    
    if exact:
        return equals("name", name)
    else:
        return starts_with("name", name)


def build_incident_query(caller_id: Optional[str] = None,
                        operator_id: Optional[str] = None,
                        operator_name: Optional[str] = None,
                        status_exclude: Optional[List[str]] = None,
                        priority_levels: Optional[List[str]] = None,
                        category: Optional[str] = None,
                        title_starts: Optional[str] = None,
                        created_after: Optional[datetime] = None,
                        created_before: Optional[datetime] = None,
                        days_back: Optional[int] = None) -> str:
    """Build comprehensive FIQL query for incident search.
    
    Args:
        caller_id: UUID of the caller
        operator_id: UUID of the operator
        operator_name: Name of the operator (fallback if no ID)
        status_exclude: List of statuses to exclude (e.g., ['Closed'])
        priority_levels: List of priority levels to include
        category: Category name to filter by
        title_starts: Brief description starts with
        created_after: Include incidents created after this datetime
        created_before: Include incidents created before this datetime
        days_back: Include incidents from N days back (overrides created_after)
        
    Returns:
        FIQL query string for incident search
    """
    parts = []
    
    # Caller filter
    if caller_id:
        parts.append(equals("caller.id", caller_id))
    
    # Operator filter
    if operator_id:
        parts.append(equals("operator.id", operator_id))
    elif operator_name:
        parts.append(equals("operator.name", operator_name))
    
    # Status exclusions
    if status_exclude:
        for status in status_exclude:
            parts.append(not_equals("status", status))
    
    # Priority filter
    if priority_levels:
        parts.append(in_list("priority.name", priority_levels))
    
    # Category filter
    if category:
        parts.append(equals("category.name", category))
    
    # Title filter
    if title_starts:
        parts.append(starts_with("briefDescription", title_starts))
    
    # Date filters
    if days_back is not None:
        created_after = datetime.utcnow() - timedelta(days=days_back)
    
    if created_after:
        parts.append(greater_equal("creationDate", created_after))
    
    if created_before:
        parts.append(less_than("creationDate", created_before))
    
    return and_join(*parts)


def validate_fiql(query: str) -> bool:
    """Basic validation of FIQL query syntax.
    
    Args:
        query: FIQL query string to validate
        
    Returns:
        True if query appears valid, False otherwise
    """
    if not query or not query.strip():
        return False
    
    # Check for balanced quotes
    single_quotes = query.count("'")
    if single_quotes % 2 != 0:
        return False
    
    # Check for balanced parentheses
    open_parens = query.count("(")
    close_parens = query.count(")")
    if open_parens != close_parens:
        return False
    
    # Basic operator validation - should contain at least one valid operator
    operators = ['==', '!=', '=ge=', '=le=', '=gt=', '=lt=', '=sw=', '=in=']
    has_operator = any(op in query for op in operators)
    
    return has_operator


def sanitize_fiql(query: str) -> str:
    """Sanitize FIQL query by removing potentially dangerous content.
    
    Args:
        query: FIQL query to sanitize
        
    Returns:
        Sanitized FIQL query
    """
    if not query:
        return ""
    
    # Remove any script-like content
    query = re.sub(r'<script.*?</script>', '', query, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove SQL injection attempts
    dangerous_patterns = [
        r'\bDROP\b', r'\bDELETE\b', r'\bINSERT\b', r'\bUPDATE\b',
        r'\bUNION\b', r'\bSELECT\b', r'\bEXEC\b'
    ]
    
    for pattern in dangerous_patterns:
        query = re.sub(pattern, '', query, flags=re.IGNORECASE)
    
    return query.strip()