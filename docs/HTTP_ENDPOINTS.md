# TOPdesk MCP Server - HTTP Endpoints

When running the TOPdesk MCP server in HTTP mode (with `TOPDESK_MCP_TRANSPORT=streamable-http` or `sse`), additional HTTP endpoints are available for testing and monitoring.

## Available Endpoints

### 1. Test Page - `/test`
**URL:** `http://your-host:port/test`  
**Method:** GET  
**Description:** Interactive HTML test page for exploring the MCP server

**Features:**
- Test TOPdesk connection using configured credentials
- List all available MCP tools
- Visual status indicators
- Quick links to API endpoints

**Screenshot:**
![Test Page](https://github.com/user-attachments/assets/467de360-1a60-4444-ae12-54d11458b471)

**Example:**
```bash
curl http://localhost:3030/test
```

---

### 2. Test Connection API - `/test/connection`
**URL:** `http://your-host:port/test/connection`  
**Method:** GET  
**Description:** JSON API endpoint to test TOPdesk connection

**Response Example:**
```json
{
  "status": "success",
  "message": "Successfully connected to TOPdesk",
  "topdesk_url": "https://yourcompany.topdesk.net",
  "username": "your_username",
  "test_result": "Retrieved 249 countries"
}
```

**For Postman Testing:**
1. Set request type to GET
2. Enter URL: `http://your-host:port/test/connection`
3. Send request
4. View JSON response with connection status

**Screenshot:**
![Connection API Response](https://github.com/user-attachments/assets/06b5180d-1411-4720-b6d7-5006097b2dfb)

---

### 3. Tools List API - `/tools`
**URL:** `http://your-host:port/tools`  
**Method:** GET  
**Description:** JSON API endpoint listing all available MCP tools

**Response Example:**
```json
{
  "status": "success",
  "count": 45,
  "tools": [
    {
      "name": "topdesk_get_incidents_by_fiql_query",
      "description": "Retrieve TOPdesk incidents using a FIQL query..."
    },
    {
      "name": "topdesk_get_incident_by_id",
      "description": "Retrieve a specific TOPdesk incident by its ID..."
    }
    // ... more tools
  ]
}
```

**For Postman Testing:**
1. Set request type to GET
2. Enter URL: `http://your-host:port/tools`
3. Send request
4. View JSON array of all available tools with their descriptions

---

### 4. Logging Endpoints

#### HTML View - `/logging`
**URL:** `http://your-host:port/logging?lines=100&level=ERROR`  
**Method:** GET  
**Description:** HTML interface for viewing server logs

**Query Parameters:**
- `lines` (optional): Number of log lines to retrieve (default: 100, max: 1000)
- `level` (optional): Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

#### JSON View - `/logging/json`
**URL:** `http://your-host:port/logging/json?lines=100&level=ERROR`  
**Method:** GET  
**Description:** JSON API for accessing server logs

---

## Starting the Server with HTTP Endpoints

### Environment Variables
```bash
export TOPDESK_URL="https://yourcompany.topdesk.net"
export TOPDESK_USERNAME="your_username"
export TOPDESK_PASSWORD="your_api_token"
export TOPDESK_MCP_TRANSPORT="streamable-http"
export TOPDESK_MCP_HOST="0.0.0.0"
export TOPDESK_MCP_PORT="3030"
```

### Start the Server
```bash
topdesk-mcp
```

### Expected Output
```
✅ HTTP endpoints available:
   📊 Logging (HTML): http://0.0.0.0:3030/logging
   📋 Logging (JSON): http://0.0.0.0:3030/logging/json
   🔧 Tools List: http://0.0.0.0:3030/tools
   🧪 Test Page: http://0.0.0.0:3030/test
   🔌 Test Connection API: http://0.0.0.0:3030/test/connection
```

---

## Postman Collection

You can import this collection to quickly test all endpoints:

### Quick Test
1. Open Postman
2. Create new request
3. GET `http://localhost:3030/test/connection`
4. Click "Send"
5. Verify the response shows `"status": "success"`

### Full Collection
Create a collection with these requests:
- **Test Connection:** GET `/test/connection`
- **List Tools:** GET `/tools`
- **View Test Page:** GET `/test` (open in browser)
- **View Logs (JSON):** GET `/logging/json?lines=50`
- **View Logs (HTML):** GET `/logging` (open in browser)

---

## Use Cases

### 1. Deployment Verification
After deploying to Render or another platform, use the `/test/connection` endpoint to verify:
- The server is running
- TOPdesk credentials are configured correctly
- Network connectivity to TOPdesk is working

### 2. Tool Discovery
Use the `/tools` endpoint to:
- List all available MCP tools
- Share tool documentation with your team
- Generate API documentation

### 3. Troubleshooting
Use the test page `/test` to:
- Quickly test TOPdesk connection
- Browse available tools
- Verify the server is responding correctly

### 4. Monitoring
Use the `/logging` endpoints to:
- Monitor server health
- Debug issues
- Track API usage

---

## Security Notes

⚠️ **Important:** These endpoints expose information about your server configuration.

**Recommendations:**
- Use these endpoints in development/testing environments
- Consider adding authentication for production use
- Use HTTPS in production
- Restrict access via firewall rules if needed
- Do not expose sensitive credentials in responses

---

## Related Documentation

- [Deployment Guide](DEPLOYMENT_GUIDE.md) - How to deploy the MCP server
- [Logging Guide](LOGGING_GUIDE.md) - Detailed logging configuration
- [Developer Guide](DEVELOPER_GUIDE.md) - Development setup and testing
