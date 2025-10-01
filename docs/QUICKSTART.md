# Quick Start Guide: TOPdesk MCP Connector

## What Was Fixed

The TOPdesk MCP connector now properly retrieves incidents and changes from your TOPdesk instance.

## New MCP Tools Available

### 1. Health Check
```json
{
  "name": "topdesk_health_check",
  "arguments": {}
}
```

**What it does:** Checks if the connector can reach your TOPdesk API and validates authentication.

**Returns:** Status, version info, and clear error messages if something is wrong.

### 2. List Open Incidents
```json
{
  "name": "topdesk_list_open_incidents",
  "arguments": {
    "limit": 5
  }
}
```

**What it does:** Retrieves the most recently modified open incidents.

**Parameters:**
- `limit` (optional): Number of incidents to return (1-100, default: 5)

**Returns:** List of incidents with:
- `id`: UUID
- `key`: Incident number (e.g., "I-2024-1234")
- `title`: Brief description
- `status`: Processing status
- `requester`: Who created the incident
- `createdAt`, `updatedAt`: Timestamps

### 3. List Recent Changes
```json
{
  "name": "topdesk_list_recent_changes",
  "arguments": {
    "limit": 5,
    "open_only": true
  }
}
```

**What it does:** Retrieves recent changes, automatically choosing the right endpoint for your TOPdesk instance.

**Parameters:**
- `limit` (optional): Number of changes to return (1-100, default: 5)
- `open_only` (optional): Only show non-closed changes (default: true)

**Smart Fallback:** Tries `/changes` first. If that's not available (404), automatically uses `/operatorChanges`.

**Returns:** Changes list plus metadata showing which endpoint was used.

## Testing the Connector

### Option 1: Using the Test Web Interface

If you're running in HTTP mode:

1. Start the server:
```bash
TOPDESK_MCP_TRANSPORT=streamable-http topdesk-mcp
```

2. Open in browser: `http://localhost:3030/test`

3. Click the test buttons:
   - "Test Connection" → Uses health check
   - "List Recent Incidents" → Shows open incidents
   - "List Recent Changes" → Shows changes with fallback

### Option 2: Using the Test Script

```bash
# Set your credentials
export TOPDESK_URL="https://yourcompany.topdesk.net"
export TOPDESK_USERNAME="your_username"
export TOPDESK_PASSWORD="your_application_password"

# Run the test script
python /tmp/test_topdesk_connector.py
```

### Option 3: Direct MCP Tool Calls

If you're using Claude Desktop or another MCP client:

1. Make sure your `mcp_config.json` has the credentials:
```json
{
  "servers": {
    "topdesk-mcp": {
      "type": "stdio",
      "command": "uvx",
      "args": ["topdesk-mcp"],
      "env": {
        "TOPDESK_URL": "https://yourcompany.topdesk.net",
        "TOPDESK_USERNAME": "your_username",
        "TOPDESK_PASSWORD": "your_application_password"
      }
    }
  }
}
```

2. Use the tools:
   - "Check TOPdesk health"
   - "List 5 open incidents"
   - "List 5 recent changes"

## Common Issues and Solutions

### ❌ "Authentication failed"
**Cause:** Wrong credentials or not using application password.

**Solution:**
1. Verify `TOPDESK_USERNAME` is correct
2. Make sure `TOPDESK_PASSWORD` is an **application password**, not your regular password
3. In TOPdesk: Settings → Operators → Generate application password

### ❌ "Access forbidden"
**Cause:** User doesn't have permissions for incidents or changes module.

**Solution:** Ask your TOPdesk administrator to grant your user access to:
- Incidents (for incident tools)
- Changes (for change tools)

### ❌ "Endpoint not found"
**Cause:** Wrong TOPDESK_URL or module not enabled.

**Solution:**
1. Verify `TOPDESK_URL` ends with `.topdesk.net` (no trailing slash)
2. Example: `https://yourcompany.topdesk.net` ✅
3. Not: `https://yourcompany.topdesk.net/` ❌
4. Not: `https://yourcompany.topdesk.net/tas/api/` ❌

### ℹ️ Changes fallback to operatorChanges
**This is normal!** Some TOPdesk instances only have `/operatorChanges`.
The connector automatically detects this and uses the right endpoint.

**Log example:**
```
INFO - /changes endpoint returned 404, falling back to /operatorChanges
INFO - Successfully retrieved changes from /operatorChanges endpoint
```

## Environment Variables

All environment variable names remain **exactly the same** as before:

```bash
# Required
TOPDESK_URL=https://yourcompany.topdesk.net
TOPDESK_USERNAME=your_username
TOPDESK_PASSWORD=your_application_password

# Optional (for debugging)
LOG_LEVEL=DEBUG                    # Shows detailed request/response info
LOG_FILE=/tmp/topdesk-mcp.log     # Save logs to file
```

## What Changed Under the Hood

### URLs and Endpoints
- ✅ All endpoints use `/tas/api/` base path (automatically handled)
- ✅ Incidents: `/tas/api/incidents?pageSize=5&closed=false&sort=modificationDate:desc`
- ✅ Changes: `/tas/api/changes` (with fallback to `/tas/api/operatorChanges`)
- ✅ Health: `/tas/api/version`

### Authentication
- ✅ Basic Auth with `username:application_password`
- ✅ Headers: `Accept: application/json`, `Content-Type: application/json`

### Error Handling
Each error type now has a specific code and clear message:
- **-32001**: Auth failed (401) → Check credentials
- **-32002**: Forbidden (403) → Check permissions
- **-32003**: Not found (404) → Check URL/module
- **-32004**: Server error (5xx) → TOPdesk issue

### Logging
All requests now log:
- Full URL (credentials removed)
- Status code
- First 300 characters of error responses
- Which endpoint was used (for changes fallback)

## Example Output

### Health Check
```json
{
  "ok": true,
  "status": "healthy",
  "version": {
    "version": "3.0.5",
    "releaseDate": "2024-01-15"
  },
  "message": "Successfully connected to TOPdesk API"
}
```

### List Incidents
```json
[
  {
    "id": "abc-123-def",
    "key": "I-2024-1234",
    "title": "Printer not working",
    "status": "Second line",
    "requester": "John Doe",
    "createdAt": "2024-01-15T10:30:00Z",
    "updatedAt": "2024-01-15T14:20:00Z",
    "closed": false
  }
]
```

### List Changes
```json
{
  "changes": [
    {
      "id": "xyz-789-abc",
      "key": "C-2024-5678",
      "title": "Server upgrade maintenance",
      "status": "In progress",
      "requester": "Jane Smith",
      "createdAt": "2024-01-14T08:00:00Z",
      "updatedAt": "2024-01-15T09:00:00Z"
    }
  ],
  "metadata": {
    "endpoint_used": "operatorChanges",
    "total_returned": 1,
    "filtered": true
  }
}
```

## Need Help?

1. **Enable debug logging** to see what's happening:
   ```bash
   export LOG_LEVEL=DEBUG
   export LOG_FILE=/tmp/topdesk-mcp.log
   ```

2. **Check the logs** after running a command:
   ```bash
   tail -50 /tmp/topdesk-mcp.log
   ```

3. **Look for these log patterns**:
   ```
   INFO - Fetching open incidents: GET https://...
   INFO - Successfully retrieved 5 incidents
   ```

4. **Common log messages and what they mean**:
   - `"Status 401"` → Wrong credentials
   - `"Status 403"` → No permissions
   - `"Status 404"` → Wrong URL or endpoint not available
   - `"fallback to /operatorChanges"` → Normal, automatic fallback working
   - `"Successfully retrieved"` → Everything working! 🎉

## Documentation

For complete technical details, see:
- `docs/TOPDESK_CONNECTOR_FIXES.md` - Full implementation documentation
- `README.md` - General usage and setup
- `docs/DEVELOPER_GUIDE.md` - Developer information
