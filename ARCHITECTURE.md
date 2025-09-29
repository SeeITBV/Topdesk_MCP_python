# TOPdesk MCP Python - Technical Architecture

## System Architecture Overview

The TOPdesk MCP Python tool implements a layered architecture that provides a clean separation between the MCP protocol handling, business logic, and TOPdesk API interactions.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      MCP Clients                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Claude    │  │   Custom    │  │   Other MCP-Compatible  │  │
│  │  Desktop    │  │ Applications│  │      Applications       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────────┘
                          │ Model Context Protocol (MCP)
                          │ Transport: stdio | HTTP | SSE
┌─────────────────────────▼───────────────────────────────────────┐
│                  MCP Server Layer                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    main.py                              │    │
│  │  • FastMCP server initialization                       │    │
│  │  • 32 MCP tool function definitions                   │    │
│  │  • Tool registration and metadata management          │    │
│  │  • Environment configuration                          │    │
│  │  • Transport selection (stdio/HTTP/SSE)               │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────┬───────────────────────────────────────┘
                          │ Function Calls
┌─────────────────────────▼───────────────────────────────────────┐
│                  SDK Orchestration Layer                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                _topdesk_sdk.py                          │    │
│  │  • Connection management and authentication            │    │
│  │  • Module initialization and coordination              │    │
│  │  • Base64 credential encoding                          │    │
│  │  • Logging configuration                               │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────┬───────────────┬───────────────┬───────────────────────┘
          │               │               │
          ▼               ▼               ▼
┌─────────────────┐ ┌─────────────┐ ┌─────────────────┐
│  Domain Layer   │ │Domain Layer │ │  Domain Layer   │
│                 │ │             │ │                 │
│ _incident.py    │ │ _person.py  │ │ _operator.py    │
│ (362 lines)     │ │ (60 lines)  │ │ (100 lines)     │
│                 │ │             │ │                 │
│ • Incident CRUD │ │ • Person    │ │ • Operator      │
│ • Search & Query│ │   CRUD      │ │   CRUD          │
│ • Attachments   │ │ • Archive   │ │ • Search        │
│ • Progress Trail│ │   Operations│ │ • Groups        │
│ • Time Tracking │ │ • FIQL      │ │ • FIQL          │
│ • Escalation    │ │   Queries   │ │   Queries       │
│ • Actions       │ │             │ │                 │
└─────────┬───────┘ └──────┬──────┘ └─────────┬───────┘
          │                │                  │
          └────────────────┼──────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Utility Layer                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   _utils.py                             │    │
│  │                  (810 lines)                            │    │
│  │                                                         │    │
│  │  HTTP Request Management:                               │    │
│  │  • request_topdesk() - GET requests with params        │    │
│  │  • post_to_topdesk() - POST operations                 │    │
│  │  • put_to_topdesk() - PUT operations                   │    │
│  │  • patch_to_topdesk() - PATCH operations               │    │
│  │  • delete_from_topdesk() - DELETE operations           │    │
│  │                                                         │    │
│  │  Response Processing:                                   │    │
│  │  • handle_topdesk_response() - Status code handling    │    │
│  │  • _handle_success_response() - 2xx responses          │    │
│  │  • _handle_client_error() - 4xx responses              │    │
│  │  • _handle_server_error() - 5xx responses              │    │
│  │  • _handle_partial_content() - Pagination support      │    │
│  │                                                         │    │
│  │  Document Conversion:                                   │    │
│  │  • convert_with_docling() - Docling API integration    │    │
│  │  • convert_with_openai() - OpenAI API integration      │    │
│  │  • convert_to_markdown() - Fallback conversion         │    │
│  │                                                         │    │
│  │  Validation & Utilities:                               │    │
│  │  • is_valid_uuid() - UUID validation                   │    │
│  │  • is_valid_email_addr() - Email validation            │    │
│  │  • resolve_lookup_candidates() - Data resolution       │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTPS Requests
┌─────────────────────────▼───────────────────────────────────────┐
│                     TOPdesk REST API                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              TOPdesk Instance                           │    │
│  │                                                         │    │
│  │  API Endpoints:                                         │    │
│  │  • /tas/api/incidents/*                                 │    │
│  │  • /tas/api/persons/*                                   │    │
│  │  • /tas/api/operators/*                                 │    │
│  │  • /tas/api/operatorgroups/*                            │    │
│  │  • Authentication: Basic Auth (Base64)                 │    │
│  │  • Response Format: JSON                               │    │
│  │  • Query Language: FIQL                                │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### MCP Server Layer (`main.py`)
- **Protocol Handling**: Implements MCP protocol using FastMCP framework
- **Tool Registration**: Manages 32 MCP tool functions with metadata
- **Transport Management**: Supports multiple transport protocols
- **Configuration**: Environment variable processing and validation
- **Error Boundaries**: Top-level error handling and logging

### SDK Orchestration Layer (`_topdesk_sdk.py`)
- **Connection Management**: Single point of API connection
- **Authentication**: Credential encoding and management
- **Module Coordination**: Initializes and coordinates domain modules
- **Session Management**: Maintains connection state across requests

### Domain Layers
Each domain module encapsulates specific TOPdesk functionality:

#### Incident Management (`_incident.py`)
```
┌─────────────────────────────────────────────────────────────┐
│                      _incident.py                          │
├─────────────────────────────────────────────────────────────┤
│  Main Class: incident                                       │
│  ┌─────────────────┐ ┌──────────────┐ ┌─────────────────┐  │
│  │   _action       │ │  _request    │ │  _timespent     │  │
│  │  Sub-class      │ │  Sub-class   │ │  Sub-class      │  │
│  │  • Add actions  │ │  • Get reqs  │ │  • Log time     │  │
│  │  • Get actions  │ │  • Manage    │ │  • Get entries  │  │
│  │  • Delete acts  │ │    requests  │ │  • Time queries │  │
│  └─────────────────┘ └──────────────┘ └─────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              _attachments                           │    │
│  │             Sub-class                               │    │
│  │  • Get attachment list                              │    │
│  │  • Download attachment data                         │    │
│  │  • Convert to markdown                              │    │
│  │  • Base64 encoding                                  │    │
│  │  • Integration with conversion services             │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

#### Person Management (`_person.py`)
- **CRUD Operations**: Create, read, update, delete persons
- **Search Functionality**: FIQL-based person queries
- **Archive Management**: Archive and unarchive operations

#### Operator Management (`_operator.py`)
- **Operator CRUD**: Manage operator accounts
- **Group Management**: Operator group operations
- **Query Support**: FIQL queries for operators

### Utility Layer (`_utils.py`)
The utility layer provides core infrastructure services:

```
┌─────────────────────────────────────────────────────────────┐
│                       _utils.py                            │
├─────────────────────────────────────────────────────────────┤
│  HTTP Management           │  Document Processing           │
│  ┌─────────────────────┐   │  ┌─────────────────────────┐   │
│  │ • GET requests      │   │  │ • Docling API           │   │
│  │ • POST requests     │   │  │ • OpenAI API            │   │
│  │ • PUT requests      │   │  │ • MarkItDown fallback   │   │
│  │ • PATCH requests    │   │  │ • Multi-format support  │   │
│  │ • DELETE requests   │   │  │ • Base64 encoding       │   │
│  └─────────────────────┘   │  └─────────────────────────┘   │
├─────────────────────────────┼─────────────────────────────────┤
│  Response Processing        │  Validation & Utilities        │
│  ┌─────────────────────┐   │  ┌─────────────────────────┐   │
│  │ • Status handling   │   │  │ • UUID validation       │   │
│  │ • Error processing  │   │  │ • Email validation      │   │
│  │ • Pagination        │   │  │ • Data resolution       │   │
│  │ • Content parsing   │   │  │ • Query building        │   │
│  │ • Header processing │   │  │ • Parameter handling    │   │
│  └─────────────────────┘   │  └─────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow Patterns

### Request Flow
1. **MCP Client** sends tool request via protocol
2. **MCP Server** receives and validates request
3. **Tool Function** processes parameters and calls SDK
4. **SDK Module** formats request and calls utility layer
5. **Utility Layer** makes HTTP request to TOPdesk API
6. **Response Processing** handles status codes and formats data
7. **Return Path** sends formatted response back to client

### Error Handling Flow
```
Error Occurrence → Utility Layer Handling → Domain Layer Processing → 
Tool Function Formatting → MCP Server Response → Client Notification
```

### Document Conversion Flow
```
Attachment Request → Download from TOPdesk → 
┌─ Try Docling API (if configured)
├─ Try OpenAI API (if configured)  
└─ Fallback to MarkItDown
→ Return Markdown Content
```

## Key Design Patterns

### 1. Layered Architecture
- Clear separation of concerns
- Each layer has specific responsibilities
- Dependencies flow downward only

### 2. Factory Pattern
- SDK connection creates module instances
- Centralized configuration and authentication

### 3. Strategy Pattern
- Multiple document conversion strategies
- Configurable transport options
- Fallback mechanisms for external services

### 4. Template Method Pattern
- Consistent HTTP request handling
- Standardized error processing
- Uniform response formatting

## Scalability Considerations

### Connection Management
- Single connection instance per server
- Connection reuse across requests
- Proper resource cleanup

### Memory Management
- Streaming for large attachments
- Temporary file cleanup
- Pagination for large result sets

### Performance Optimization
- Lazy loading of modules
- Efficient data structures
- Minimal object creation in hot paths

## Security Architecture

### Authentication Flow
```
Environment Variables → Base64 Encoding → HTTP Headers → TOPdesk API
```

### Data Protection
- Credentials never logged
- Temporary files securely handled
- Error messages sanitized

### Network Security
- HTTPS only connections
- Certificate validation
- Secure header handling

This architecture provides a robust, scalable, and maintainable foundation for TOPdesk-MCP integration while maintaining clear separation of concerns and following established design patterns.