# TOPdesk MCP Python - Developer Guide

## Quick Start

### Prerequisites
- Python 3.11 or higher
- TOPdesk instance with API access
- API credentials (username and API token)

### Installation & Setup

```bash
# Install via pip
pip install topdesk-mcp

# Or install from source
git clone https://github.com/SeeITBV/Topdesk_MCP_python.git
cd Topdesk_MCP_python
pip install -e .
```

### Basic Configuration

Create a `.env` file or set environment variables:

```bash
# Required
export TOPDESK_URL="https://yourcompany.topdesk.net"
export TOPDESK_USERNAME="your_username"
export TOPDESK_PASSWORD="your_api_token"

# Optional
export TOPDESK_MCP_TRANSPORT="stdio"  # stdio|streamable-http|sse
export LOG_LEVEL="INFO"
```

### Running the Server

```bash
# Standard MCP stdio mode (for Claude Desktop)
topdesk-mcp

# HTTP mode for web applications
TOPDESK_MCP_TRANSPORT=streamable-http topdesk-mcp

# Development mode with debug logging
LOG_LEVEL=DEBUG topdesk-mcp
```

## MCP Client Configuration

### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "topdesk-mcp": {
      "command": "topdesk-mcp",
      "env": {
        "TOPDESK_URL": "https://yourcompany.topdesk.net",
        "TOPDESK_USERNAME": "your_username",
        "TOPDESK_PASSWORD": "your_api_token"
      }
    }
  }
}
```

### Using uvx (Recommended)

```json
{
  "mcpServers": {
    "topdesk-mcp": {
      "command": "uvx",
      "args": ["topdesk-mcp"],
      "env": {
        "TOPDESK_URL": "https://yourcompany.topdesk.net",
        "TOPDESK_USERNAME": "your_username",
        "TOPDESK_PASSWORD": "your_api_token"
      }
    }
  }
}
```

## Common Usage Patterns

### Basic Incident Management

```python
# Search for incidents
incidents = search(query="printer offline", max_results=10)

# Get specific incident
incident = fetch("I-240101-001")  # or UUID

# Create new incident
new_incident = topdesk_create_incident(
    caller_id="person-uuid",
    incident_fields={
        "briefDescription": "Printer not working",
        "request": "The office printer is not responding"
    }
)
```

### Advanced Querying with FIQL

```python
# Get FIQL help
fiql_help = topdesk_get_fiql_query_howto()

# Complex incident search
incidents = topdesk_get_incidents_by_fiql_query(
    "status=secondLine;operatorGroup.name=='IT Support'"
)

# Date range queries
recent_incidents = topdesk_get_incidents_by_fiql_query(
    "creationDate=ge=2024-01-01T00:00:00Z"
)
```

### Working with Attachments

```python
# Get attachments as base64 data
attachments = topdesk_get_incident_attachments("incident-uuid")

# Convert attachments to markdown
markdown_attachments = topdesk_get_incident_attachments_as_markdown("incident-uuid")

# Get complete incident overview with all data
complete_overview = topdesk_get_complete_incident_overview("incident-uuid")
```

## Development Workflow

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/SeeITBV/Topdesk_MCP_python.git
cd Topdesk_MCP_python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
python -m pytest topdesk_mcp/tests/ -v

# Run with coverage
python -m pytest --cov=topdesk_mcp topdesk_mcp/tests/
```

### Testing

#### Running Tests

```bash
# All tests
python -m pytest

# Specific test file
python -m pytest topdesk_mcp/tests/test_utils.py

# With verbose output
python -m pytest -v

# With coverage report
python -m pytest --cov=topdesk_mcp --cov-report=html
```

#### Test Structure

Tests are organized by module:
- `test_main_tools.py` - MCP tool function tests
- `test_utils.py` - Utility function tests  
- `test_python_sdk.py` - SDK integration tests
- `conftest.py` - Test configuration and fixtures

### Code Style and Quality

The project follows Python best practices:

```bash
# Code formatting (if using black)
black topdesk_mcp/

# Linting (if using flake8)
flake8 topdesk_mcp/

# Type checking (if using mypy)
mypy topdesk_mcp/
```

## Advanced Configuration

### Document Conversion Setup

For enhanced attachment processing, configure external services:

#### Docling API Setup

```bash
# Docker deployment
docker run -p 8080:8080 docling/docling-api

# Environment configuration
export DOCLING_ADDRESS="http://localhost:8080"
export DOCLING_API_KEY="your_api_key"  # If authentication required
```

#### OpenAI API Setup

```bash
export OPENAI_API_BASE="https://api.openai.com"
export OPENAI_API_KEY="your_openai_key"
export OPENAI_MODEL_NAME="gpt-4o"
```

### Transport Configuration

#### HTTP Transport

```bash
export TOPDESK_MCP_TRANSPORT="streamable-http"
export TOPDESK_MCP_HOST="0.0.0.0"
export TOPDESK_MCP_PORT="3030"
```

#### Server-Sent Events

```bash
export TOPDESK_MCP_TRANSPORT="sse"
export TOPDESK_MCP_HOST="0.0.0.0"
export TOPDESK_MCP_PORT="3030"
```

## Troubleshooting

### Common Issues

#### Authentication Errors

```
RuntimeError: Missing TOPdesk credentials
```
**Solution**: Ensure all required environment variables are set:
- `TOPDESK_URL`
- `TOPDESK_USERNAME` 
- `TOPDESK_PASSWORD`

#### Connection Issues

```
requests.exceptions.ConnectionError
```

**Solutions**:
1. Verify TOPdesk URL is correct and accessible
2. Check network connectivity
3. Verify API credentials are valid
4. Check TOPdesk instance is online

#### Document Conversion Issues

```
Error processing attachment with Docling: Connection refused
```

**Solutions**:
1. Ensure Docling service is running if configured
2. Check `DOCLING_ADDRESS` environment variable
3. Verify API key is correct
4. Falls back to MarkItDown if external services fail

### Debug Mode

Enable detailed logging:

```bash
export LOG_LEVEL="DEBUG"
export LOG_FILE="/tmp/topdesk-mcp.log"
```

### Performance Issues

#### Large Result Sets

For queries returning many results, use pagination:

```python
# Use FIQL with limit
incidents = topdesk_get_incidents_by_fiql_query("status=open")  # Handles pagination automatically

# Or use search with max_results
incidents = search(query="printer", max_results=50)
```

#### Attachment Processing

Large attachments may cause timeout issues:

```python
# Process attachments individually
attachments = topdesk_get_incident_attachments("incident-id")
for attachment in attachments:
    # Process one at a time
    pass
```

## API Reference Quick Guide

### Most Used Functions

#### Incident Operations
- `topdesk_get_incident(incident_id, concise=True)` - Get incident details
- `topdesk_get_incidents_by_fiql_query(query)` - Search incidents
- `topdesk_create_incident(caller_id, incident_fields)` - Create incident
- `topdesk_add_action_to_incident(incident_id, action_text)` - Add comment

#### Person Operations
- `topdesk_get_person_by_query(query)` - Search persons
- `topdesk_get_person(person_id)` - Get person details
- `topdesk_create_person(person_data)` - Create person

#### Utility Functions
- `topdesk_get_fiql_query_howto()` - FIQL syntax help
- `topdesk_get_object_schemas()` - Object schema reference
- `list_registered_tools()` - List all available tools

### Return Value Patterns

Most functions return:
- **Success**: Dictionary or list with data
- **Error**: String with error description
- **Not Found**: Empty list or "Not found" message

## Contributing

### Adding New Tools

1. Add function to `main.py` with `@mcp.tool()` decorator
2. Implement functionality using SDK classes
3. Add appropriate error handling
4. Write tests in appropriate test file
5. Update documentation

Example:

```python
@mcp.tool()
def topdesk_new_function(param: str) -> dict:
    """Description of the new function."""
    try:
        result = topdesk_client.module.operation(param)
        return result
    except Exception as e:
        return f"Error: {str(e)}"
```

### Extending SDK Functionality

1. Add methods to appropriate module (`_incident.py`, `_person.py`, etc.)
2. Use existing utility patterns from `_utils.py`
3. Follow existing error handling patterns
4. Add comprehensive tests

### Documentation Updates

1. Update `README.md` for user-facing changes
2. Update `CODEBASE_DOCUMENTATION.md` for architectural changes
3. Update this guide for development process changes
4. Update docstrings for all new functions

## Best Practices

### Error Handling

```python
try:
    result = topdesk_client.incident.get(incident_id)
    return result
except Exception as e:
    logger.error(f"Error getting incident {incident_id}: {e}")
    return f"Error: {str(e)}"
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)
logger.debug("Starting operation")
logger.info("Operation completed successfully")
logger.error("Operation failed: %s", error_message)
```

### Configuration

Use environment variables with sensible defaults:

```python
transport = os.getenv("TOPDESK_MCP_TRANSPORT", "stdio")
port = int(os.getenv("TOPDESK_MCP_PORT", 3030))
```

This developer guide provides practical information for setting up, using, and extending the TOPdesk MCP Python tool.