# Natural Language → TOPdesk MCP Router

A FastAPI-based service that converts natural language queries into secure MCP toolcalls for TOPdesk, providing intelligent query planning, result normalization, and natural language summaries.

## Features

- **Natural Language Processing**: Convert plain English queries to structured MCP calls
- **Intelligent Query Planning**: Automatic intent detection and execution planning
- **Security First**: Rate limiting, circuit breaker, and tool allowlisting
- **Result Normalization**: Consistent data structures across different MCP responses
- **Natural Language Summaries**: Human-readable summaries of technical results
- **Comprehensive Logging**: Detailed logging without PII exposure

## Quick Start

### 1. Install Dependencies

```bash
# Install the package with router dependencies
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### 2. Configure Environment

Copy the example environment file and configure:

```bash
cp .env.nl-router .env
```

Edit `.env` with your MCP server details:

```env
MCP_BASE_URL=http://localhost:3030
MCP_API_KEY=your-api-key-if-needed
LOG_LEVEL=INFO
```

### 3. Start the Router

```bash
# Using uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Or using the FastAPI CLI (if installed)
fastapi run app/main.py --port 8000
```

### 4. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Example query
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "tickets for John Doe", "max_results": 5}'
```

## API Endpoints

### POST /ask

Main endpoint for natural language queries.

**Request:**
```json
{
  "query": "tickets for John Doe that are open",
  "max_results": 5
}
```

**Response:**
```json
{
  "plan": {
    "intent": "Find incidents for person: John Doe",
    "steps": [...],
    "tool_calls": [...],
    "warnings": []
  },
  "tool_calls": [...],
  "raw": {...},
  "results": [...],
  "summary": "John Doe has 3 incidents: 2 open, 1 assigned to IT Support.",
  "execution_time": 1.23,
  "warnings": []
}
```

### GET /health

Health check endpoint.

### GET /status  

Detailed service status including circuit breaker and rate limiting status.

## Query Examples

### Person-Specific Queries
```
"tickets for Sander Sterckx"
"John Doe's open incidents"
"incidents from jane.smith@company.com"
```

### Operator Queries
```
"incidents assigned to Jane Smith"  
"tickets handled by IT Support team"
"operator John's workload"
```

### Category/Type Filters
```
"recent changes"
"RFC requests from last month"
"change category incidents"
```

### Status and Priority
```
"open high priority tickets"
"critical incidents from yesterday"
"closed tickets this week"
```

### Specific Incident Details
```
"show complete details for incident I-240101-001"
"full overview of ticket I-231225-042"
```

### Search Queries
```
"email problems"
"password reset issues"
"network connectivity"
```

## Architecture

### Query Planning Process

1. **Intent Detection**: Analyze natural language to determine query type
2. **Parameter Extraction**: Extract names, dates, priorities, etc.
3. **Tool Selection**: Choose appropriate MCP tools for the query
4. **FIQL Generation**: Build proper FIQL queries for complex filtering
5. **Execution Planning**: Create step-by-step execution plan

### Multi-Step Queries

Some queries require multiple steps:

1. **Person Lookup** → **Incident Search**
   - "tickets for John Doe" first looks up John's person ID
   - Then searches incidents with caller.id matching that person

2. **Operator Lookup** → **Assignment Search**
   - "incidents assigned to Jane" first finds Jane's operator ID
   - Then searches incidents assigned to that operator

### Security Features

- **Rate Limiting**: 60 requests per 5 minutes per IP
- **Circuit Breaker**: Protects against MCP server failures
- **Tool Allowlisting**: Only approved tools can be called
- **No-Write Policy**: Only read operations are permitted
- **Input Validation**: All inputs are validated and sanitized
- **PII Protection**: Sensitive data is not logged

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_BASE_URL` | Required | Base URL of the MCP server |
| `MCP_API_KEY` | Optional | API key for MCP authentication |
| `LOG_LEVEL` | INFO | Logging level |
| `RATE_LIMIT_REQUESTS` | 60 | Max requests per time window |
| `RATE_LIMIT_WINDOW` | 300 | Rate limit window in seconds |
| `CIRCUIT_BREAKER_FAILURE_THRESHOLD` | 5 | Failures before circuit opens |
| `CIRCUIT_BREAKER_RECOVERY_TIMEOUT` | 60 | Seconds before retry |
| `MCP_TIMEOUT` | 8 | Request timeout in seconds |
| `MCP_RETRIES` | 2 | Number of request retries |
| `DEFAULT_MAX_RESULTS` | 5 | Default result limit |
| `MAX_ALLOWED_RESULTS` | 25 | Maximum allowed results |
| `DEFAULT_TIME_WINDOW` | 30 | Default time filter in days |

### Allowed MCP Tools

The router only allows these MCP tools for security:

- `search` - Text search across incidents
- `topdesk_get_incidents_by_fiql_query` - FIQL-based incident filtering
- `topdesk_get_person_by_query` - Person lookup
- `topdesk_get_operators_by_fiql_query` - Operator lookup  
- `topdesk_get_complete_incident_overview` - Complete incident details

## Development

### Running Tests

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### Code Quality

```bash
# Format code
black app/ tests/

# Lint code  
ruff check app/ tests/

# Type checking (if mypy installed)
mypy app/
```

### Project Structure

```
app/
├── main.py              # FastAPI application
├── router.py            # Main query router
├── planning.py          # Natural language planning
├── fiql.py             # FIQL query building
├── validators.py        # Input validation
├── normalize.py         # Result normalization
├── summarize.py         # Natural language summaries
├── security.py          # Rate limiting & circuit breaker
├── config.py           # Configuration management
├── schemas.py          # Pydantic models
└── tools/
    └── topdesk_client.py # MCP client

tests/
├── test_fiql.py         # FIQL building tests
├── test_planning.py     # Query planning tests
└── test_router_integration.py # Integration tests
```

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -e .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Considerations

1. **Environment**: Set `LOG_LEVEL=WARNING` in production
2. **Reverse Proxy**: Use nginx or similar for SSL termination
3. **Monitoring**: Monitor the `/health` and `/status` endpoints
4. **Rate Limiting**: Adjust rate limits based on usage patterns
5. **Circuit Breaker**: Monitor circuit breaker metrics
6. **Security**: Implement proper authentication if needed

## Troubleshooting

### Common Issues

1. **MCP Connection Failed**
   - Check `MCP_BASE_URL` is correct and server is running
   - Verify network connectivity
   - Check MCP server logs

2. **Rate Limiting Issues**
   - Adjust `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW`
   - Check for proper load balancing if using multiple instances

3. **Circuit Breaker Open**
   - Check MCP server health
   - Review circuit breaker configuration
   - Wait for recovery timeout or restart service

4. **Query Not Understood**
   - Queries may need clarification
   - Check supported query patterns
   - Review query planning logs

### Monitoring

Monitor these metrics:

- Response times (`X-Process-Time` header)
- Rate limit status (`X-RateLimit-*` headers)  
- Circuit breaker state (`GET /status`)
- Error rates in logs
- MCP server connectivity

## License

This project follows the same license as the main TOPdesk MCP project.