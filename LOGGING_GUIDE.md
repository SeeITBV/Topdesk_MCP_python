# TOPdesk MCP Server - Logging Guide

## Overview

The TOPdesk MCP Server now includes comprehensive logging functionality accessible through both MCP tools and a web interface. This feature allows you to monitor server activity, debug issues, and track API interactions.

## 🔧 Configuration

### Environment Variables

```bash
# Enable file-based logging (optional)
LOG_FILE=/var/log/topdesk-mcp/server.log

# Set log level (optional, default: INFO)
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Enable HTTP transport to access web interface
TOPDESK_MCP_TRANSPORT=streamable-http
TOPDESK_MCP_HOST=0.0.0.0
TOPDESK_MCP_PORT=3030
```

### Log Levels

- **DEBUG**: Detailed information for diagnosing problems
- **INFO**: General information about server operation (default)
- **WARNING**: Something unexpected happened but the server continues
- **ERROR**: Serious problem that prevented an operation
- **CRITICAL**: Very serious error that may cause the server to stop

## 📊 Accessing Logs

### 1. Web Interface (HTTP Transport)

When using HTTP transport (`TOPDESK_MCP_TRANSPORT=streamable-http`), logs are accessible via:

- **HTML Interface**: `http://localhost:3030/logging`
  - Interactive web interface with filtering and refresh capabilities
  - Real-time log viewing with syntax highlighting
  - Responsive design for desktop and mobile

- **JSON API**: `http://localhost:3030/logging/json`
  - Programmatic access to log data
  - Same filtering options as HTML interface
  - Suitable for monitoring tools and scripts

#### Web Interface Features

- **Filtering**: Filter logs by level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **Line Limits**: Show 1-1000 recent log lines
- **Live Updates**: Manual refresh or auto-refresh capabilities
- **Syntax Highlighting**: Color-coded log levels for easy reading
- **Mobile Friendly**: Responsive design works on all devices

### 2. MCP Tool

The `get_log_entries` tool provides programmatic access to logs:

```javascript
// Example MCP tool call
{
  "method": "get_log_entries",
  "params": {
    "lines": 100,        // Optional: 1-1000 lines (default: 100)
    "level": "ERROR"     // Optional: filter by level
  }
}
```

#### Tool Parameters

- `lines` (integer, optional): Number of recent lines to retrieve (1-1000, default: 100)
- `level` (string, optional): Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

#### Tool Response

```json
{
  "configuration": {
    "log_file": "/var/log/topdesk-mcp/server.log",
    "log_level": "INFO",
    "total_lines_in_file": 1250,
    "lines_requested": 100,
    "lines_returned": 45,
    "level_filter": "ERROR"
  },
  "entries": [
    {
      "timestamp": "2024-01-15 14:25:01,012",
      "logger": "topdesk_mcp._person",
      "level": "ERROR", 
      "message": "Failed to retrieve person with ID 'invalid-uuid'"
    }
  ]
}
```

## 🚀 Usage Examples

### Basic Web Access

1. Start server with HTTP transport:
   ```bash
   export TOPDESK_MCP_TRANSPORT=streamable-http
   export LOG_FILE=/tmp/topdesk-mcp.log
   topdesk-mcp
   ```

2. Open browser to: `http://localhost:3030/logging`

### Filtering Examples

- **View only errors**: `http://localhost:3030/logging?level=ERROR`
- **Last 50 lines**: `http://localhost:3030/logging?lines=50`
- **Warnings, last 200 lines**: `http://localhost:3030/logging?lines=200&level=WARNING`

### MCP Tool Examples

```bash
# Get last 100 log entries (all levels)
curl -X POST http://localhost:3030/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "get_log_entries", "params": {"lines": 100}, "id": 1}'

# Get only ERROR level logs
curl -X POST http://localhost:3030/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "get_log_entries", "params": {"level": "ERROR"}, "id": 1}'
```

## 📝 Log Format

The server uses Python's standard logging format:

```
2024-01-15 14:23:45,123 - topdesk_mcp.main - INFO - Server starting up
^timestamp               ^logger           ^level ^message
```

### Common Loggers

- `topdesk_mcp.main`: Server startup, shutdown, and main operations
- `topdesk_mcp._topdesk_sdk`: TOPdesk API connections and authentication  
- `topdesk_mcp._incident`: Incident-related operations
- `topdesk_mcp._person`: Person-related operations
- `topdesk_mcp._operator`: Operator-related operations
- `topdesk_mcp._utils`: Utility functions and document conversion
- `fastmcp.server`: FastMCP framework messages

## 🔍 Troubleshooting

### No Logs Showing

1. **Check configuration**:
   ```bash
   # Verify LOG_FILE is set
   echo $LOG_FILE
   
   # Check if file exists and is writable
   ls -la $LOG_FILE
   ```

2. **Verify log level**: Ensure `LOG_LEVEL` allows the messages you want to see

3. **Generate log activity**: Execute some MCP tools to generate log entries

### Web Interface Not Accessible

1. **Check transport mode**: Ensure `TOPDESK_MCP_TRANSPORT=streamable-http`
2. **Verify port**: Check if port 3030 (or your configured port) is accessible
3. **Check server logs**: Look for startup messages about logging endpoints

### Common Error Messages

- `"No log file configured"`: Set the `LOG_FILE` environment variable
- `"Log file not found"`: File doesn't exist yet - run some operations first
- `"Permission denied"`: Ensure the server process can write to the log file

## 🔒 Security Considerations

- **Log file permissions**: Ensure log files are readable only by authorized users
- **Sensitive data**: The server avoids logging sensitive information like passwords
- **Log rotation**: Consider implementing log rotation to prevent disk space issues
- **Access control**: Restrict access to the `/logging` endpoint in production

## 📚 Integration Examples

### Monitoring Scripts

```bash
#!/bin/bash
# Simple monitoring script
ERRORS=$(curl -s "http://localhost:3030/logging/json?level=ERROR" | jq '.configuration.lines_returned')
if [ "$ERRORS" -gt 0 ]; then
    echo "⚠️  Found $ERRORS error(s) in logs"
    # Send alert...
fi
```

### Log Analysis

```python
import requests

# Get recent logs
response = requests.get('http://localhost:3030/logging/json?lines=1000')
data = response.json()

# Analyze patterns
for entry in data['entries']:
    if 'timeout' in entry['message'].lower():
        print(f"Timeout detected: {entry['timestamp']} - {entry['message']}")
```

## 🎯 Best Practices

1. **Use appropriate log levels**: Don't log sensitive information at INFO level
2. **Monitor regularly**: Set up automated monitoring for ERROR and CRITICAL logs
3. **Rotate logs**: Implement log rotation to prevent disk space issues
4. **Secure access**: Restrict access to logging endpoints in production
5. **Performance**: Use filtering to reduce data transfer when accessing logs programmatically

---

For more information, see the [TOPdesk MCP Server Documentation](README.md).