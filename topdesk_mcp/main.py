from fastmcp import FastMCP
from topdesk_mcp import _topdesk_sdk as topdesk_sdk
from dotenv import load_dotenv
import os
import logging
from types import MethodType
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
    decorator = _original_tool(*args, **kwargs)

    def wrapper(func):
        registered = decorator(func)
        metadata = getattr(registered, "__mcp_tool__", None)
        tool_name = kwargs.get("name") or getattr(registered, "__name__", func.__name__)
        description = kwargs.get("description")
        input_schema = kwargs.get("input_schema") or kwargs.get("schema")

        if isinstance(metadata, dict):
            tool_name = metadata.get("name", tool_name)
            description = metadata.get("description", description)
            input_schema = metadata.get("input_schema") or metadata.get("inputSchema") or input_schema
        else:
            metadata = None

        if description is None:
            description = registered.__doc__ or ""

        _REGISTERED_TOOLS[tool_name] = {
            "callable": registered,
            "metadata": metadata,
            "name": tool_name,
            "description": description,
            "input_schema": input_schema,
        }

        return registered

    return wrapper


mcp.tool = MethodType(_registering_tool, mcp)


def _register_list_tools(handler):
    """Register the list tools handler in a version agnostic way."""

    decorator = getattr(mcp, "list_tools", None)

    if callable(decorator):
        return decorator()(handler)

    for attr_name in ("register_list_tools_handler", "set_list_tools_handler"):
        registrar = getattr(mcp, attr_name, None)
        if callable(registrar):
            registrar(handler)
            return handler

    get_tools_method = getattr(mcp, "get_tools", None)

    if callable(get_tools_method):
        def patched_get_tools(self, *args, **kwargs):
            return handler(*args, **kwargs)

        mcp.get_tools = MethodType(patched_get_tools, mcp)
        return handler

    raise AttributeError("FastMCP instance does not support list tools registration")


@_register_list_tools
def list_registered_tools(_request: ListToolsRequest | None = None):
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

            if tool_info.get("input_schema") is not None:
                tool_entry["input_schema"] = tool_info["input_schema"]

            collected.append(tool_entry)

    return collected

    
###################
# HINTS
###################
@mcp.tool(
    description="Get a hint on how to construct FIQL queries, with examples.",
    input_schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
@handle_mcp_error
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
            }
        },
        "required": ["query"]
    }
)
@handle_mcp_error
def topdesk_get_incidents_by_fiql_query(query: str) -> list:
    """Get TOPdesk incidents by FIQL query.

    Parameters:
        query: The FIQL query string to filter incidents.
    """
    if not query or not str(query).strip():
        raise MCPError("FIQL query must be provided and cannot be empty", -32602)
    
    return topdesk_client.incident.get_list(query=query)



def _normalise_title(title: str) -> str:
    """Normalise and validate an incident title provided by a user."""
    if title is None:
        raise MCPError("Incident title must be provided", -32602)

    # Collapse whitespace and strip leading/trailing spaces
    normalised = " ".join(title.split())
    if not normalised:
        raise MCPError("Incident title must not be empty", -32602)
    return normalised


@mcp.tool(
    description="Search Codex for incidents by their title (briefDescription).",
    input_schema={
        "type": "object",
        "properties": {
            "title": {
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
        "required": ["title"]
    }
)
@handle_mcp_error
def search(title: str, max_results: int = 5) -> List[Dict[str, str | None]]:
    """Search Codex for incidents by their title (briefDescription).

    Parameters:
        title: The (partial) title of the incident to look up.
        max_results: Maximum number of matches to return. Defaults to 5.

    Returns:
        A list of dictionaries containing incident identifiers and summary fields.
    """

    normalised_title = _normalise_title(title)
    # Escape double quotes to avoid breaking FIQL queries
    escaped_title = normalised_title.replace('"', '\\"')
    fiql_query = f"briefDescription==*{escaped_title}*"

    incidents = topdesk_client.incident.get_list(query=fiql_query)

    results: List[Dict[str, str | None]] = []
    for incident in incidents[:max_results]:
        processing_status = incident.get("processingStatus")
        if isinstance(processing_status, dict):
            processing_status_value = processing_status.get("name")
        else:
            processing_status_value = processing_status

        results.append(
            {
                "id": incident.get("id"),
                "number": incident.get("number"),
                "title": incident.get("briefDescription"),
                "processingStatus": processing_status_value,
            }
        )

    return results


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
def fetch(incident_id: str, concise: bool = True) -> dict:
    """Get a TOPdesk incident by UUID or by Incident Number (I-xxxxxx-xxx). Both formats are accepted.

    Parameters:
        incident_id: The UUID or incident number of the TOPdesk incident to retrieve.
        concise: Whether to return a concise version of the incident. Defaults to True.
    """
    if incident_id is None or not str(incident_id).strip():
        raise MCPError("Incident ID must be provided and cannot be empty", -32602)

    if concise:
        return topdesk_client.incident.get_concise(incident=incident_id)
    else:
        return topdesk_client.incident.get(incident=incident_id)


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

@mcp.tool()
def topdesk_archive_incident(incident_id: str) -> dict:
    """Archive a TOPdesk incident.

    Parameters:
        incident_id: The UUID or incident number of the TOPdesk incident to archive.
    """
    return topdesk_client.incident.archive(incident=incident_id)

@mcp.tool()
def topdesk_unarchive_incident(incident_id: str) -> dict:
    """Unarchive a TOPdesk incident.

    Parameters:
        incident_id: The UUID or incident number of the TOPdesk incident to unarchive.
    """
    return topdesk_client.incident.unarchive(incident=incident_id)

@mcp.tool()
def topdesk_get_timespent_on_incident(incident_id: str) -> list:
    """Get all time spent entries for a TOPdesk incident.

    Parameters:
        incident_id: The UUID or incident number of the TOPdesk incident.
    """
    return topdesk_client.incident.timespent.get(incident=incident_id)

@mcp.tool()
def topdesk_register_timespent_on_incident(incident_id: str, time_spent: int) -> dict:
    """Register time spent on a TOPdesk incident.

    Parameters:
        incident_id: The UUID or incident number of the TOPdesk incident.
        time_spent: Time spent in minutes.
    """
    return topdesk_client.incident.timespent.register(incident=incident_id, timespent=time_spent)

@mcp.tool()
def topdesk_escalate_incident(incident_id: str, reason_id: str) -> dict:
    """Escalate a TOPdesk incident.

    Parameters:
        incident_id: The UUID or incident number of the TOPdesk incident to escalate.
        reason_id: The ID of the escalation reason.
    """
    return topdesk_client.incident.escalate(incident=incident_id, reason=reason_id)

@mcp.tool()
def topdesk_get_available_escalation_reasons() -> list:
    """Get all available escalation reasons for a TOPdesk incident.

    (No parameters)
    """
    return topdesk_client.incident.escalation_reasons()

@mcp.tool()
def topdesk_get_available_deescalation_reasons() -> list:
    """Get all available de-escalation reasons for a TOPdesk incident.

    (No parameters)
    """
    return topdesk_client.incident.deescalation_reasons()

@mcp.tool()
def topdesk_deescalate_incident(incident_id: str, reason_id: str) -> dict:
    """De-escalate a TOPdesk incident.

    Parameters:
        incident_id: The UUID or incident number of the TOPdesk incident to de-escalate.
        reason_id: The ID of the de-escalation reason.
    """
    return topdesk_client.incident.deescalate(incident=incident_id, reason_id=reason_id)

@mcp.tool()
def topdesk_get_progress_trail(incident_id: str, inlineimages: bool=True, force_images_as_data: bool=True) -> list:
    """Get the progress trail for a TOPdesk incident.

    Parameters:
        incident_id: The UUID or incident number of the TOPdesk incident.
        force_images_as_data: Whether to force images to be returned as base64 data. Defaults to True.
        inlineimages: Whether to include inline images in the progress trail. Defaults to True.
    """
    return topdesk_client.incident.get_progress_trail(
        incident=incident_id, 
        inlineimages=inlineimages,
        force_images_as_data=force_images_as_data
    )

@mcp.tool()
def topdesk_get_incident_attachments(incident_id: str) -> list:
    """Get all attachments for a TOPdesk incident.

    Parameters:
        incident_id: The UUID or incident number of the TOPdesk incident.
    """
    return topdesk_client.incident.attachments.download_attachments(incident=incident_id)

@mcp.tool()
def topdesk_get_incident_attachments_as_markdown(incident_id: str) -> list:
    """Get all attachments for a TOPdesk incident in Markdown format via pytesseract OCR.

    Parameters:
        incident_id: The UUID or incident number of the TOPdesk incident.
    """
    return topdesk_client.incident.attachments.download_attachments_as_markdown(incident=incident_id)

@mcp.tool()
def topdesk_get_complete_incident_overview(incident_id: str) -> dict:
    """Get a comprehensive overview of a TOPdesk incident including its details, progress trail, and attachments converted to Markdown.

    Parameters:
        incident_id: The UUID or incident number of the TOPdesk incident.
    """
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
@mcp.tool()
def topdesk_get_operatorgroups_of_operator(operator_id: str) -> list:
    """Get a list of TOPdesk operator groups that an op is a member of, optionally by FIQL query or leave blank to return all groups.

    Parameters:
        operator_id: The ID of the TOPdesk operator whose groups to retrieve.
    """
    return topdesk_client.operator.get_operatorgroups(operator_id=operator_id)

@mcp.tool()
def topdesk_get_operator(operator_id: str) -> dict:
    """Get a TOPdesk operator by ID.

    Parameters:
        operator_id: The ID of the TOPdesk operator to retrieve.
    """
    return topdesk_client.operator.get(id=operator_id)

@mcp.tool()
def topdesk_get_operators_by_fiql_query(query: str) -> list:
    """Get TOPdesk operators by FIQL query.

    Parameters:
        query: The FIQL query string to filter operators.
    """
    return topdesk_client.operator.get_list(query=query)

##################
# ACTIONS
##################
@mcp.tool()
def topdesk_add_action_to_incident(incident_id: str, text: str) -> dict:
    """Add an action (ie, reply/comment) to a TOPdesk incident. Only HTML formatting is supported.

    Parameters:
        incident_id: The UUID or incident number of the TOPdesk incident.
        text: The HTML-formatted content of the action to add.
    """
    return topdesk_client.incident.patch(incident=incident_id, action=text)

@mcp.tool()
def topdesk_get_incident_actions(incident_id: str) -> list:
    """Get all actions (ie, replies/comments) for a TOPdesk incident.

    Parameters:
        incident_id: The UUID or incident number of the TOPdesk incident.
    """
    return topdesk_client.incident.action.get_list(
        incident=incident_id
    )

@mcp.tool()
def topdesk_delete_incident_action(incident_id: str, action_id: str) -> dict:
    """Delete a specific action (ie, reply/comment) for a TOPdesk incident.

    Parameters:
        incident_id: The UUID or incident number of the TOPdesk incident.
        action_id: The ID of the action to delete.
    """
    return topdesk_client.incident.action.delete(incident=incident_id, actions_id=action_id)

################
# PERSONS
################
@mcp.tool()
def topdesk_get_person_by_query(query: str) -> list:
    """Get TOPdesk persons by FIQL query.

    Parameters:
        query: The FIQL query string to filter persons.
    """
    return topdesk_client.person.get_list(query=query)

@mcp.tool()
def topdesk_get_person(person_id: str) -> dict:
    """Get a TOPdesk person by ID.

    Parameters:
        person_id: The ID of the TOPdesk person to retrieve.
    """
    return topdesk_client.person.get(id=person_id)

@mcp.tool()
def topdesk_create_person(person: dict) -> dict:
    """Create a new TOPdesk person.

    Parameters:
        person: A dictionary of person fields to create.
    """
    return topdesk_client.person.create(**person)

@mcp.tool()
def topdesk_update_person(person_id: str, updated_fields: dict) -> dict:
    """Update an existing TOPdesk person.

    Parameters:
        person_id: The ID of the TOPdesk person to update.
        updated_fields: A dictionary of fields to update.
    """
    return topdesk_client.person.update(person=person_id, **updated_fields)

@mcp.tool()
def topdesk_archive_person(person_id: str, reason_id: str = None) -> dict:
    """Archive a TOPdesk person.

    Parameters:
        person_id: The ID of the TOPdesk person to archive.
        reason_id: Optional ID of the archive reason.
    """
    return topdesk_client.person.archive(person_id=person_id, reason_id=reason_id)

@mcp.tool()
def topdesk_unarchive_person(person_id: str) -> dict:
    """Unarchive a TOPdesk person.

    Parameters:
        person_id: The ID of the TOPdesk person to unarchive.
    """
    return topdesk_client.person.unarchive(person_id=person_id)

def main():
    """Main function to run the MCP server."""
    transport = os.getenv("TOPDESK_MCP_TRANSPORT", "stdio")
    host = os.getenv("TOPDESK_MCP_HOST", "0.0.0.0")
    port = int(os.getenv("TOPDESK_MCP_PORT", 3030))
    
    if transport not in ["stdio", "streamable-http", "sse"]:
        raise ValueError("Invalid transport type. Choose 'stdio', 'streamable-http', or 'sse'.")
    
    if transport == "stdio":
        mcp.run()    
    else:
        mcp.run(transport=transport, host=host, port=port)

if __name__ == "__main__":
    main()
