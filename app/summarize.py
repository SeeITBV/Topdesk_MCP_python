"""Result summarization utilities."""

import logging
from typing import List, Dict, Any, Optional
from collections import Counter
from .schemas import NormalizedIncident


logger = logging.getLogger(__name__)


def summarize_incidents(incidents: List[NormalizedIncident], original_query: str = "") -> str:
    """Generate a natural language summary of incident results.
    
    Args:
        incidents: List of normalized incidents
        original_query: Original user query for context
        
    Returns:
        Natural language summary string
    """
    if not incidents:
        return "No incidents found matching your query."
    
    count = len(incidents)
    
    # Analyze the data
    status_counts = Counter(inc.status for inc in incidents if inc.status)
    priority_counts = Counter(inc.priority for inc in incidents if inc.priority)
    operator_counts = Counter(inc.operator for inc in incidents if inc.operator)
    caller_counts = Counter(inc.caller for inc in incidents if inc.caller)
    
    # Start building summary
    summary_parts = []
    
    # Basic count
    if count == 1:
        summary_parts.append("Found 1 incident")
    else:
        summary_parts.append(f"Found {count} incidents")
    
    # Status breakdown
    if status_counts:
        status_info = _format_counter_summary(status_counts, "status", top_n=3)
        if status_info:
            summary_parts.append(status_info)
    
    # Priority information
    if priority_counts:
        high_priority = sum(count for priority, count in priority_counts.items() 
                          if priority and priority.lower() in ['high', 'critical', 'urgent'])
        if high_priority > 0:
            if high_priority == 1:
                summary_parts.append("1 high priority")
            else:
                summary_parts.append(f"{high_priority} high priority")
    
    # Assignment information
    if operator_counts:
        assigned_count = sum(operator_counts.values())
        unassigned_count = count - assigned_count
        
        if assigned_count > 0:
            if assigned_count == 1:
                summary_parts.append("1 assigned")
            else:
                summary_parts.append(f"{assigned_count} assigned")
        
        # Mention top operator if significant
        if operator_counts:
            top_operator, top_count = operator_counts.most_common(1)[0]
            if top_count > 1 and top_operator:
                summary_parts.append(f"{top_count} to {_format_name(top_operator)}")
    
    # Caller information (if query was person-specific)
    if len(caller_counts) == 1 and any(name in original_query.lower() for name in caller_counts.keys() if name):
        # Single caller query
        caller_name = list(caller_counts.keys())[0]
        if caller_name:
            summary_parts.append(f"for {_format_name(caller_name)}")
    
    # Time context
    if "recent" in original_query.lower() or "last" in original_query.lower():
        summary_parts.append("(recent)")
    elif any(word in original_query.lower() for word in ["today", "yesterday"]):
        summary_parts.append("(recent)")
    
    # Join with appropriate separators
    if len(summary_parts) <= 2:
        summary = " ".join(summary_parts)
    else:
        # Use commas for multiple parts
        summary = summary_parts[0]
        for i, part in enumerate(summary_parts[1:], 1):
            if i == len(summary_parts) - 1:
                summary += f", {part}"
            else:
                summary += f", {part}"
    
    # Ensure sentence ends properly
    if not summary.endswith('.'):
        summary += '.'
    
    return summary


def _format_counter_summary(counter: Counter, category: str, top_n: int = 3) -> str:
    """Format a counter into a summary string.
    
    Args:
        counter: Counter object with item counts
        category: Category name for context
        top_n: Maximum number of items to include
        
    Returns:
        Formatted summary string
    """
    if not counter:
        return ""
    
    total = sum(counter.values())
    most_common = counter.most_common(top_n)
    
    if len(most_common) == 1:
        item, count = most_common[0]
        if count == total:
            return f"all {item}"
        else:
            return f"{count} {item}"
    
    # Multiple items
    parts = []
    for item, count in most_common:
        if item:  # Skip None/empty values
            parts.append(f"{count} {item}")
    
    if len(parts) <= 2:
        return ", ".join(parts)
    else:
        # Show first few and summarize rest
        shown = parts[:2]
        remaining = len(parts) - 2
        if remaining == 1:
            return f"{', '.join(shown)}, {parts[2]}"
        else:
            return f"{', '.join(shown)}, {remaining} others"


def _format_name(name: str) -> str:
    """Format a person name for display.
    
    Args:
        name: Full name to format
        
    Returns:
        Formatted name
    """
    if not name:
        return ""
    
    # If name appears to be "FirstName LastName", keep as is
    parts = name.strip().split()
    if len(parts) == 2:
        return name
    elif len(parts) > 2:
        # Use first and last name only
        return f"{parts[0]} {parts[-1]}"
    else:
        return name


def summarize_single_incident(incident: NormalizedIncident) -> str:
    """Summarize a single incident for detailed view.
    
    Args:
        incident: Single normalized incident
        
    Returns:
        Detailed summary string
    """
    summary_parts = []
    
    # Basic info
    if incident.number:
        summary_parts.append(f"Incident {incident.number}")
    else:
        summary_parts.append("Incident")
    
    # Title
    if incident.title:
        title = incident.title
        if len(title) > 50:
            title = title[:47] + "..."
        summary_parts.append(f": {title}")
    
    # Status and creation
    status_info = []
    if incident.status:
        status_info.append(incident.status)
    
    if incident.created_at:
        # Format creation date
        try:
            from datetime import datetime
            if len(incident.created_at) >= 10:  # Has date portion
                date_part = incident.created_at[:10]
                status_info.append(f"created {date_part}")
        except:
            pass
    
    if status_info:
        summary_parts.append(f" ({', '.join(status_info)})")
    
    # Priority
    if incident.priority:
        summary_parts.append(f", Priority: {incident.priority}")
    
    # Assignment
    if incident.operator:
        summary_parts.append(f", Assigned to: {_format_name(incident.operator)}")
    elif incident.operator_group:
        summary_parts.append(f", Assigned to: {incident.operator_group}")
    else:
        summary_parts.append(", Unassigned")
    
    # Caller
    if incident.caller:
        summary_parts.append(f", Caller: {_format_name(incident.caller)}")
    
    return "".join(summary_parts)


def summarize_person_lookup(person_info: Optional[Dict[str, str]], 
                          incidents: List[NormalizedIncident], 
                          original_query: str = "") -> str:
    """Summarize person lookup results with their incidents.
    
    Args:
        person_info: Normalized person information
        incidents: Person's incidents
        original_query: Original query
        
    Returns:
        Summary including person info and incident summary
    """
    if not person_info:
        return "Person not found. " + summarize_incidents(incidents, original_query)
    
    person_name = person_info.get("name", "Unknown person")
    
    if not incidents:
        return f"Found {person_name} but no incidents match your criteria."
    
    incident_summary = summarize_incidents(incidents, original_query)
    
    # Replace generic "Found X incidents" with person-specific version
    if incident_summary.startswith("Found "):
        count_part = incident_summary.split(" ")[1]
        rest = incident_summary.split(" ", 2)[2] if len(incident_summary.split(" ")) > 2 else ""
        return f"{person_name} has {count_part} incidents {rest}".strip()
    
    return f"{person_name}: {incident_summary}"


def summarize_operator_lookup(operator_info: Optional[Dict[str, str]], 
                            incidents: List[NormalizedIncident], 
                            original_query: str = "") -> str:
    """Summarize operator lookup results with their assigned incidents.
    
    Args:
        operator_info: Normalized operator information
        incidents: Operator's assigned incidents
        original_query: Original query
        
    Returns:
        Summary including operator info and incident summary
    """
    if not operator_info:
        return "Operator not found. " + summarize_incidents(incidents, original_query)
    
    operator_name = operator_info.get("name", "Unknown operator")
    
    if not incidents:
        return f"Found {operator_name} but no assigned incidents match your criteria."
    
    incident_summary = summarize_incidents(incidents, original_query)
    
    # Replace generic "Found X incidents" with operator-specific version
    if incident_summary.startswith("Found "):
        count_part = incident_summary.split(" ")[1]
        rest = incident_summary.split(" ", 2)[2] if len(incident_summary.split(" ")) > 2 else ""
        return f"{operator_name} is assigned {count_part} incidents {rest}".strip()
    
    return f"{operator_name}: {incident_summary}"


def generate_error_summary(error_msg: str, query: str = "") -> str:
    """Generate user-friendly error summary.
    
    Args:
        error_msg: Technical error message
        query: Original user query
        
    Returns:
        User-friendly error summary
    """
    error_lower = error_msg.lower()
    
    if "timeout" in error_lower:
        return "The request took too long to complete. Please try again or refine your query."
    
    elif "circuit" in error_lower and "open" in error_lower:
        return "The TOPdesk service is currently unavailable. Please try again in a few minutes."
    
    elif "rate limit" in error_lower:
        return "Too many requests. Please wait a moment before trying again."
    
    elif "not found" in error_lower:
        if query and any(word in query.lower() for word in ["person", "user", "caller"]):
            return "The person you're looking for was not found. Please check the name spelling."
        elif query and any(word in query.lower() for word in ["operator", "technician"]):
            return "The operator you're looking for was not found. Please check the name spelling."
        else:
            return "The requested information was not found."
    
    elif "invalid" in error_lower:
        return "Your query contains invalid parameters. Please check your input and try again."
    
    elif "permission" in error_lower or "unauthorized" in error_lower:
        return "Access denied. You may not have permission to view this information."
    
    else:
        return "An error occurred while processing your request. Please try again or contact support."