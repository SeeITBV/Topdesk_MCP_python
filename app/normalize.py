"""Data normalization utilities for MCP responses."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from .schemas import NormalizedIncident


logger = logging.getLogger(__name__)


def safe_get(data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely get nested dictionary values.
    
    Args:
        data: Dictionary to extract from
        *keys: Nested keys to traverse
        default: Default value if key not found
        
    Returns:
        Value at the key path or default
    """
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def normalize_datetime(dt_str: Optional[str]) -> str:
    """Normalize datetime string to consistent format.
    
    Args:
        dt_str: DateTime string in various formats
        
    Returns:
        Normalized datetime string or empty string
    """
    if not dt_str:
        return ""
    
    try:
        # Try parsing common TOPdesk datetime formats
        formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",      # ISO with microseconds
            "%Y-%m-%dT%H:%M:%SZ",         # ISO without microseconds  
            "%Y-%m-%dT%H:%M:%S",          # ISO without timezone
            "%Y-%m-%d %H:%M:%S",          # Space separated
            "%Y-%m-%d"                    # Date only
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(dt_str, fmt)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
        
        # If no format matches, return original
        return str(dt_str)
    
    except Exception as e:
        logger.warning(f"Failed to normalize datetime '{dt_str}': {e}")
        return str(dt_str) if dt_str else ""


def normalize_person_name(person_data: Optional[Dict[str, Any]]) -> str:
    """Extract and normalize person name from person object.
    
    Args:
        person_data: Person object from TOPdesk API
        
    Returns:
        Formatted person name or empty string
    """
    if not person_data or not isinstance(person_data, dict):
        return ""
    
    # Try different name field combinations
    first_name = safe_get(person_data, "firstName", default="").strip()
    last_name = safe_get(person_data, "surname", default="").strip()
    display_name = safe_get(person_data, "dynamicName", default="").strip()
    
    # Use display name if available
    if display_name:
        return display_name
    
    # Combine first and last name
    if first_name and last_name:
        return f"{first_name} {last_name}"
    elif first_name:
        return first_name
    elif last_name:
        return last_name
    
    # Fallback to other name fields
    return safe_get(person_data, "name", default="")


def normalize_incident(incident_data: Dict[str, Any]) -> NormalizedIncident:
    """Normalize a single incident from TOPdesk API response.
    
    Args:
        incident_data: Raw incident data from TOPdesk
        
    Returns:
        Normalized incident object
    """
    try:
        # Extract basic fields with safe defaults
        incident_id = safe_get(incident_data, "id", default="")
        number = safe_get(incident_data, "number", default="")
        title = safe_get(incident_data, "briefDescription", default="")
        
        # Handle status - could be string or object
        status_data = safe_get(incident_data, "status")
        if isinstance(status_data, dict):
            status = safe_get(status_data, "name", default="Unknown")
        else:
            status = str(status_data) if status_data else "Unknown"
        
        # Handle creation date
        created_at = normalize_datetime(safe_get(incident_data, "creationDate"))
        
        # Handle priority - could be string or object
        priority_data = safe_get(incident_data, "priority")
        if isinstance(priority_data, dict):
            priority = safe_get(priority_data, "name")
        else:
            priority = str(priority_data) if priority_data else None
        
        # Handle caller - could be string or object
        caller_data = safe_get(incident_data, "caller")
        caller = normalize_person_name(caller_data) if caller_data else None
        
        # Handle operator - could be string or object
        operator_data = safe_get(incident_data, "operator")
        operator = normalize_person_name(operator_data) if operator_data else None
        
        # Handle operator group
        operator_group_data = safe_get(incident_data, "operatorGroup")
        if isinstance(operator_group_data, dict):
            operator_group = safe_get(operator_group_data, "name")
        else:
            operator_group = str(operator_group_data) if operator_group_data else None
        
        return NormalizedIncident(
            id=str(incident_id),
            number=str(number),
            title=str(title),
            status=status,
            created_at=created_at,
            priority=priority,
            caller=caller,
            operator=operator,
            operator_group=operator_group
        )
    
    except Exception as e:
        logger.error(f"Failed to normalize incident: {e}")
        logger.debug(f"Incident data: {incident_data}")
        
        # Return minimal incident with available data
        return NormalizedIncident(
            id=safe_get(incident_data, "id", default="unknown"),
            number=safe_get(incident_data, "number", default="unknown"),
            title=safe_get(incident_data, "briefDescription", default="Error normalizing incident"),
            status="Unknown",
            created_at="",
            priority=None,
            caller=None,
            operator=None,
            operator_group=None
        )


def normalize_incidents_response(response: Dict[str, Any]) -> List[NormalizedIncident]:
    """Normalize incidents from MCP response.
    
    Args:
        response: Raw MCP response containing incidents
        
    Returns:
        List of normalized incidents
    """
    incidents = []
    
    try:
        # Handle different response structures
        if isinstance(response, list):
            # Direct list of incidents
            incident_list = response
        elif isinstance(response, dict):
            # Check for common response structures
            incident_list = (
                safe_get(response, "incidents", default=[]) or
                safe_get(response, "data", default=[]) or 
                safe_get(response, "results", default=[]) or
                []
            )
        else:
            logger.warning(f"Unexpected response type: {type(response)}")
            return incidents
        
        # Normalize each incident
        for incident_data in incident_list:
            if isinstance(incident_data, dict):
                normalized = normalize_incident(incident_data)
                incidents.append(normalized)
            else:
                logger.warning(f"Skipping non-dict incident: {type(incident_data)}")
    
    except Exception as e:
        logger.error(f"Failed to normalize incidents response: {e}")
        logger.debug(f"Response data: {response}")
    
    return incidents


def normalize_person_response(response: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Normalize person response from MCP.
    
    Args:
        response: Raw MCP response containing person data
        
    Returns:
        Normalized person information or None
    """
    try:
        # Handle different response structures
        person_data = None
        
        if isinstance(response, dict):
            # Direct person object
            if "id" in response or "firstName" in response or "surname" in response:
                person_data = response
            else:
                # Check for nested person data
                person_list = (
                    safe_get(response, "persons", default=[]) or
                    safe_get(response, "data", default=[]) or
                    safe_get(response, "results", default=[])
                )
                
                if person_list and len(person_list) > 0:
                    person_data = person_list[0]  # Take first match
        
        if not person_data:
            return None
        
        return {
            "id": safe_get(person_data, "id", default=""),
            "name": normalize_person_name(person_data),
            "email": safe_get(person_data, "email", default=""),
            "firstName": safe_get(person_data, "firstName", default=""),
            "surname": safe_get(person_data, "surname", default="")
        }
    
    except Exception as e:
        logger.error(f"Failed to normalize person response: {e}")
        return None


def normalize_operator_response(response: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Normalize operator response from MCP.
    
    Args:
        response: Raw MCP response containing operator data
        
    Returns:
        Normalized operator information or None
    """
    try:
        # Handle different response structures
        operator_data = None
        
        if isinstance(response, dict):
            # Direct operator object
            if "id" in response and "name" in response:
                operator_data = response
            else:
                # Check for nested operator data
                operator_list = (
                    safe_get(response, "operators", default=[]) or
                    safe_get(response, "data", default=[]) or
                    safe_get(response, "results", default=[])
                )
                
                if operator_list and len(operator_list) > 0:
                    operator_data = operator_list[0]  # Take first match
        
        if not operator_data:
            return None
        
        return {
            "id": safe_get(operator_data, "id", default=""),
            "name": safe_get(operator_data, "name", default=""),
            "firstName": safe_get(operator_data, "firstName", default=""),
            "surname": safe_get(operator_data, "surname", default="")
        }
    
    except Exception as e:
        logger.error(f"Failed to normalize operator response: {e}")
        return None


def sanitize_for_logging(data: Any, max_depth: int = 3) -> Any:
    """Sanitize data for safe logging by removing PII and limiting depth.
    
    Args:
        data: Data to sanitize
        max_depth: Maximum nesting depth to preserve
        
    Returns:
        Sanitized data safe for logging
    """
    if max_depth <= 0:
        return "..."
    
    if isinstance(data, dict):
        sanitized = {}
        
        # Fields to completely remove (PII)
        pii_fields = {
            'password', 'api_key', 'token', 'secret', 'credential',
            'email', 'phone', 'ssn', 'address', 'personalDetails'
        }
        
        # Fields to truncate
        truncate_fields = {
            'briefDescription', 'request', 'action', 'memo'
        }
        
        for key, value in data.items():
            key_lower = key.lower()
            
            # Skip PII fields
            if any(pii in key_lower for pii in pii_fields):
                continue
            
            # Truncate long text fields
            if any(field in key_lower for field in truncate_fields) and isinstance(value, str):
                sanitized[key] = value[:100] + "..." if len(value) > 100 else value
            else:
                sanitized[key] = sanitize_for_logging(value, max_depth - 1)
        
        return sanitized
    
    elif isinstance(data, list):
        # Limit list size for logging
        return [sanitize_for_logging(item, max_depth - 1) for item in data[:5]]
    
    elif isinstance(data, str) and len(data) > 200:
        # Truncate very long strings
        return data[:200] + "..."
    
    else:
        return data