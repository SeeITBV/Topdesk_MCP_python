# TOPdesk MCP Connector - Implementation Notes

## Overview
This document describes the fixes implemented for the TOPdesk MCP connector to properly retrieve incidents and changes from the TOPdesk REST API.

## Problem Statement
The original MCP connector was not retrieving data from TOPdesk. The issues were:
- No health check mechanism
- No dedicated MCP tools for listing open incidents
- No MCP tools for listing changes
- Missing fallback mechanism for changes endpoint (some tenants have `/changes`, others only `/operatorChanges`)

## Solution Implemented

### 1. Health Check Tool
**Function:** `topdesk_health_check()`

**Endpoint:** `GET /tas/api/version`

**Purpose:** Validates connectivity and authentication with TOPdesk API

**Returns:**
```json
{
  "ok": true,
  "status": "healthy",
  "version": { ... },
  "message": "Successfully connected to TOPdesk API"
}
```

**Error Handling:**
- Logs full URL (sanitized)
- Returns clear status messages
- Indicates specific failure reasons

### 2. List Open Incidents Tool
**Function:** `topdesk_list_open_incidents(limit=5)`

**Endpoint:** `GET /tas/api/incidents?pageSize={limit}&closed=false&sort=modificationDate:desc`

**Parameters:**
- `limit` (int, default=5): Maximum number of incidents to return (1-100)

**Query Parameters:**
- `pageSize`: Controls result count
- `closed=false`: Filters to open incidents only
- `sort=modificationDate:desc`: Most recently modified first

**Returns:** List of normalized incidents:
```json
[
  {
    "id": "uuid",
    "key": "I-2024-1234",
    "title": "Brief description",
    "status": "Processing status name",
    "requester": "Caller dynamic name",
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-02T00:00:00Z",
    "closed": false
  }
]
```

**Error Codes:**
- `-32001`: Authentication failed (401) - check credentials
- `-32002`: Access forbidden (403) - user lacks permissions
- `-32003`: Not found (404) - check URL and API path
- `-32004`: Server error (500+) - TOPdesk issue
- `-32000`: Unexpected status code
- `-32603`: General failure

### 3. List Recent Changes Tool
**Function:** `topdesk_list_recent_changes(limit=5, open_only=True)`

**Endpoints:** 
1. Primary: `GET /tas/api/changes?pageSize={limit}&sort=modificationDate:desc`
2. Fallback: `GET /tas/api/operatorChanges?pageSize={limit}&sort=modificationDate:desc`

**Parameters:**
- `limit` (int, default=5): Maximum number of changes to return (1-100)
- `open_only` (bool, default=True): Filter to open/non-closed changes

**Fallback Logic:**
1. Try `/tas/api/changes` first
2. If 404 response, automatically retry with `/tas/api/operatorChanges`
3. Log which endpoint was successfully used

**Client-Side Filtering:**
When `open_only=True`, filters out changes where:
- `closedDate` or `closureDate` is present
- `status.name` is "Closed" or "Gesloten" (Dutch)
- `state` is "Closed" or "Gesloten"

**Returns:** Dictionary with changes and metadata:
```json
{
  "changes": [
    {
      "id": "uuid",
      "key": "C-2024-5678",
      "title": "Brief description",
      "status": "Status name",
      "requester": "Requester dynamic name",
      "createdAt": "2024-01-01T00:00:00Z",
      "updatedAt": "2024-01-02T00:00:00Z"
    }
  ],
  "metadata": {
    "endpoint_used": "operatorChanges",
    "total_returned": 5,
    "filtered": true
  }
}
```

**Error Codes:** Same as incidents tool

## Environment Variables

The connector uses these environment variables (names remain unchanged per requirements):

```bash
# Required
TOPDESK_URL=https://yourcompany.topdesk.net
TOPDESK_USERNAME=your_username
TOPDESK_PASSWORD=your_application_password  # Important: use application password, not regular password

# Optional
TOPDESK_MCP_TRANSPORT=stdio                # stdio|streamable-http|sse
LOG_LEVEL=INFO                             # DEBUG for detailed logging
LOG_FILE=/path/to/logfile.log             # For persistent logs
SSL_VERIFY=true                            # Set to false only for testing
```

## URL Normalization

The connector automatically normalizes the base URL:
- Strips trailing slashes from `TOPDESK_URL`
- All API calls use full path: `{TOPDESK_URL}/tas/api/{resource}`
- No manual path construction needed

## Authentication

Uses **Basic Authentication**:
- Header: `Authorization: Basic <base64(username:password)>`
- Standard headers:
  - `Accept: application/json` (all requests)
  - `Content-Type: application/json` (POST/PUT/PATCH only)

## Logging

Enhanced logging includes:
- **Full URL** for every request (credentials removed)
- **Status code** for all responses
- **Response body preview** (first 300 characters) on errors
- **Explicit error interpretation** (401/403/404/5xx)

Example log entries:
```
INFO  - Fetching open incidents: GET https://example.topdesk.net/tas/api/incidents?pageSize=5&closed=false&sort=modificationDate:desc
INFO  - Successfully retrieved 5 incidents
ERROR - Authentication failed - check TOPDESK_USERNAME and TOPDESK_PASSWORD (application password): {"error": "Invalid credentials"}
```

## Error Messages

Clear, actionable error messages:

| Status | Error Message | Action |
|--------|---------------|--------|
| 401 | Authentication failed - check TOPDESK_USERNAME and TOPDESK_PASSWORD (application password) | Verify credentials, ensure using application password |
| 403 | Access forbidden - user lacks permissions for {module} module | Check user permissions in TOPdesk |
| 404 | Endpoint not found - check TOPdesk URL and API path | Verify URL, check if module is enabled |
| 404 (changes) | Falls back to /operatorChanges automatically | No action needed, automatic |
| 5xx | TOPdesk server error (status {code}) | Check TOPdesk service status, retry later |

## Testing

To test the implementation:

```bash
# Set credentials
export TOPDESK_URL="https://your-instance.topdesk.net"
export TOPDESK_USERNAME="your_username"
export TOPDESK_PASSWORD="your_application_password"

# Run test script
python /tmp/test_topdesk_connector.py
```

Or test individual tools via the MCP interface:
```json
// Health check
{"name": "topdesk_health_check", "arguments": {}}

// List incidents
{"name": "topdesk_list_open_incidents", "arguments": {"limit": 5}}

// List changes
{"name": "topdesk_list_recent_changes", "arguments": {"limit": 5, "open_only": true}}
```

## Compatibility

- ✅ Works with TOPdesk API versions 3.x
- ✅ Compatible with both `/changes` and `/operatorChanges` endpoints
- ✅ Handles Dutch and English status names
- ✅ No breaking changes to existing MCP tools
- ✅ All existing environment variable names preserved

## Example Log Output (404 → Fallback)

```
2024-10-01 10:00:00 - INFO - Attempting to fetch changes: GET https://example.topdesk.net/tas/api/changes?pageSize=5&sort=modificationDate:desc
2024-10-01 10:00:00 - DEBUG - Response status for /changes: 404
2024-10-01 10:00:00 - INFO - /changes endpoint returned 404, falling back to /operatorChanges
2024-10-01 10:00:00 - INFO - Attempting to fetch changes from fallback: GET https://example.topdesk.net/tas/api/operatorChanges?pageSize=5&sort=modificationDate:desc
2024-10-01 10:00:00 - DEBUG - Response status for /operatorChanges: 200
2024-10-01 10:00:00 - INFO - Successfully retrieved changes from /operatorChanges endpoint
2024-10-01 10:00:00 - INFO - Normalized 5 changes from operatorChanges endpoint
```

## Future Enhancements (Optional)

As mentioned in the specification, these could be added later:
- Capability detection at startup (probe `/changes` availability once)
- Toggleable TLS validation per request
- Rate limiting and backoff for 429/503 responses
- Timeout configuration via environment variable
- Caching of health check results

## Verification Checklist

- [x] Environment variables remain unchanged
- [x] Health check endpoint works (`/tas/api/version`)
- [x] Open incidents listing works
- [x] Changes endpoint with fallback works
- [x] Error codes are distinct (401/403/404/5xx)
- [x] Logging includes URLs and status codes
- [x] Client-side filtering for open changes
- [x] Server-side sorting (modificationDate:desc)
- [x] No breaking changes to existing tools
