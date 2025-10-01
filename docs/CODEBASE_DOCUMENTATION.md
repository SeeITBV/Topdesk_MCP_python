# TOPdesk MCP Python - Comprehensive Codebase Documentation

## Overview

The TOPdesk MCP Python tool is a Model Context Protocol (MCP) server implementation that provides a bridge between MCP clients (like Claude Desktop, IDEs, or other AI tools) and the TOPdesk API. It acts as a middleware layer that exposes TOPdesk's incident management, person management, and operator functionalities through the standardized MCP protocol.

## Architecture

### High-Level Architecture

The tool follows a layered architecture pattern:

1. **MCP Protocol Layer** (`main.py`) - Handles MCP protocol communication and tool registration
2. **Business Logic Layer** - Tool implementations that orchestrate API calls
3. **API Abstraction Layer** (`_topdesk_sdk.py`, `_incident.py`, `_person.py`, `_operator.py`) - TOPdesk API wrappers
4. **Utility Layer** (`_utils.py`) - HTTP handling, response processing, file conversion

### Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        MCP Client                               │
│                   (Claude Desktop, etc.)                       │
└─────────────────────────┬───────────────────────────────────────┘
                          │ MCP Protocol
┌─────────────────────────▼───────────────────────────────────────┐
│                    main.py (MCP Server)                         │
│  • FastMCP integration  • Tool registration  • Entry point     │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                   TOPdesk SDK Layer                             │
│  _topdesk_sdk.py: Connection management and module orchestration│
└─────────┬───────────────┬───────────────┬───────────────────────┘
          │               │               │
┌─────────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
│ _incident.py   │ │ _person.py  │ │ _operator.py│
│ Incident       │ │ Person      │ │ Operator    │
│ Management     │ │ Management  │ │ Management  │
└─────────┬──────┘ └──────┬──────┘ └──────┬──────┘
          │               │               │
          └───────────────┼───────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                      _utils.py                                  │
│  HTTP requests • Response handling • File conversion            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    TOPdesk REST API                             │
└─────────────────────────────────────────────────────────────────┘
```

## File Structure and Organization

### Core Implementation Files

#### `main.py` (559 lines)
- **Purpose**: MCP server entry point and tool registration
- **Key Components**:
  - FastMCP server initialization
  - Environment variable configuration
  - Tool registration system with metadata tracking
  - 32 MCP tool function definitions
  - Server startup logic with multiple transport options (stdio, HTTP, SSE)

#### `_topdesk_sdk.py` (184 lines)
- **Purpose**: Main SDK connection class and module orchestration
- **Key Components**:
  - `connect` class: Main SDK entry point
  - Authentication handling (base64 encoding)
  - Module initialization for incidents, persons, operators, departments, etc.
  - Logging configuration
  - Multiple entity management sub-classes

#### `_incident.py` (362 lines)
- **Purpose**: Incident management API wrapper
- **Key Components**:
  - `incident` class with comprehensive incident operations
  - Sub-classes for actions, requests, timespent, attachments
  - Concise incident data formatting
  - Attachment processing with markdown conversion
  - FIQL query support for incident searching
  - Progress trail management with image handling

#### `_person.py` (60 lines)
- **Purpose**: Person/user management API wrapper
- **Key Components**:
  - Basic CRUD operations for persons
  - FIQL query support for person searching
  - Archive/unarchive functionality

#### `_operator.py` (100 lines)
- **Purpose**: Operator management API wrapper
- **Key Components**:
  - Operator CRUD operations
  - FIQL query support for operator searching
  - Operator group management

#### `_utils.py` (810 lines)
- **Purpose**: HTTP utilities, response handling, and file conversion
- **Key Components**:
  - HTTP request/response handling
  - Error handling for various HTTP status codes
  - Document conversion via Docling and OpenAI APIs
  - File attachment processing
  - Pagination handling for partial content responses

### Resource Files

#### `resources/fiql_query_howto.md`
- Comprehensive FIQL (Feed Item Query Language) documentation
- Query syntax examples and operations
- Field-specific query examples for incidents

#### `resources/object_schemas.yaml`
- Complete schema definitions for TOPdesk objects
- Incident field specifications with types and examples
- Referenced schemas for related entities

### Testing Infrastructure

#### `tests/` directory
- **`conftest.py` (111 lines)**: Test configuration and stubs for FastMCP/external dependencies
- **`test_main_tools.py` (99 lines)**: Tests for main tool functions
- **`test_utils.py` (713 lines)**: Comprehensive utility function tests
- **`test_python_sdk.py` (288 lines)**: SDK integration tests

## Exposed MCP Tools (32 Total)

The tool exposes 32 MCP functions organized into several categories:

### Documentation and Schema Tools
1. **`topdesk_get_fiql_query_howto`** - Returns FIQL query syntax help
2. **`topdesk_get_object_schemas`** - Returns complete object schemas

### Incident Management Tools (Core)
3. **`topdesk_get_incident`** - Get incident by UUID or number
4. **`topdesk_get_incidents_by_fiql_query`** - Search incidents using FIQL
5. **`search`** - Simple incident search by title
6. **`fetch`** - Alias for getting incident data
7. **`topdesk_create_incident`** - Create new incident
8. **`topdesk_archive_incident`** - Archive incident
9. **`topdesk_unarchive_incident`** - Unarchive incident

### Incident Requests and Communication
10. **`topdesk_get_incident_user_requests`** - Get user requests on incident
11. **`topdesk_add_action_to_incident`** - Add comment/reply to incident
12. **`topdesk_get_incident_actions`** - Get all actions/comments
13. **`topdesk_delete_incident_action`** - Delete specific action/comment

### Time Tracking
14. **`topdesk_get_timespent_on_incident`** - Get time entries
15. **`topdesk_register_timespent_on_incident`** - Register time spent

### Escalation Management
16. **`topdesk_escalate_incident`** - Escalate incident
17. **`topdesk_get_available_escalation_reasons`** - Get escalation reasons
18. **`topdesk_get_available_deescalation_reasons`** - Get de-escalation reasons
19. **`topdesk_deescalate_incident`** - De-escalate incident

### Progress and Status Tracking
20. **`topdesk_get_progress_trail`** - Get progress trail with images
21. **`topdesk_get_complete_incident_overview`** - Complete incident summary

### Attachment Management
22. **`topdesk_get_incident_attachments`** - Get base64-encoded attachments
23. **`topdesk_get_incident_attachments_as_markdown`** - Convert attachments to markdown

### Person Management
24. **`topdesk_get_person_by_query`** - Search persons using FIQL
25. **`topdesk_get_person`** - Get person by ID
26. **`topdesk_create_person`** - Create new person
27. **`topdesk_update_person`** - Update existing person
28. **`topdesk_archive_person`** - Archive person
29. **`topdesk_unarchive_person`** - Unarchive person

### Operator Management
30. **`topdesk_get_operators_by_fiql_query`** - Search operators using FIQL
31. **`topdesk_get_operator`** - Get operator by ID
32. **`list_registered_tools`** - List all available MCP tools

## Key Features and Capabilities

### Advanced Query Support
- **FIQL Integration**: Full support for TOPdesk's Feed Item Query Language
- **Flexible Search**: Multiple search interfaces from simple text to complex queries
- **Pagination Handling**: Automatic handling of paginated API responses

### Document Processing
- **Multi-format Support**: Handles PDFs, images, Word docs, spreadsheets
- **Markdown Conversion**: Converts attachments to LLM-friendly markdown format
- **Multiple Backends**: Support for Docling API, OpenAI API, and MarkItDown fallback
- **Base64 Encoding**: Direct attachment access as encoded data

### Robust Error Handling
- **HTTP Status Management**: Comprehensive handling of 2xx, 4xx, 5xx responses
- **Partial Content Support**: Handles paginated responses (206 status)
- **Graceful Degradation**: Fallback options for document conversion

### Flexible Transport Options
- **Multiple Transports**: stdio (default), HTTP, Server-Sent Events
- **Environment Configuration**: Extensive configuration via environment variables
- **Logging Integration**: Comprehensive logging with configurable levels

## Configuration

### Required Environment Variables
```bash
TOPDESK_URL=https://yourcompany.topdesk.net
TOPDESK_USERNAME=your_username
TOPDESK_PASSWORD=your_api_token
```

### Optional Configuration
```bash
# Transport Configuration
TOPDESK_MCP_TRANSPORT=stdio  # stdio|streamable-http|sse
TOPDESK_MCP_HOST=0.0.0.0     # For HTTP/SSE transport
TOPDESK_MCP_PORT=3030        # For HTTP/SSE transport

# Logging
LOG_LEVEL=INFO
LOG_FILE=/path/to/logfile

# Document Conversion
DOCLING_ADDRESS=http://localhost:8080
DOCLING_API_KEY=your_docling_key
OPENAI_API_BASE=https://api.openai.com
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL_NAME=gpt-4o
```

## Development Setup

### Prerequisites
- Python 3.11+
- pip or uv package manager

### Installation
```bash
# Clone repository
git clone https://github.com/SeeITBV/Topdesk_MCP_python.git
cd Topdesk_MCP_python

# Install dependencies
pip install -e .

# Install development dependencies
pip install -e ".[dev]"

# Run tests
python -m pytest topdesk_mcp/tests/ -v
```

### Running the Server
```bash
# Direct execution
python -m topdesk_mcp.main

# Via installed script
topdesk-mcp

# With custom transport
TOPDESK_MCP_TRANSPORT=streamable-http python -m topdesk_mcp.main
```

## Dependencies

### Core Dependencies
- **fastmcp**: MCP protocol implementation and server framework
- **requests**: HTTP client for API communication
- **markitdown**: Document to markdown conversion fallback

### Development Dependencies
- **pytest**: Testing framework
- **pytest-cov**: Test coverage reporting

### Optional Dependencies (for enhanced document conversion)
- **Docling API**: Advanced document processing
- **OpenAI API**: AI-powered document conversion

## Code Quality and Testing

### Test Coverage
- **Unit Tests**: Comprehensive coverage of utility functions and API wrappers
- **Integration Tests**: SDK integration testing
- **Mocking**: Extensive use of mocks for external API dependencies
- **Stub Support**: Test environment supports stubbed dependencies

### Code Organization
- **Separation of Concerns**: Clear separation between protocol, business logic, and API layers
- **Error Handling**: Consistent error handling patterns throughout
- **Logging**: Comprehensive logging for debugging and monitoring
- **Documentation**: Inline documentation and comprehensive README

## Performance Considerations

### Optimization Features
- **Connection Reuse**: Single SDK connection instance
- **Lazy Loading**: Module initialization on demand
- **Pagination**: Efficient handling of large result sets
- **Caching**: Response caching where appropriate

### Scalability
- **Multiple Transports**: Support for different deployment scenarios
- **Stateless Design**: No server-side state management
- **Resource Management**: Proper cleanup of temporary files and connections

## Security Considerations

### Authentication
- **API Token Support**: Secure token-based authentication
- **Base64 Encoding**: Proper credential encoding
- **Environment Variables**: Secure credential storage

### Data Handling
- **Attachment Processing**: Secure handling of file attachments
- **Temporary Files**: Proper cleanup of temporary processing files
- **Error Sanitization**: Prevents credential leakage in error messages

## Future Enhancement Opportunities

### Potential Improvements
1. **Caching Layer**: Redis/memory caching for frequently accessed data
2. **Batch Operations**: Support for bulk incident operations
3. **Webhook Support**: Real-time incident updates
4. **Advanced Filtering**: Enhanced query capabilities beyond FIQL
5. **Performance Metrics**: Built-in performance monitoring
6. **Configuration Validation**: Enhanced startup configuration validation

### Integration Possibilities
1. **Additional TOPdesk Modules**: Asset management, change management
2. **Third-party Integrations**: Slack, Teams notifications
3. **Custom Workflows**: Configurable incident processing workflows
4. **Reporting Tools**: Advanced reporting and analytics capabilities

This comprehensive documentation provides a complete picture of the TOPdesk MCP Python tool's architecture, capabilities, and usage patterns, serving as both a developer reference and user guide.