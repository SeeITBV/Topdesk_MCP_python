from fastmcp import FastMCP
from topdesk_mcp import _topdesk_sdk as topdesk_sdk
from dotenv import load_dotenv
import os
import logging
from types import MethodType
import functools
import json
from typing import Any, List, Dict

try:  # pragma: no cover - fallback for environments with stubbed FastMCP
    from fastmcp.requests import ListToolsRequest
except ImportError:  # pragma: no cover - align with tests that stub fastmcp
    class ListToolsRequest:  # type: ignore[too-many-ancestors]
        """Fallback ListToolsRequest used when FastMCP is unavailable."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            """Initialise a minimal request placeholder."""

            self.args = args
            self.kwargs = kwargs

# MCP Error handling utility
class MCPError(Exception):
    """Base class for MCP-specific errors."""
    def __init__(self, message: str, error_code: int = -1):
        self.message = message
        self.error_code = error_code
        super().__init__(message)

def handle_mcp_error(func):
    """Decorator to handle errors in MCP tools and return proper error format."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except MCPError as e:
            return {
                "error": {
                    "code": e.error_code,
                    "message": e.message
                }
            }
        except Exception as e:
            return {
                "error": {
                    "code": -32603,  # Internal error
                    "message": f"Internal error: {str(e)}"
                }
            }
    return wrapper

# Set up logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=os.getenv("LOG_FILE", None)
)

# Store log configuration for later access
LOG_FILE = os.getenv("LOG_FILE", None)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
load_dotenv()

# Load config from environment variables
TOPDESK_URL = os.getenv("TOPDESK_URL")
TOPDESK_USERNAME = os.getenv("TOPDESK_USERNAME")
TOPDESK_PASSWORD = os.getenv("TOPDESK_PASSWORD")

if not (TOPDESK_URL and TOPDESK_USERNAME and TOPDESK_PASSWORD):
    raise RuntimeError("Missing TOPdesk credentials. Set TOPDESK_URL, TOPDESK_USERNAME, and TOPDESK_PASSWORD as environment variables.")

# Initialise TOPdesk SDK
topdesk_client = topdesk_sdk.connect(TOPDESK_URL, TOPDESK_USERNAME, TOPDESK_PASSWORD)

# Initialise the MCP server
mcp = FastMCP("TOPdesk MCP Server")

_REGISTERED_TOOLS: dict[str, dict[str, Any]] = {}
_original_tool = mcp.tool


def _registering_tool(self, *args: Any, **kwargs: Any):
    # Remove input_schema from kwargs as FastMCP doesn't support it
    filtered_kwargs = {k: v for k, v in kwargs.items() if k != "input_schema"}
    decorator = _original_tool(*args, **filtered_kwargs)

    def wrapper(func):
        registered = decorator(func)
        metadata = getattr(registered, "__mcp_tool__", None)
        tool_name = kwargs.get("name") or func.__name__
        description = kwargs.get("description")

        if isinstance(metadata, dict):
            tool_name = metadata.get("name", tool_name)
            description = metadata.get("description", description)
        else:
            metadata = None

        if description is None:
            description = registered.__doc__ or ""

        _REGISTERED_TOOLS[tool_name] = {
            "callable": registered,
            "metadata": metadata,
            "name": tool_name,
            "description": description,
        }

        return registered

    return wrapper


mcp.tool = MethodType(_registering_tool, mcp)


def _register_list_tools(handler):
    """Register the list tools handler in a version agnostic way."""
    # For now, just create a simple tool instead of complex registration
    return handler


# Create a simple tool to list registered tools
@mcp.tool(description="List all registered MCP tools available in this server")
def list_registered_tools() -> List[Dict[str, Any]]:
    """Return all tools registered with the TOPdesk MCP server."""

    tools = getattr(mcp, "tools", None)

    if callable(tools):  # pragma: no branch - defensive check for callables
        tools = tools()

    collected: list[Any] = []

    if isinstance(tools, dict):
        collected = list(tools.values())
    elif isinstance(tools, (list, tuple, set)):
        collected = list(tools)
    elif tools is not None:
        collected = list(tools)

    if not collected:
        for tool_info in _REGISTERED_TOOLS.values():
            metadata = tool_info.get("metadata")
            if metadata is not None:
                collected.append(metadata)
                continue

            tool_entry: dict[str, Any] = {
                "name": tool_info["name"],
                "description": tool_info.get("description", ""),
            }

            collected.append(tool_entry)

    return collected

    
###################
# HINTS
###################
@mcp.tool(
    description="Get a hint on how to construct FIQL queries, with examples."
)
def topdesk_get_fiql_query_howto() -> str:
    """Get a hint on how to construct FIQL queries, with examples."""
    try:
        with open(os.path.join(os.path.dirname(__file__), "resources", "fiql_query_howto.md"), "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        raise MCPError(f"Error reading FIQL query guide: {str(e)}", -32603)

##################
# SCHEMAS
##################
@mcp.tool(
    description="Get the full object schemas for TOPdesk incidents and all their subfields.",
    input_schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
@handle_mcp_error
def topdesk_get_object_schemas() -> str:
    """Get the full object schemas for TOPdesk incidents and all their subfields."""
    try:
        with open(os.path.join(os.path.dirname(__file__), "resources", "object_schemas.yaml"), "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        raise MCPError(f"Error reading object schemas: {str(e)}", -32603)

#################
# LOGGING
#################
@mcp.tool(
    description="Get log entries from the TOPdesk MCP server. Can retrieve recent logs or search by level.",
    input_schema={
        "type": "object",
        "properties": {
            "lines": {
                "type": "integer",
                "description": "Number of recent log lines to retrieve (default: 100, max: 1000).",
                "default": 100
            },
            "level": {
                "type": "string",
                "description": "Filter logs by level (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
                "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            }
        },
        "required": []
    }
)
@handle_mcp_error
def get_log_entries(lines: int = 100, level: str = None) -> dict:
    """Get log entries from the TOPdesk MCP server.
    
    Parameters:
        lines: Number of recent log lines to retrieve (default: 100, max: 1000).
        level: Filter logs by level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    import re
    from datetime import datetime
    
    # Validate parameters
    if lines <= 0 or lines > 1000:
        raise MCPError("Lines parameter must be between 1 and 1000", -32602)
    
    log_entries = []
    
    # If no log file is configured, return in-memory logs or current status
    if not LOG_FILE:
        return {
            "message": "No log file configured (LOG_FILE environment variable not set)",
            "configuration": {
                "log_file": LOG_FILE,
                "log_level": LOG_LEVEL,
                "current_time": datetime.now().isoformat()
            },
            "entries": [],
            "note": "Logs are being written to console/stdout. Configure LOG_FILE environment variable to enable file-based logging."
        }
    
    try:
        # Check if log file exists
        import os
        if not os.path.exists(LOG_FILE):
            return {
                "message": f"Log file not found: {LOG_FILE}",
                "configuration": {
                    "log_file": LOG_FILE,
                    "log_level": LOG_LEVEL,
                    "current_time": datetime.now().isoformat()
                },
                "entries": [],
                "note": "Log file may not have been created yet. Try running some operations first."
            }
        
        # Read log file
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
        
        # Get the last N lines
        recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        # Parse log entries
        log_pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ([^-]+) - (\w+) - (.*)$'
        
        for line in recent_lines:
            line = line.strip()
            if not line:
                continue
                
            match = re.match(log_pattern, line)
            if match:
                timestamp, logger_name, log_level_entry, message = match.groups()
                
                # Filter by level if specified
                if level and log_level_entry != level:
                    continue
                
                log_entries.append({
                    "timestamp": timestamp,
                    "logger": logger_name.strip(),
                    "level": log_level_entry,
                    "message": message
                })
            else:
                # Handle multi-line log entries or malformed lines
                if log_entries:
                    # Append to the last entry's message
                    log_entries[-1]["message"] += "\\n" + line
                else:
                    # Add as a raw entry
                    log_entries.append({
                        "timestamp": datetime.now().isoformat(),
                        "logger": "raw",
                        "level": "INFO",
                        "message": line
                    })
        
        return {
            "configuration": {
                "log_file": LOG_FILE,
                "log_level": LOG_LEVEL,
                "total_lines_in_file": len(all_lines),
                "lines_requested": lines,
                "lines_returned": len(log_entries),
                "level_filter": level
            },
            "entries": log_entries
        }
        
    except Exception as e:
        raise MCPError(f"Error reading log file: {str(e)}", -32603)

#################
# INCIDENTS
#################
@mcp.tool(
    description="Get a TOPdesk incident by UUID or by Incident Number (I-xxxxxx-xxx). Both formats are accepted.",
    input_schema={
        "type": "object",
        "properties": {
            "incident_id": {
                "type": "string",
                "description": "The UUID or incident number of the TOPdesk incident to retrieve."
            },
            "concise": {
                "type": "boolean",
                "description": "Whether to return a concise version of the incident.",
                "default": True
            }
        },
        "required": ["incident_id"]
    }
)
@handle_mcp_error
def topdesk_get_incident(incident_id: str, concise: bool = True) -> dict:
    """Get a TOPdesk incident by UUID or by Incident Number (I-xxxxxx-xxx). Both formats are accepted.

    Parameters:
        incident_id: The UUID or incident number of the TOPdesk incident to retrieve.
        concise: Whether to return a concise version of the incident. Defaults to True.
    """
    if not incident_id or not str(incident_id).strip():
        raise MCPError("Incident ID must be provided and cannot be empty", -32602)
    
    if concise:
        return topdesk_client.incident.get_concise(incident=incident_id)
    else:
        return topdesk_client.incident.get(incident=incident_id)


@mcp.tool(
    description="Get TOPdesk incidents by FIQL query.",
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The FIQL query string to filter incidents."
            },
            "page_size": {
                "type": "integer",
                "description": "Maximum number of incidents to return.",
                "default": 100,
                "minimum": 1,
                "maximum": 1000
            }
        },
        "required": ["query"]
    }
)
@handle_mcp_error
def topdesk_get_incidents_by_fiql_query(query: str, page_size: int = 100) -> list:
    """Get TOPdesk incidents by FIQL query.

    Parameters:
        query: The FIQL query string to filter incidents.
        page_size: Maximum number of incidents to return. Defaults to 100.
    """
    if not query or not str(query).strip():
        raise MCPError("FIQL query must be provided and cannot be empty", -32602)
    
    if page_size < 1 or page_size > 1000:
        raise MCPError("page_size must be between 1 and 1000", -32602)
    
    return topdesk_client.incident.get_list(query=query, page_size=page_size)



def _normalise_title(title: str) -> str:
    """Normalise and validate an incident title provided by a user."""
    if title is None:
        raise MCPError("Search query must be provided", -32602)

    # Collapse whitespace and strip leading/trailing spaces
    normalised = " ".join(title.split())
    if not normalised:
        raise MCPError("Search query must not be empty", -32602)
    return normalised


@mcp.tool(
    description="Search Codex for incidents by their title (briefDescription).",
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The (partial) title of the incident to look up."
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of matches to return.",
                "default": 5,
                "minimum": 1,
                "maximum": 100
            }
        },
        "required": ["query"]
    }
)
@handle_mcp_error
def search(query: str, max_results: int = 5) -> Dict[str, List[Dict[str, str]]]:
    """Search Codex for incidents by their title (briefDescription).

    Parameters:
        query: The (partial) title of the incident to look up.
        max_results: Maximum number of matches to return. Defaults to 5.

    Returns:
        MCP-compliant response with content array containing JSON-encoded search results.
    """

    normalised_title = _normalise_title(query)
    # Escape double quotes to avoid breaking FIQL queries
    escaped_title = normalised_title.replace('"', '\\"')
    fiql_query = f"briefDescription==*{escaped_title}*"

    incidents = topdesk_client.incident.get_list(query=fiql_query)

    results: List[Dict[str, str]] = []
    for incident in incidents[:max_results]:
        incident_id = incident.get("id")
        incident_title = incident.get("briefDescription", "")
        
        # Construct URL for the incident in TOPdesk
        incident_url = f"{TOPDESK_URL}/tas/secure/incident?unid={incident_id}" if incident_id else ""

        results.append(
            {
                "id": incident_id or "",
                "title": incident_title,
                "url": incident_url,
            }
        )

    # Return in MCP-compliant format
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps({"results": results})
            }
        ]
    }


@mcp.tool(
    description="Get a TOPdesk incident by UUID or by Incident Number (I-xxxxxx-xxx). Both formats are accepted.",
    input_schema={
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": "The UUID or incident number of the TOPdesk incident to retrieve."
            },
            "concise": {
                "type": "boolean",
                "description": "Whether to return a concise version of the incident.",
                "default": True
            }
        },
        "required": ["id"]
    }
)
@handle_mcp_error
def fetch(id: str, concise: bool = True) -> Dict[str, List[Dict[str, str]]]:
    """Get a TOPdesk incident by UUID or by Incident Number (I-xxxxxx-xxx). Both formats are accepted.

    Parameters:
        id: The UUID or incident number of the TOPdesk incident to retrieve.
        concise: Whether to return a concise version of the incident. Defaults to True.

    Returns:
        MCP-compliant response with content array containing the incident details.
    """
    if id is None or not str(id).strip():
        raise MCPError("Incident ID must be provided and cannot be empty", -32602)

    if concise:
        incident = topdesk_client.incident.get_concise(incident=id)
    else:
        incident = topdesk_client.incident.get(incident=id)

    # Extract relevant fields for MCP format
    incident_id_value = incident.get("id", id)
    title = incident.get("briefDescription", "")
    
    # Construct the text content - combine key fields into readable text
    text_parts = []
    if title:
        text_parts.append(f"Title: {title}")
    if incident.get("number"):
        text_parts.append(f"Number: {incident.get('number')}")
    if incident.get("request"):
        text_parts.append(f"Request: {incident.get('request')}")
    if incident.get("processingStatus"):
        if isinstance(incident.get("processingStatus"), dict):
            status = incident.get("processingStatus", {}).get("name", "")
        else:
            status = str(incident.get("processingStatus"))
        if status:
            text_parts.append(f"Status: {status}")
    
    text_content = "\n".join(text_parts) if text_parts else json.dumps(incident, indent=2)
    
    # Construct URL for the incident
    url = f"{TOPDESK_URL}/tas/secure/incident?unid={incident_id_value}"
    
    # Create metadata with all other incident fields
    metadata = {k: v for k, v in incident.items() if k not in ["id", "briefDescription"]}
    
    # Prepare the result object
    result = {
        "id": incident_id_value,
        "title": title,
        "text": text_content,
        "url": url,
        "metadata": metadata
    }

    # Return in MCP-compliant format
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(result, indent=2)
            }
        ]
    }


@mcp.tool(
    description="Get all user requests on a TOPdesk incident.",
    input_schema={
        "type": "object",
        "properties": {
            "incident_id": {
                "type": "string",
                "description": "The UUID or incident number of the TOPdesk incident whose requests to retrieve."
            }
        },
        "required": ["incident_id"]
    }
)
@handle_mcp_error
def topdesk_get_incident_user_requests(incident_id: str) -> list:
    """Get all user requests on a TOPdesk incident.

    Parameters:
        incident_id: The UUID or incident number of the TOPdesk incident whose requests to retrieve.
    """
    if not incident_id or not str(incident_id).strip():
        raise MCPError("Incident ID must be provided and cannot be empty", -32602)
    
    return topdesk_client.incident.request.get_list(incident=incident_id)

@mcp.tool(
    description="Create a new TOPdesk incident.",
    input_schema={
        "type": "object",
        "properties": {
            "caller_id": {
                "type": "string",
                "description": "The ID of the caller creating the incident."
            },
            "incident_fields": {
                "type": "object",
                "description": "A dictionary of fields for the new incident.",
                "properties": {
                    "briefDescription": {"type": "string", "description": "Brief description of the incident"},
                    "request": {"type": "string", "description": "Detailed description of the incident"}
                }
            }
        },
        "required": ["caller_id", "incident_fields"]
    }
)
@handle_mcp_error
def topdesk_create_incident(caller_id: str, incident_fields: dict) -> dict:
    """Create a new TOPdesk incident.

    Parameters:
        caller_id: The ID of the caller creating the incident.
        incident_fields: A dictionary of fields for the new incident.
    """
    if not caller_id or not str(caller_id).strip():
        raise MCPError("Caller ID must be provided and cannot be empty", -32602)
    
    if not incident_fields or not isinstance(incident_fields, dict):
        raise MCPError("Incident fields must be provided as a dictionary", -32602)
    
    return topdesk_client.incident.create(caller=caller_id, **incident_fields)

@mcp.tool(
    description="Archive a TOPdesk incident.",
    input_schema={
        "type": "object",
        "properties": {
            "incident_id": {
                "type": "string",
                "description": "The UUID or incident number of the TOPdesk incident to archive."
            }
        },
        "required": ["incident_id"]
    }
)
@handle_mcp_error
def topdesk_archive_incident(incident_id: str) -> dict:
    """Archive a TOPdesk incident.

    Parameters:
        incident_id: The UUID or incident number of the TOPdesk incident to archive.
    """
    if not incident_id or not str(incident_id).strip():
        raise MCPError("Incident ID must be provided and cannot be empty", -32602)
    
    return topdesk_client.incident.archive(incident=incident_id)

@mcp.tool(
    description="Unarchive a TOPdesk incident.",
    input_schema={
        "type": "object",
        "properties": {
            "incident_id": {
                "type": "string",
                "description": "The UUID or incident number of the TOPdesk incident to unarchive."
            }
        },
        "required": ["incident_id"]
    }
)
@handle_mcp_error
def topdesk_unarchive_incident(incident_id: str) -> dict:
    """Unarchive a TOPdesk incident.

    Parameters:
        incident_id: The UUID or incident number of the TOPdesk incident to unarchive.
    """
    if not incident_id or not str(incident_id).strip():
        raise MCPError("Incident ID must be provided and cannot be empty", -32602)
    
    return topdesk_client.incident.unarchive(incident=incident_id)

@mcp.tool(
    description="Get all time spent entries for a TOPdesk incident.",
    input_schema={
        "type": "object",
        "properties": {
            "incident_id": {
                "type": "string",
                "description": "The UUID or incident number of the TOPdesk incident."
            }
        },
        "required": ["incident_id"]
    }
)
@handle_mcp_error
def topdesk_get_timespent_on_incident(incident_id: str) -> list:
    """Get all time spent entries for a TOPdesk incident.

    Parameters:
        incident_id: The UUID or incident number of the TOPdesk incident.
    """
    if not incident_id or not str(incident_id).strip():
        raise MCPError("Incident ID must be provided and cannot be empty", -32602)
    
    return topdesk_client.incident.timespent.get(incident=incident_id)

@mcp.tool(
    description="Register time spent on a TOPdesk incident.",
    input_schema={
        "type": "object",
        "properties": {
            "incident_id": {
                "type": "string",
                "description": "The UUID or incident number of the TOPdesk incident."
            },
            "time_spent": {
                "type": "integer",
                "description": "Time spent in minutes.",
                "minimum": 1
            }
        },
        "required": ["incident_id", "time_spent"]
    }
)
@handle_mcp_error
def topdesk_register_timespent_on_incident(incident_id: str, time_spent: int) -> dict:
    """Register time spent on a TOPdesk incident.

    Parameters:
        incident_id: The UUID or incident number of the TOPdesk incident.
        time_spent: Time spent in minutes.
    """
    if not incident_id or not str(incident_id).strip():
        raise MCPError("Incident ID must be provided and cannot be empty", -32602)
    
    if not isinstance(time_spent, int) or time_spent < 1:
        raise MCPError("Time spent must be a positive integer (minutes)", -32602)
    
    return topdesk_client.incident.timespent.register(incident=incident_id, timespent=time_spent)

@mcp.tool(
    description="Escalate a TOPdesk incident.",
    input_schema={
        "type": "object",
        "properties": {
            "incident_id": {
                "type": "string",
                "description": "The UUID or incident number of the TOPdesk incident to escalate."
            },
            "reason_id": {
                "type": "string",
                "description": "The ID of the escalation reason."
            }
        },
        "required": ["incident_id", "reason_id"]
    }
)
@handle_mcp_error
def topdesk_escalate_incident(incident_id: str, reason_id: str) -> dict:
    """Escalate a TOPdesk incident.

    Parameters:
        incident_id: The UUID or incident number of the TOPdesk incident to escalate.
        reason_id: The ID of the escalation reason.
    """
    if not incident_id or not str(incident_id).strip():
        raise MCPError("Incident ID must be provided and cannot be empty", -32602)
    
    if not reason_id or not str(reason_id).strip():
        raise MCPError("Reason ID must be provided and cannot be empty", -32602)
    
    return topdesk_client.incident.escalate(incident=incident_id, reason=reason_id)

@mcp.tool(
    description="Get all available escalation reasons for a TOPdesk incident.",
    input_schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
@handle_mcp_error
def topdesk_get_available_escalation_reasons() -> list:
    """Get all available escalation reasons for a TOPdesk incident.

    (No parameters)
    """
    return topdesk_client.incident.escalation_reasons()

@mcp.tool(
    description="Get all available de-escalation reasons for a TOPdesk incident.",
    input_schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
@handle_mcp_error
def topdesk_get_available_deescalation_reasons() -> list:
    """Get all available de-escalation reasons for a TOPdesk incident.

    (No parameters)
    """
    return topdesk_client.incident.deescalation_reasons()

@mcp.tool(
    description="De-escalate a TOPdesk incident.",
    input_schema={
        "type": "object",
        "properties": {
            "incident_id": {
                "type": "string",
                "description": "The UUID or incident number of the TOPdesk incident to de-escalate."
            },
            "reason_id": {
                "type": "string",
                "description": "The ID of the de-escalation reason."
            }
        },
        "required": ["incident_id", "reason_id"]
    }
)
@handle_mcp_error
def topdesk_deescalate_incident(incident_id: str, reason_id: str) -> dict:
    """De-escalate a TOPdesk incident.

    Parameters:
        incident_id: The UUID or incident number of the TOPdesk incident to de-escalate.
        reason_id: The ID of the de-escalation reason.
    """
    if not incident_id or not str(incident_id).strip():
        raise MCPError("Incident ID must be provided and cannot be empty", -32602)
    
    if not reason_id or not str(reason_id).strip():
        raise MCPError("Reason ID must be provided and cannot be empty", -32602)
    
    return topdesk_client.incident.deescalate(incident=incident_id, reason_id=reason_id)

@mcp.tool(
    description="Get the progress trail for a TOPdesk incident.",
    input_schema={
        "type": "object",
        "properties": {
            "incident_id": {
                "type": "string",
                "description": "The UUID or incident number of the TOPdesk incident."
            },
            "inlineimages": {
                "type": "boolean",
                "description": "Whether to include inline images in the progress trail.",
                "default": True
            },
            "force_images_as_data": {
                "type": "boolean",
                "description": "Whether to force images to be returned as base64 data.",
                "default": True
            }
        },
        "required": ["incident_id"]
    }
)
@handle_mcp_error
def topdesk_get_progress_trail(incident_id: str, inlineimages: bool=True, force_images_as_data: bool=True) -> list:
    """Get the progress trail for a TOPdesk incident.

    Parameters:
        incident_id: The UUID or incident number of the TOPdesk incident.
        force_images_as_data: Whether to force images to be returned as base64 data. Defaults to True.
        inlineimages: Whether to include inline images in the progress trail. Defaults to True.
    """
    if not incident_id or not str(incident_id).strip():
        raise MCPError("Incident ID must be provided and cannot be empty", -32602)
    
    return topdesk_client.incident.get_progress_trail(
        incident=incident_id, 
        inlineimages=inlineimages,
        force_images_as_data=force_images_as_data
    )

@mcp.tool(
    description="Get all attachments for a TOPdesk incident as base64-encoded data.",
    input_schema={
        "type": "object",
        "properties": {
            "incident_id": {
                "type": "string",
                "description": "The UUID or incident number of the TOPdesk incident."
            }
        },
        "required": ["incident_id"]
    }
)
@handle_mcp_error
def topdesk_get_incident_attachments(incident_id: str) -> list:
    """Get all attachments for a TOPdesk incident.

    Parameters:
        incident_id: The UUID or incident number of the TOPdesk incident.
    """
    if not incident_id or not str(incident_id).strip():
        raise MCPError("Incident ID must be provided and cannot be empty", -32602)
    
    return topdesk_client.incident.attachments.download_attachments(incident=incident_id)

@mcp.tool(
    description="Download and convert all attachments for a TOPdesk incident to Markdown format using intelligent document conversion.",
    input_schema={
        "type": "object",
        "properties": {
            "incident_id": {
                "type": "string",
                "description": "The UUID or incident number of the TOPdesk incident."
            }
        },
        "required": ["incident_id"]
    }
)
@handle_mcp_error
def topdesk_get_incident_attachments_as_markdown(incident_id: str) -> list:
    """Get all attachments for a TOPdesk incident in Markdown format via pytesseract OCR.

    Parameters:
        incident_id: The UUID or incident number of the TOPdesk incident.
    """
    if not incident_id or not str(incident_id).strip():
        raise MCPError("Incident ID must be provided and cannot be empty", -32602)
    
    return topdesk_client.incident.attachments.download_attachments_as_markdown(incident=incident_id)

@mcp.tool(
    description="Get a comprehensive overview of a TOPdesk incident including its details, progress trail, and attachments converted to Markdown.",
    input_schema={
        "type": "object",
        "properties": {
            "incident_id": {
                "type": "string",
                "description": "The UUID or incident number of the TOPdesk incident."
            }
        },
        "required": ["incident_id"]
    }
)
@handle_mcp_error
def topdesk_get_complete_incident_overview(incident_id: str) -> dict:
    """Get a comprehensive overview of a TOPdesk incident including its details, progress trail, and attachments converted to Markdown.

    Parameters:
        incident_id: The UUID or incident number of the TOPdesk incident.
    """
    if not incident_id or not str(incident_id).strip():
        raise MCPError("Incident ID must be provided and cannot be empty", -32602)
    
    # Get incident details
    incident_details = topdesk_client.incident.get_concise(incident=incident_id)
    
    # Get progress trail
    progress_trail = topdesk_client.incident.get_progress_trail(
        incident=incident_id, 
        inlineimages=False,
        force_images_as_data=False
    )

    # Get attachments as markdown
    attachments = topdesk_client.incident.attachments.download_attachments_as_markdown(incident=incident_id)

    # Combine results into a comprehensive overview
    comprehensive_overview = {
        "incident": incident_details,
        "progress_trail": progress_trail,
        "attachments": attachments
    }
    
    return comprehensive_overview

##################
# OPERATORS
##################
@mcp.tool(
    description="Get a list of TOPdesk operator groups that an operator is a member of.",
    input_schema={
        "type": "object",
        "properties": {
            "operator_id": {
                "type": "string",
                "description": "The ID of the TOPdesk operator whose groups to retrieve."
            }
        },
        "required": ["operator_id"]
    }
)
@handle_mcp_error
def topdesk_get_operatorgroups_of_operator(operator_id: str) -> list:
    """Get a list of TOPdesk operator groups that an op is a member of, optionally by FIQL query or leave blank to return all groups.

    Parameters:
        operator_id: The ID of the TOPdesk operator whose groups to retrieve.
    """
    if not operator_id or not str(operator_id).strip():
        raise MCPError("Operator ID must be provided and cannot be empty", -32602)
    
    return topdesk_client.operator.get_operatorgroups(operator_id=operator_id)

@mcp.tool(
    description="Get a TOPdesk operator by ID.",
    input_schema={
        "type": "object",
        "properties": {
            "operator_id": {
                "type": "string",
                "description": "The ID of the TOPdesk operator to retrieve."
            }
        },
        "required": ["operator_id"]
    }
)
@handle_mcp_error
def topdesk_get_operator(operator_id: str) -> dict:
    """Get a TOPdesk operator by ID.

    Parameters:
        operator_id: The ID of the TOPdesk operator to retrieve.
    """
    if not operator_id or not str(operator_id).strip():
        raise MCPError("Operator ID must be provided and cannot be empty", -32602)
    
    return topdesk_client.operator.get(id=operator_id)

@mcp.tool(
    description="Get TOPdesk operators by FIQL query.",
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The FIQL query string to filter operators."
            }
        },
        "required": ["query"]
    }
)
@handle_mcp_error
def topdesk_get_operators_by_fiql_query(query: str) -> list:
    """Get TOPdesk operators by FIQL query.

    Parameters:
        query: The FIQL query string to filter operators.
    """
    if not query or not str(query).strip():
        raise MCPError("FIQL query must be provided and cannot be empty", -32602)
    
    return topdesk_client.operator.get_list(query=query)

##################
# ACTIONS
##################
@mcp.tool(
    description="Add an action (ie, reply/comment) to a TOPdesk incident. Only HTML formatting is supported.",
    input_schema={
        "type": "object",
        "properties": {
            "incident_id": {
                "type": "string",
                "description": "The UUID or incident number of the TOPdesk incident."
            },
            "text": {
                "type": "string",
                "description": "The HTML-formatted content of the action to add."
            }
        },
        "required": ["incident_id", "text"]
    }
)
@handle_mcp_error
def topdesk_add_action_to_incident(incident_id: str, text: str) -> dict:
    """Add an action (ie, reply/comment) to a TOPdesk incident. Only HTML formatting is supported.

    Parameters:
        incident_id: The UUID or incident number of the TOPdesk incident.
        text: The HTML-formatted content of the action to add.
    """
    if not incident_id or not str(incident_id).strip():
        raise MCPError("Incident ID must be provided and cannot be empty", -32602)
    
    if not text or not str(text).strip():
        raise MCPError("Action text must be provided and cannot be empty", -32602)
    
    return topdesk_client.incident.patch(incident=incident_id, action=text)

@mcp.tool(
    description="Get all actions (ie, replies/comments) for a TOPdesk incident.",
    input_schema={
        "type": "object",
        "properties": {
            "incident_id": {
                "type": "string",
                "description": "The UUID or incident number of the TOPdesk incident."
            }
        },
        "required": ["incident_id"]
    }
)
@handle_mcp_error
def topdesk_get_incident_actions(incident_id: str) -> list:
    """Get all actions (ie, replies/comments) for a TOPdesk incident.

    Parameters:
        incident_id: The UUID or incident number of the TOPdesk incident.
    """
    if not incident_id or not str(incident_id).strip():
        raise MCPError("Incident ID must be provided and cannot be empty", -32602)
    
    return topdesk_client.incident.action.get_list(
        incident=incident_id
    )

@mcp.tool(
    description="Delete a specific action (ie, reply/comment) for a TOPdesk incident.",
    input_schema={
        "type": "object",
        "properties": {
            "incident_id": {
                "type": "string",
                "description": "The UUID or incident number of the TOPdesk incident."
            },
            "action_id": {
                "type": "string",
                "description": "The ID of the action to delete."
            }
        },
        "required": ["incident_id", "action_id"]
    }
)
@handle_mcp_error
def topdesk_delete_incident_action(incident_id: str, action_id: str) -> dict:
    """Delete a specific action (ie, reply/comment) for a TOPdesk incident.

    Parameters:
        incident_id: The UUID or incident number of the TOPdesk incident.
        action_id: The ID of the action to delete.
    """
    if not incident_id or not str(incident_id).strip():
        raise MCPError("Incident ID must be provided and cannot be empty", -32602)
    
    if not action_id or not str(action_id).strip():
        raise MCPError("Action ID must be provided and cannot be empty", -32602)
    
    return topdesk_client.incident.action.delete(incident=incident_id, actions_id=action_id)

################
# PERSONS
################
@mcp.tool(
    description="Get TOPdesk persons by FIQL query.",
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The FIQL query string to filter persons."
            }
        },
        "required": ["query"]
    }
)
@handle_mcp_error
def topdesk_get_person_by_query(query: str) -> list:
    """Get TOPdesk persons by FIQL query.

    Parameters:
        query: The FIQL query string to filter persons.
    """
    if not query or not str(query).strip():
        raise MCPError("FIQL query must be provided and cannot be empty", -32602)
    
    return topdesk_client.person.get_list(query=query)

@mcp.tool(
    description="Get a TOPdesk person by ID.",
    input_schema={
        "type": "object",
        "properties": {
            "person_id": {
                "type": "string",
                "description": "The ID of the TOPdesk person to retrieve."
            }
        },
        "required": ["person_id"]
    }
)
@handle_mcp_error
def topdesk_get_person(person_id: str) -> dict:
    """Get a TOPdesk person by ID.

    Parameters:
        person_id: The ID of the TOPdesk person to retrieve.
    """
    if not person_id or not str(person_id).strip():
        raise MCPError("Person ID must be provided and cannot be empty", -32602)
    
    return topdesk_client.person.get(id=person_id)

@mcp.tool(
    description="Create a new TOPdesk person.",
    input_schema={
        "type": "object",
        "properties": {
            "person": {
                "type": "object",
                "description": "A dictionary of person fields to create.",
                "properties": {
                    "email": {"type": "string", "description": "Email address of the person"},
                    "firstName": {"type": "string", "description": "First name of the person"},
                    "surname": {"type": "string", "description": "Surname of the person"},
                    "telephone": {"type": "string", "description": "Telephone number"}
                },
                "required": ["email"]
            }
        },
        "required": ["person"]
    }
)
@handle_mcp_error
def topdesk_create_person(person: dict) -> dict:
    """Create a new TOPdesk person.

    Parameters:
        person: A dictionary of person fields to create.
    """
    if not person or not isinstance(person, dict):
        raise MCPError("Person fields must be provided as a dictionary", -32602)
    
    if not person.get("email"):
        raise MCPError("Person email is required", -32602)
    
    return topdesk_client.person.create(**person)

@mcp.tool(
    description="Update an existing TOPdesk person.",
    input_schema={
        "type": "object",
        "properties": {
            "person_id": {
                "type": "string",
                "description": "The ID of the TOPdesk person to update."
            },
            "updated_fields": {
                "type": "object",
                "description": "A dictionary of fields to update.",
                "properties": {
                    "email": {"type": "string", "description": "Email address"},
                    "firstName": {"type": "string", "description": "First name"},
                    "surname": {"type": "string", "description": "Surname"},
                    "telephone": {"type": "string", "description": "Telephone number"}
                }
            }
        },
        "required": ["person_id", "updated_fields"]
    }
)
@handle_mcp_error
def topdesk_update_person(person_id: str, updated_fields: dict) -> dict:
    """Update an existing TOPdesk person.

    Parameters:
        person_id: The ID of the TOPdesk person to update.
        updated_fields: A dictionary of fields to update.
    """
    if not person_id or not str(person_id).strip():
        raise MCPError("Person ID must be provided and cannot be empty", -32602)
    
    if not updated_fields or not isinstance(updated_fields, dict):
        raise MCPError("Updated fields must be provided as a dictionary", -32602)
    
    return topdesk_client.person.update(person=person_id, **updated_fields)

@mcp.tool(
    description="Archive a TOPdesk person.",
    input_schema={
        "type": "object",
        "properties": {
            "person_id": {
                "type": "string",
                "description": "The ID of the TOPdesk person to archive."
            },
            "reason_id": {
                "type": "string",
                "description": "Optional ID of the archive reason."
            }
        },
        "required": ["person_id"]
    }
)
@handle_mcp_error
def topdesk_archive_person(person_id: str, reason_id: str = None) -> dict:
    """Archive a TOPdesk person.

    Parameters:
        person_id: The ID of the TOPdesk person to archive.
        reason_id: Optional ID of the archive reason.
    """
    if not person_id or not str(person_id).strip():
        raise MCPError("Person ID must be provided and cannot be empty", -32602)
    
    return topdesk_client.person.archive(person_id=person_id, reason_id=reason_id)

@mcp.tool(
    description="Unarchive a TOPdesk person.",
    input_schema={
        "type": "object",
        "properties": {
            "person_id": {
                "type": "string",
                "description": "The ID of the TOPdesk person to unarchive."
            }
        },
        "required": ["person_id"]
    }
)
@handle_mcp_error
def topdesk_unarchive_person(person_id: str) -> dict:
    """Unarchive a TOPdesk person.

    Parameters:
        person_id: The ID of the TOPdesk person to unarchive.
    """
    if not person_id or not str(person_id).strip():
        raise MCPError("Person ID must be provided and cannot be empty", -32602)
    
    return topdesk_client.person.unarchive(person_id=person_id)

def main():
    """Main function to run the MCP server."""
    transport = os.getenv("TOPDESK_MCP_TRANSPORT", "stdio")
    host = os.getenv("TOPDESK_MCP_HOST", "0.0.0.0")
    port = int(os.getenv("TOPDESK_MCP_PORT", 3030))
    
    if transport not in ["stdio", "streamable-http", "sse"]:
        raise ValueError("Invalid transport type. Choose 'stdio', 'streamable-http', or 'sse'.")
    
    # Add logging endpoint for HTTP transports
    if transport in ["streamable-http", "sse"]:
        _add_logging_endpoint(mcp, host, port)
    
    if transport == "stdio":
        mcp.run()    
    else:
        mcp.run(transport=transport, host=host, port=port)

def _add_logging_endpoint(mcp_instance, host: str, port: int):
    """Add a /logging endpoint for HTTP transports."""
    try:
        # Try to access the underlying FastAPI app if available
        if hasattr(mcp_instance, 'app'):
            app = mcp_instance.app
            
            @app.get("/logging")
            async def get_logs(lines: int = 100, level: str = None):
                """HTTP endpoint to access logs."""
                try:
                    result = get_log_entries(lines, level)
                    
                    # Return HTML page
                    html_content = _generate_log_html(result)
                    from fastapi.responses import HTMLResponse
                    return HTMLResponse(content=html_content)
                    
                except Exception as e:
                    from fastapi.responses import JSONResponse
                    return JSONResponse(
                        status_code=500,
                        content={"error": f"Failed to retrieve logs: {str(e)}"}
                    )
            
            @app.get("/logging/json")
            async def get_logs_json(lines: int = 100, level: str = None):
                """HTTP endpoint to access logs as JSON."""
                try:
                    result = get_log_entries(lines, level)
                    from fastapi.responses import JSONResponse
                    return JSONResponse(content=result)
                except Exception as e:
                    from fastapi.responses import JSONResponse
                    return JSONResponse(
                        status_code=500,
                        content={"error": f"Failed to retrieve logs: {str(e)}"}
                    )
                    
            print(f"✅ Logging endpoints added:")
            print(f"   📊 HTML: http://{host}:{port}/logging")
            print(f"   📋 JSON: http://{host}:{port}/logging/json")
            
    except Exception as e:
        # Fallback: just log that we couldn't add the endpoint
        print(f"⚠️  Could not add logging endpoint: {e}")
        print(f"📝 Logs are still accessible via the 'get_log_entries' MCP tool")

def _generate_log_html(log_data: dict) -> str:
    """Generate HTML page for displaying logs."""
    config = log_data.get('configuration', {})
    entries = log_data.get('entries', [])
    message = log_data.get('message', '')
    note = log_data.get('note', '')
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TOPdesk MCP Server - Logs</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
                color: #333;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
            }}
            .controls {{
                padding: 20px;
                border-bottom: 1px solid #eee;
                background: #fafafa;
            }}
            .controls form {{
                display: flex;
                gap: 15px;
                align-items: center;
                flex-wrap: wrap;
            }}
            .controls label {{
                font-weight: 600;
            }}
            .controls input, .controls select {{
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }}
            .controls button {{
                background: #667eea;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                transition: background 0.2s;
            }}
            .controls button:hover {{
                background: #5a67d8;
            }}
            .info {{
                padding: 20px;
                background: #e6f3ff;
                border-left: 4px solid #2196F3;
                margin: 0;
            }}
            .info h3 {{
                margin-top: 0;
                color: #1976D2;
            }}
            .info p {{
                margin: 5px 0;
                font-size: 14px;
            }}
            .warning {{
                padding: 20px;
                background: #fff3cd;
                border-left: 4px solid #ffc107;
                margin: 0;
            }}
            .warning h3 {{
                margin-top: 0;
                color: #856404;
            }}
            .logs {{
                padding: 20px;
            }}
            .log-entry {{
                display: flex;
                padding: 12px;
                border-bottom: 1px solid #eee;
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                font-size: 13px;
                line-height: 1.4;
            }}
            .log-entry:hover {{
                background: #f8f9fa;
            }}
            .log-timestamp {{
                color: #666;
                width: 180px;
                flex-shrink: 0;
                font-weight: 500;
            }}
            .log-level {{
                width: 80px;
                flex-shrink: 0;
                font-weight: bold;
                text-align: center;
                padding: 2px 6px;
                border-radius: 3px;
                margin-right: 10px;
            }}
            .log-level.DEBUG {{ background: #e3f2fd; color: #1976d2; }}
            .log-level.INFO {{ background: #e8f5e8; color: #2e7d2e; }}
            .log-level.WARNING {{ background: #fff3e0; color: #f57c00; }}
            .log-level.ERROR {{ background: #ffebee; color: #d32f2f; }}
            .log-level.CRITICAL {{ background: #fce4ec; color: #c2185b; }}
            .log-logger {{
                color: #7b1fa2;
                width: 150px;
                flex-shrink: 0;
                margin-right: 10px;
            }}
            .log-message {{
                flex: 1;
                word-break: break-word;
            }}
            .empty {{
                text-align: center;
                padding: 60px 20px;
                color: #666;
            }}
            .empty h3 {{
                margin-top: 0;
            }}
            .json-link {{
                text-align: center;
                padding: 20px;
                border-top: 1px solid #eee;
                background: #fafafa;
            }}
            .json-link a {{
                color: #667eea;
                text-decoration: none;
                font-weight: 600;
            }}
            .json-link a:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 TOPdesk MCP Server Logs</h1>
            </div>
            
            <div class="controls">
                <form method="get">
                    <label for="lines">Lines:</label>
                    <input type="number" id="lines" name="lines" value="{config.get('lines_requested', 100)}" min="1" max="1000">
                    
                    <label for="level">Level:</label>
                    <select id="level" name="level">
                        <option value="">All Levels</option>
                        <option value="DEBUG" {"selected" if config.get('level_filter') == 'DEBUG' else ""}>DEBUG</option>
                        <option value="INFO" {"selected" if config.get('level_filter') == 'INFO' else ""}>INFO</option>
                        <option value="WARNING" {"selected" if config.get('level_filter') == 'WARNING' else ""}>WARNING</option>
                        <option value="ERROR" {"selected" if config.get('level_filter') == 'ERROR' else ""}>ERROR</option>
                        <option value="CRITICAL" {"selected" if config.get('level_filter') == 'CRITICAL' else ""}>CRITICAL</option>
                    </select>
                    
                    <button type="submit">Refresh Logs</button>
                </form>
            </div>
    """
    
    if message or note:
        html += f"""
            <div class="warning">
                <h3>⚠️ Notice</h3>
                {f"<p>{message}</p>" if message else ""}
                {f"<p>{note}</p>" if note else ""}
            </div>
        """
    
    if config:
        html += f"""
            <div class="info">
                <h3>ℹ️ Configuration</h3>
                <p><strong>Log File:</strong> {config.get('log_file', 'Not configured')}</p>
                <p><strong>Log Level:</strong> {config.get('log_level', 'INFO')}</p>
                <p><strong>Total Lines in File:</strong> {config.get('total_lines_in_file', 'N/A')}</p>
                <p><strong>Lines Returned:</strong> {config.get('lines_returned', len(entries))}</p>
                {f"<p><strong>Level Filter:</strong> {config.get('level_filter')}</p>" if config.get('level_filter') else ""}
            </div>
        """
    
    if entries:
        html += """
            <div class="logs">
        """
        for entry in entries:
            level_class = entry.get('level', 'INFO')
            html += f"""
                <div class="log-entry">
                    <div class="log-timestamp">{entry.get('timestamp', '')}</div>
                    <div class="log-level {level_class}">{level_class}</div>
                    <div class="log-logger">{entry.get('logger', '')}</div>
                    <div class="log-message">{entry.get('message', '').replace('<', '&lt;').replace('>', '&gt;')}</div>
                </div>
            """
        html += """
            </div>
        """
    else:
        html += """
            <div class="empty">
                <h3>📭 No Log Entries Found</h3>
                <p>No log entries match your current filters, or logging may not be configured properly.</p>
            </div>
        """
    
    html += """
            <div class="json-link">
                <a href="/logging/json">📋 View as JSON</a>
            </div>
        </div>
        
        <script>
            // Auto-refresh every 30 seconds if user wants it
            // setInterval(() => window.location.reload(), 30000);
        </script>
    </body>
    </html>
    """
    
    return html

if __name__ == "__main__":
    main()
