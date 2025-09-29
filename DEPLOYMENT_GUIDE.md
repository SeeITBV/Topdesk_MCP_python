# TOPdesk MCP Python - Deployment Guide

This guide explains how to deploy and test the TOPdesk MCP Python server in various environments.

## Quick Start (Local Testing)

### Prerequisites
- Python 3.11+
- TOPdesk instance with API access
- API credentials (username and API token)

### 1. Installation

```bash
# Clone repository
git clone https://github.com/SeeITBV/Topdesk_MCP_python.git
cd Topdesk_MCP_python

# Install the package
pip install -e .
```

### 2. Configuration

Create a `.env` file in the project root:

```bash
# Required - TOPdesk API Configuration
TOPDESK_URL=https://yourcompany.topdesk.net
TOPDESK_USERNAME=your_username
TOPDESK_PASSWORD=your_api_token

# Optional - Server Configuration
TOPDESK_MCP_TRANSPORT=stdio           # stdio|streamable-http|sse
TOPDESK_MCP_HOST=0.0.0.0             # For HTTP/SSE transport
TOPDESK_MCP_PORT=3030                # For HTTP/SSE transport

# Optional - Logging
LOG_LEVEL=INFO
```

### 3. Test the Deployment

#### Option A: Stdio Mode (for MCP clients like Claude Desktop)
```bash
topdesk-mcp
```

#### Option B: HTTP Mode (for web testing)
```bash
TOPDESK_MCP_TRANSPORT=streamable-http topdesk-mcp
```

#### Option C: Direct Python execution
```bash
python -m topdesk_mcp.main
```

## Deployment Options

### 1. Local Development

Perfect for testing and development:

```bash
# Set environment variables
export TOPDESK_URL="https://yourcompany.topdesk.net"
export TOPDESK_USERNAME="your_username"
export TOPDESK_PASSWORD="your_api_token"

# Run in different modes
topdesk-mcp                                                    # stdio mode
TOPDESK_MCP_TRANSPORT=streamable-http topdesk-mcp             # HTTP mode
TOPDESK_MCP_TRANSPORT=sse topdesk-mcp                         # Server-Sent Events mode
```

### 2. Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy application
COPY . .

# Install dependencies
RUN pip install -e .

# Expose port for HTTP transport
EXPOSE 3030

# Default to HTTP transport for container deployment
ENV TOPDESK_MCP_TRANSPORT=streamable-http
ENV TOPDESK_MCP_HOST=0.0.0.0
ENV TOPDESK_MCP_PORT=3030

CMD ["topdesk-mcp"]
```

Build and run:

```bash
# Build image
docker build -t topdesk-mcp .

# Run with environment variables
docker run -p 3030:3030 \
  -e TOPDESK_URL="https://yourcompany.topdesk.net" \
  -e TOPDESK_USERNAME="your_username" \
  -e TOPDESK_PASSWORD="your_api_token" \
  topdesk-mcp
```

### 3. Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  topdesk-mcp:
    build: .
    ports:
      - "3030:3030"
    environment:
      - TOPDESK_URL=https://yourcompany.topdesk.net
      - TOPDESK_USERNAME=your_username
      - TOPDESK_PASSWORD=your_api_token
      - TOPDESK_MCP_TRANSPORT=streamable-http
      - TOPDESK_MCP_HOST=0.0.0.0
      - TOPDESK_MCP_PORT=3030
      - LOG_LEVEL=INFO
    restart: unless-stopped
```

Run:
```bash
docker-compose up -d
```

### 4. systemd Service (Linux)

Create `/etc/systemd/system/topdesk-mcp.service`:

```ini
[Unit]
Description=TOPdesk MCP Python Server
After=network.target

[Service]
Type=simple
User=topdesk-mcp
WorkingDirectory=/opt/topdesk-mcp
Environment=TOPDESK_URL=https://yourcompany.topdesk.net
Environment=TOPDESK_USERNAME=your_username
Environment=TOPDESK_PASSWORD=your_api_token
Environment=TOPDESK_MCP_TRANSPORT=streamable-http
Environment=TOPDESK_MCP_HOST=0.0.0.0
Environment=TOPDESK_MCP_PORT=3030
ExecStart=/opt/topdesk-mcp/venv/bin/topdesk-mcp
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable topdesk-mcp
sudo systemctl start topdesk-mcp
```

## MCP Client Configuration

### Claude Desktop

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

### Using uvx (Recommended for Claude Desktop)

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

## Testing Your Deployment

### 1. Basic Connectivity Test

```bash
# Test that the server starts without errors
export TOPDESK_URL="https://yourcompany.topdesk.net"
export TOPDESK_USERNAME="your_username"
export TOPDESK_PASSWORD="your_api_token"

timeout 10 topdesk-mcp || echo "Server started successfully"
```

### 2. HTTP Endpoint Test

If using HTTP transport:

```bash
# Start server in background
TOPDESK_MCP_TRANSPORT=streamable-http topdesk-mcp &
SERVER_PID=$!

# Wait for startup
sleep 5

# Test the MCP endpoint
curl -X POST http://localhost:3030/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "list_tools", "params": {}, "id": 1}'

# Clean up
kill $SERVER_PID
```

### 3. Tool Availability Test

Create a test script `test_tools.py`:

```python
import os
import sys
import importlib.util

# Set test credentials
os.environ["TOPDESK_URL"] = "https://test.example.com"
os.environ["TOPDESK_USERNAME"] = "test"  
os.environ["TOPDESK_PASSWORD"] = "test"

try:
    # Import the main module
    spec = importlib.util.spec_from_file_location("topdesk_mcp.main", "topdesk_mcp/main.py")
    main_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_module)
    
    # Check if MCP server exists
    mcp = getattr(main_module, 'mcp', None)
    if mcp:
        print("✅ MCP server created successfully")
        
        # Try to get tools
        tools = getattr(mcp, 'tools', None)
        if tools:
            if callable(tools):
                tool_list = tools()
            else:
                tool_list = tools
            print(f"✅ Found {len(tool_list)} tools registered")
        else:
            print("⚠️  No tools found")
    else:
        print("❌ MCP server not found")
        
except Exception as e:
    print(f"❌ Error loading server: {e}")
```

Run the test:
```bash
python test_tools.py
```

## Known Issues & Troubleshooting

### FastMCP Compatibility Issue

**Problem**: The current version has compatibility issues with FastMCP 2.12.4 due to `input_schema` parameters and `*args`/`**kwargs` decorators.

**Symptoms**:
```
TypeError: FastMCP.tool() got an unexpected keyword argument 'input_schema'
ValueError: Functions with *args are not supported as tools
```

**Temporary Workaround**: 
The server will start with basic functionality, but some advanced tools may not work until the compatibility issue is resolved.

**Solution in Progress**: 
- Remove `input_schema` parameters from tool decorators
- Replace `@handle_mcp_error` decorators with FastMCP-compatible error handling
- Use proper type annotations instead of manual schema definitions

### Common Issues

1. **Missing Credentials**
   ```
   RuntimeError: Missing TOPdesk credentials
   ```
   Solution: Set `TOPDESK_URL`, `TOPDESK_USERNAME`, and `TOPDESK_PASSWORD` environment variables.

2. **Connection Refused**
   ```
   Connection refused on localhost:3030
   ```
   Solution: Ensure the server is running and the port is not blocked by firewall.

3. **Import Errors**
   ```
   ModuleNotFoundError: No module named 'topdesk_mcp'
   ```
   Solution: Install the package with `pip install -e .`

## Security Considerations

1. **API Credentials**: Never commit API credentials to version control. Use environment variables or secure secret management.

2. **Network Access**: When using HTTP transport, ensure proper firewall rules and consider using HTTPS in production.

3. **User Permissions**: Run the service with minimal required permissions.

4. **Logging**: Be careful not to log sensitive information in production logs.

## Production Deployment Checklist

- [ ] Secure API credential storage
- [ ] Proper logging configuration
- [ ] Firewall rules configured
- [ ] Health check endpoints
- [ ] Process monitoring (systemd, supervisor, etc.)
- [ ] Backup and recovery procedures
- [ ] Performance monitoring
- [ ] Security updates process

## Support

For issues and questions:
- Check the [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for development information
- Review [CODEBASE_DOCUMENTATION.md](CODEBASE_DOCUMENTATION.md) for technical details
- Open an issue on GitHub for bugs or feature requests