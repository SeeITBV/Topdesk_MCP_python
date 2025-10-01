# topdesk-mcp

This project is a Model Context Protocol (MCP) server implemented in Python. It exposes the Topdesk API via the TOPdeskPy SDK.

## 🚀 ChatGPT Integration (MCP HTTP Interface)

The server now includes MCP-compatible HTTP endpoints that work seamlessly with ChatGPT and other AI assistants!

### Quick Start for ChatGPT

1. **Start the server in HTTP mode:**
   ```bash
   TOPDESK_MCP_TRANSPORT=streamable-http TOPDESK_MCP_PORT=3030 topdesk-mcp
   ```

2. **Available MCP Endpoints:**
   - `GET/POST http://localhost:3030/mcp/list_tools` - List available tools
   - `POST http://localhost:3030/mcp/call_tool` - Execute tool calls

### Example ChatGPT Prompts

Once connected, you can use natural language queries:

```
"Haal de laatste 5 incidenten"
"Toon de laatste 10 changes"  
"Search for incidents with limit 3"
```

### curl Examples

**List available tools:**
```bash
curl http://localhost:3030/mcp/list_tools
```

**Search for incidents:**
```bash
curl -X POST http://localhost:3030/mcp/call_tool \
  -H "Content-Type: application/json" \
  -d '{
    "name": "search",
    "arguments": {
      "entity": "incidents",
      "limit": 5
    }
  }'
```

**Fetch a specific incident:**
```bash
curl -X POST http://localhost:3030/mcp/call_tool \
  -H "Content-Type: application/json" \
  -d '{
    "name": "fetch",
    "arguments": {
      "entity": "incidents",
      "id": "I-2024-001"
    }
  }'
```

**Natural language fallback (Dutch):**
```bash
curl -X POST http://localhost:3030/mcp/call_tool \
  -H "Content-Type: application/json" \
  -d '{"prompt": "haal de laatste 3 incidenten"}'
```

### MCP Tools

The MCP interface exposes two main tools:

- **search**: Search for incidents, changes, or requests
  - Arguments: `entity` (incidents/changes/requests), `query` (optional FIQL), `limit` (1-100)
  - Example: `{"entity": "incidents", "limit": 5}`

- **fetch**: Get detailed information about a specific entity
  - Arguments: `entity` (incidents/changes/requests), `id` (ID or number)
  - Example: `{"entity": "incidents", "id": "I-2024-001"}`

### Response Format

All MCP endpoints return responses in the standard MCP format:

```json
{
  "content": [
    {
      "type": "text",
      "text": "Found 5 incidents",
      "structured": {
        "results": [...],
        "count": 5
      }
    }
  ],
  "isError": false
}
```

### Error Handling

- **400 Bad Request**: Invalid arguments or malformed request
- **500 Internal Server Error**: TOPdesk API errors or server issues
- All responses include `X-Request-Id` header for tracking
- Detailed error messages in `content[0].text`

## 🎉 New: Incidents & Changes Support

The connector now includes dedicated tools for retrieving incidents and changes from TOPdesk:

- **✅ Health Check**: Validate API connectivity via `/tas/api/version`
- **✅ List Open Incidents**: Retrieve open incidents with proper filtering and sorting
- **✅ List Recent Changes**: Automatic fallback between `/changes` and `/operatorChanges`

**Quick Start:** See [QUICKSTART.md](docs/QUICKSTART.md) for usage examples and testing instructions.

**Technical Details:** See [TOPDESK_CONNECTOR_FIXES.md](docs/TOPDESK_CONNECTOR_FIXES.md) for complete implementation documentation.

## Project Purpose
- Acts as an MCP server to bridge MCP clients with the Topdesk API.
- Uses the [TOPdeskPy SDK](https://github.com/TwinkelToe/TOPdeskPy) (with some modifications) for all Topdesk API interactions.

## MCP Config JSON
```
{
  "servers": {
    "topdesk-mcp": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "topdesk-mcp"
      ],
      "env": {
         "TOPDESK_URL": "<your topdesk URL>",
         "TOPDESK_USERNAME": "<your topdesk username>",
         "TOPDESK_PASSWORD": "<your topdesk api key>"
      }
    }
  }
}
```

## Environment Variables
* `TOPDESK_URL`: The base URL of your Topdesk instance. e.g. `https://yourcompany.topdesk.net`
* `TOPDESK_USERNAME`: The username you generated the API token against.
* `TOPDESK_PASSWORD`: Your API token
* `TOPDESK_MCP_TRANSPORT`: (Optional) The transport to use: 'stdio', 'streamable-http', 'sse'. Defaults to 'stdio'.
* `TOPDESK_MCP_HOST`: (Optional) The host to listen on (for 'streamable-http' and 'sse'). Defaults to '0.0.0.0'.
* `TOPDESK_MCP_PORT`: (Optional) The port to listen on (for 'streamable-http' and 'sse'). Defaults to '3030'.
* `LOG_LEVEL`: (Optional) Logging level: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'. Defaults to 'INFO'.
* `LOG_FILE`: (Optional) Path to log file. If not set, logs go to console/stdout.

## 📊 Logging & Monitoring

The server includes comprehensive logging functionality:

- **MCP Tool**: Use `get_log_entries` to retrieve logs programmatically
- **Web Interface**: When using HTTP transport, access `http://localhost:3030/logging` for a web-based log viewer
- **JSON API**: Get logs as JSON at `http://localhost:3030/logging/json`

Features include log filtering by level, line limits, and real-time viewing. See [LOGGING_GUIDE.md](LOGGING_GUIDE.md) for detailed documentation.

## 🧪 HTTP Testing Endpoints

When running in HTTP mode (`TOPDESK_MCP_TRANSPORT=streamable-http`), additional endpoints are available:

- **Test Page**: `http://localhost:3030/test` - Interactive HTML page to test TOPdesk connection and explore tools
- **Connection Test API**: `http://localhost:3030/test/connection` - JSON API for testing TOPdesk connectivity (perfect for Postman)
- **Tools List API**: `http://localhost:3030/tools` - JSON API listing all available MCP tools

See [HTTP_ENDPOINTS.md](HTTP_ENDPOINTS.md) for complete documentation and usage examples.

### Document Conversion Environment Variables
Topdesk Attachments can be converted to Markdown format by the tool. 

By default it will try to do this with simple MarkItDown library which often isn't sufficient.

These variables configure the attachment-to-markdown conversion feature to leverage a Docling or OpenAI instance instead:

* `DOCLING_ADDRESS`: (Optional) URL of a Docling API server for document conversion. e.g. `http://localhost:8080`
* `DOCLING_API_KEY`: (Optional) API key for Docling API authentication
* `DOCLING_USERNAME`: (Optional) Username for Docling API basic authentication (fallback if no API key)
* `DOCLING_PASSWORD`: (Optional) Password for Docling API basic authentication (fallback if no API key)
* `OPENAI_API_BASE`: (Optional) Base URL for OpenAI-compatible API for document conversion. e.g. `https://api.openai.com`
* `OPENAI_API_KEY`: (Optional) API key for OpenAI API authentication
* `OPENAI_MODEL_NAME`: (Optional) Model name to use for OpenAI API calls. Defaults to 'gpt-4.1'
* `SSL_VERIFY`: (Optional) Enable/disable SSL verification for API calls. Set to 'false' to disable. Defaults to 'true'.

## Setup for Local Development
1. Ensure Python 3.11+ is installed.
2. Create and activate a virtual environment:

   ```bash
   pip install uv
   uv venv
   uv pip install -e .
   uv pip install -e ".[dev]"
   ```

4. Run:
   ```bash
   python -m topdesk_mcp.main
   ```
   
### Notes:
* The server skeleton was generated using the official MCP server template.
* Contributions are welcome.

## Deployment

### Quick Start
```bash
# Clone and install
git clone https://github.com/SeeITBV/Topdesk_MCP_python.git
cd Topdesk_MCP_python
pip install -e .

# Configure environment
cp .env.example .env
# Edit .env with your TOPdesk credentials

# Test deployment
python scripts/test_deployment.py

# Run server
topdesk-mcp  # stdio mode
# or
TOPDESK_MCP_TRANSPORT=streamable-http topdesk-mcp  # HTTP mode
```

### Docker Deployment
```bash
# Using docker-compose
docker-compose up -d

# Or build manually
docker build -t topdesk-mcp .
docker run -p 3030:3030 -e TOPDESK_URL="..." -e TOPDESK_USERNAME="..." -e TOPDESK_PASSWORD="..." topdesk-mcp
```

📚 **See [DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) for comprehensive deployment instructions and troubleshooting.**

## Package Structure
```
topdesk_mcp/  # Directory for the MCP server package
    __init__.py     # Marks as a Python package
    main.py         # Entry point for the MCP server
    
    _topdesk_sdk.py # TOPdeskPy SDK
    _incident.py    # Incidents API
    _operator.py    # Operator API
    _person.py      # Person API
    _utils.py       # Helper methods for Requests

    tests/
      (unit tests)
```

## Exposed Tools

### Core Tools

- **list_registered_tools**  
  List all registered MCP tools available in this server.

- **get_log_entries**  
  Get log entries from the TOPdesk MCP server. Can retrieve recent logs or search by level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Useful for monitoring and debugging.

- **topdesk_get_fiql_query_howto**  
  Get a hint on how to construct FIQL queries, with examples.

- **topdesk_get_object_schemas**  
  Get the full object schemas for TOPdesk incidents and all their subfields.

### Incident Management

- **topdesk_list_open_incidents**  
  List open/unresolved incidents from TOPdesk, sorted by most recent modification. Returns normalized incident objects with id, number, title, status, requester, and timestamps.

- **topdesk_get_recent_incidents** *(Convenience Tool)*  
  Get recent incidents with flexible sorting options (by creationDate, modificationDate, or closedDate). Allows 1-100 incidents with explicit sort control.

- **topdesk_get_incident**  
  Get a TOPdesk incident by UUID or by Incident Number (I-xxxxxx-xxx). Both formats are accepted.

- **topdesk_get_incidents_by_fiql_query**  
  Get TOPdesk incidents by FIQL query.

- **topdesk_get_incident_user_requests**  
  Get all user requests on a TOPdesk incident.

- **topdesk_create_incident**  
  Create a new TOPdesk incident.

- **topdesk_archive_incident**  
  Archive a TOPdesk incident.

- **topdesk_unarchive_incident**  
  Unarchive a TOPdesk incident.

- **topdesk_get_timespent_on_incident**  
  Get all time spent entries for a TOPdesk incident.

- **topdesk_register_timespent_on_incident**  
  Register time spent on a TOPdesk incident.

- **topdesk_escalate_incident**  
  Escalate a TOPdesk incident.

- **topdesk_get_available_escalation_reasons**  
  Get all available escalation reasons for a TOPdesk incident.

- **topdesk_get_available_deescalation_reasons**  
  Get all available de-escalation reasons for a TOPdesk incident.

- **topdesk_deescalate_incident**  
  De-escalate a TOPdesk incident.

- **topdesk_get_progress_trail**  
  Get the progress trail for a TOPdesk incident.

- **topdesk_get_incident_attachments**  
  Get all attachments for a TOPdesk incident as base64-encoded data.

- **topdesk_get_incident_attachments_as_markdown**  
  Download and convert all attachments for a TOPdesk incident to Markdown format. Uses intelligent document conversion with support for PDFs, Office documents, images, and other file types. Attempts conversion using OpenAI API (if configured), then Docling API (if configured), and falls back to MarkItDown for local processing.

- **topdesk_get_complete_incident_overview**  
  Get a complete overview of a TOPdesk incident including all actions, progress trail, and attachments in a single call.

### Change Management

- **topdesk_list_recent_changes**  
  List recent changes from TOPdesk. Automatically tries `/changes` endpoint first, falls back to `/operatorChanges` if not available. Returns normalized change objects with id, number, title, status, requester, and timestamps.

- **topdesk_get_recent_changes** *(Convenience Tool)*  
  Get recent changes with flexible sorting options (by creationDate or modificationDate). Allows 1-100 changes with explicit sort control and automatic endpoint fallback.

### Person & Operator Management
  Get a comprehensive overview of a TOPdesk incident including its details, progress trail, and attachments converted to Markdown. This tool combines the results of `topdesk_get_incident`, `topdesk_get_progress_trail`, and `topdesk_get_incident_attachments_as_markdown` into a single response for convenient access to all incident information.

- **topdesk_get_operatorgroups_of_operator**  
  Get a list of TOPdesk operator groups that an op is a member of, optionally by FIQL query or leave blank to return all groups.

- **topdesk_get_operator**  
  Get a TOPdesk operator by ID.

- **topdesk_get_operators_by_fiql_query**  
  Get TOPdesk operators by FIQL query.

- **topdesk_add_action_to_incident**  
  Add an action (ie, reply/comment) to a TOPdesk incident.

- **topdesk_get_incident_actions**  
  Get all actions (ie, replies/comments) for a TOPdesk incident.

- **topdesk_delete_incident_action**  
  Delete a specific action (ie, reply/comment) for a TOPdesk incident.

- **topdesk_get_person_by_query**  
  Get TOPdesk persons by FIQL query.

- **topdesk_get_person**  
  Get a TOPdesk person by ID.

- **topdesk_create_person**  
  Create a new TOPdesk person.

- **topdesk_update_person**  
  Update an existing TOPdesk person.

- **topdesk_archive_person**  
  Archive a TOPdesk person.

- **topdesk_unarchive_person**  
  Unarchive a TOPdesk person.

## Documentation

For comprehensive information about this tool:

### User Guides
- **[MCP Tooling Guide](docs/MCP_TOOLING_GUIDE.md)** - 📚 **START HERE** - Comprehensive guide to all 33 MCP tools with prompting examples
- **[Quick Reference Guide](docs/MCP_QUICK_REFERENCE.md)** - 🚀 Concise reference for all tools and common patterns

### Technical Documentation
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - Setup, usage examples, and development workflow
- **[Codebase Documentation](docs/CODEBASE_DOCUMENTATION.md)** - Complete architecture, design patterns, and technical details
- **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - Comprehensive deployment instructions and troubleshooting

### Reference Materials
- **[FIQL Query Guide](topdesk_mcp/resources/fiql_query_howto.md)** - TOPdesk query language reference
- **[Object Schemas](topdesk_mcp/resources/object_schemas.yaml)** - Complete API object definitions

## References
- [MCP Protocol Documentation](https://modelcontextprotocol.io/llms-full.txt)
- [TOPdeskPy SDK](https://github.com/TwinkelToe/TOPdeskPy)
- [FastMCP](https://github.com/jlowin/fastmcp)

## License
MIT license.
