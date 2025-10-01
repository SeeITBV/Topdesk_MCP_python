# Example Log Output - TOPdesk MCP Connector

This document shows example log output for various scenarios when using the new TOPdesk MCP tools.

## Successful Health Check

```
2024-10-01 10:00:00,123 - INFO - Health check: GET https://minttandartsen-test.topdesk.net/tas/api/version -> Status 200
2024-10-01 10:00:00,124 - DEBUG - TOPdesk version data: {'version': '3.0.5', 'releaseDate': '2024-01-15'}
```

**Result:**
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

---

## Successful Incidents Retrieval

```
2024-10-01 10:00:01,234 - INFO - Fetching open incidents: GET https://minttandartsen-test.topdesk.net/tas/api/incidents?pageSize=5&closed=false&sort=modificationDate:desc
2024-10-01 10:00:01,456 - DEBUG - Response status: 200
2024-10-01 10:00:01,457 - INFO - Successfully retrieved 5 incidents
```

**Result:**
```json
[
  {
    "id": "abc-123-def-456",
    "key": "I-2024-1234",
    "title": "Printer niet werkend op afdeling Sales",
    "status": "Tweede lijn",
    "requester": "Jan Jansen",
    "createdAt": "2024-01-15T10:30:00Z",
    "updatedAt": "2024-01-15T14:20:00Z",
    "closed": false
  }
]
```

---

## Successful Changes Retrieval (Primary Endpoint)

```
2024-10-01 10:00:02,567 - INFO - Attempting to fetch changes: GET https://minttandartsen-test.topdesk.net/tas/api/changes?pageSize=5&sort=modificationDate:desc
2024-10-01 10:00:02,789 - DEBUG - Response status for /changes: 200
2024-10-01 10:00:02,790 - INFO - Successfully retrieved changes from /changes endpoint
2024-10-01 10:00:02,791 - INFO - Normalized 5 changes from changes endpoint
```

**Result:**
```json
{
  "changes": [
    {
      "id": "xyz-789-abc-012",
      "key": "C-2024-5678",
      "title": "Server upgrade onderhoud",
      "status": "In behandeling",
      "requester": "Piet Pietersen",
      "createdAt": "2024-01-14T08:00:00Z",
      "updatedAt": "2024-01-15T09:00:00Z"
    }
  ],
  "metadata": {
    "endpoint_used": "changes",
    "total_returned": 5,
    "filtered": true
  }
}
```

---

## Changes Retrieval with Fallback (404 → operatorChanges)

```
2024-10-01 10:00:03,123 - INFO - Attempting to fetch changes: GET https://minttandartsen-test.topdesk.net/tas/api/changes?pageSize=5&sort=modificationDate:desc
2024-10-01 10:00:03,345 - DEBUG - Response status for /changes: 404
2024-10-01 10:00:03,346 - INFO - /changes endpoint returned 404, falling back to /operatorChanges
2024-10-01 10:00:03,347 - INFO - Attempting to fetch changes from fallback: GET https://minttandartsen-test.topdesk.net/tas/api/operatorChanges?pageSize=5&sort=modificationDate:desc
2024-10-01 10:00:03,567 - DEBUG - Response status for /operatorChanges: 200
2024-10-01 10:00:03,568 - INFO - Successfully retrieved changes from /operatorChanges endpoint
2024-10-01 10:00:03,569 - INFO - Normalized 3 changes from operatorChanges endpoint
```

**Result:**
```json
{
  "changes": [
    {
      "id": "def-456-ghi-789",
      "key": "C-2024-9012",
      "title": "Nieuwe werkplekken inrichten",
      "status": "Gepland",
      "requester": "Marie de Vries",
      "createdAt": "2024-01-13T14:00:00Z",
      "updatedAt": "2024-01-15T11:30:00Z"
    }
  ],
  "metadata": {
    "endpoint_used": "operatorChanges",
    "total_returned": 3,
    "filtered": true
  }
}
```

**Note:** This is the expected behavior - the fallback mechanism is working correctly!

---

## Error: Authentication Failed (401)

```
2024-10-01 10:00:04,123 - INFO - Fetching open incidents: GET https://minttandartsen-test.topdesk.net/tas/api/incidents?pageSize=5&closed=false&sort=modificationDate:desc
2024-10-01 10:00:04,345 - DEBUG - Response status: 401
2024-10-01 10:00:04,346 - ERROR - Authentication failed - check TOPDESK_USERNAME and TOPDESK_PASSWORD (application password): {"error": "Invalid credentials"}
```

**Error Message:**
```
Authentication failed - check TOPDESK_USERNAME and TOPDESK_PASSWORD (application password)
```

**Action Required:**
1. Verify `TOPDESK_USERNAME` is correct
2. Ensure `TOPDESK_PASSWORD` is an **application password** (not your regular TOPdesk password)
3. Generate a new application password in TOPdesk: Settings → Operators → Application passwords

---

## Error: Access Forbidden (403)

```
2024-10-01 10:00:05,123 - INFO - Fetching open incidents: GET https://minttandartsen-test.topdesk.net/tas/api/incidents?pageSize=5&closed=false&sort=modificationDate:desc
2024-10-01 10:00:05,345 - DEBUG - Response status: 403
2024-10-01 10:00:05,346 - ERROR - Access forbidden - user lacks permissions for incidents module: {"error": "Insufficient permissions"}
```

**Error Message:**
```
Access forbidden - user lacks permissions for incidents module
```

**Action Required:**
Ask your TOPdesk administrator to grant your user account permissions for:
- **Incidents module** (for incident tools)
- **Changes module** (for change tools)

---

## Error: Endpoint Not Found (404)

```
2024-10-01 10:00:06,123 - INFO - Fetching open incidents: GET https://minttandartsen-wrong.topdesk.net/tas/api/incidents?pageSize=5&closed=false&sort=modificationDate:desc
2024-10-01 10:00:06,345 - DEBUG - Response status: 404
2024-10-01 10:00:06,346 - ERROR - Incidents endpoint not found - check TOPdesk URL and API path: <!DOCTYPE html><html><head><title>404 Not Found</title></head><body><h1>404 Not Found</h1></body></html>
```

**Error Message:**
```
Incidents endpoint not found - check TOPdesk URL and API path
```

**Action Required:**
1. Verify `TOPDESK_URL` is correct
2. Should be: `https://yourcompany.topdesk.net` (no trailing slash)
3. Should NOT be: `https://yourcompany.topdesk.net/` or `https://yourcompany.topdesk.net/tas/api/`

---

## Error: Server Error (500)

```
2024-10-01 10:00:07,123 - INFO - Fetching open incidents: GET https://minttandartsen-test.topdesk.net/tas/api/incidents?pageSize=5&closed=false&sort=modificationDate:desc
2024-10-01 10:00:07,345 - DEBUG - Response status: 500
2024-10-01 10:00:07,346 - ERROR - TOPdesk server error (status 500): {"error": "Internal Server Error", "message": "Database connection failed"}
```

**Error Message:**
```
TOPdesk server error (status 500)
```

**Action Required:**
1. This is a TOPdesk server issue, not a connector problem
2. Check TOPdesk service status
3. Try again in a few minutes
4. Contact TOPdesk support if the issue persists

---

## Changes with Client-Side Filtering

When `open_only=True`, the connector filters out closed changes:

```
2024-10-01 10:00:08,123 - INFO - Attempting to fetch changes: GET https://minttandartsen-test.topdesk.net/tas/api/operatorChanges?pageSize=10&sort=modificationDate:desc
2024-10-01 10:00:08,345 - DEBUG - Response status for /operatorChanges: 200
2024-10-01 10:00:08,346 - INFO - Successfully retrieved changes from /operatorChanges endpoint
2024-10-01 10:00:08,347 - INFO - Normalized 5 changes from operatorChanges endpoint
```

**Note:** API returned 10 changes, but after client-side filtering (removing closed changes), only 5 open changes remain.

---

## Complete Debug Session Example

With `LOG_LEVEL=DEBUG`:

```
2024-10-01 10:00:00,000 - topdesk_mcp._utils - DEBUG - TOPdesk API utils object initialised.
2024-10-01 10:00:00,001 - topdesk_mcp._topdesk_sdk - DEBUG - TOPdesk API connect object initialised.
2024-10-01 10:00:00,002 - topdesk_mcp._topdesk_sdk - DEBUG - TOPdesk URL: https://minttandartsen-test.topdesk.net

2024-10-01 10:00:01,123 - __main__ - INFO - Health check: GET https://minttandartsen-test.topdesk.net/tas/api/version -> Status 200
2024-10-01 10:00:01,124 - __main__ - DEBUG - TOPdesk version data: {'version': '3.0.5', 'releaseDate': '2024-01-15'}

2024-10-01 10:00:02,234 - __main__ - INFO - Fetching open incidents: GET https://minttandartsen-test.topdesk.net/tas/api/incidents?pageSize=5&closed=false&sort=modificationDate:desc
2024-10-01 10:00:02,456 - topdesk_mcp._utils - DEBUG - Response from TopDesk API: HTTP Status Code 200: [{"id":"abc-123",...}]
2024-10-01 10:00:02,457 - __main__ - DEBUG - Response status: 200
2024-10-01 10:00:02,458 - __main__ - INFO - Successfully retrieved 5 incidents

2024-10-01 10:00:03,567 - __main__ - INFO - Attempting to fetch changes: GET https://minttandartsen-test.topdesk.net/tas/api/changes?pageSize=5&sort=modificationDate:desc
2024-10-01 10:00:03,678 - __main__ - DEBUG - Response status for /changes: 404
2024-10-01 10:00:03,679 - __main__ - INFO - /changes endpoint returned 404, falling back to /operatorChanges
2024-10-01 10:00:03,680 - __main__ - INFO - Attempting to fetch changes from fallback: GET https://minttandartsen-test.topdesk.net/tas/api/operatorChanges?pageSize=5&sort=modificationDate:desc
2024-10-01 10:00:03,901 - topdesk_mcp._utils - DEBUG - Response from TopDesk API: HTTP Status Code 200: [{"id":"xyz-789",...}]
2024-10-01 10:00:03,902 - __main__ - DEBUG - Response status for /operatorChanges: 200
2024-10-01 10:00:03,903 - __main__ - INFO - Successfully retrieved changes from /operatorChanges endpoint
2024-10-01 10:00:03,904 - __main__ - INFO - Normalized 5 changes from operatorChanges endpoint
```

---

## Using the Logs for Troubleshooting

### 1. Check Authentication
Look for:
```
INFO - Health check: GET https://... -> Status 200
```
If you see 401, your credentials are wrong.

### 2. Check Endpoint Availability
Look for:
```
INFO - /changes endpoint returned 404, falling back to /operatorChanges
```
This is normal and expected for many TOPdesk instances.

### 3. Check Data Retrieval
Look for:
```
INFO - Successfully retrieved X incidents
```
If you see 0 incidents, check your filters or data in TOPdesk.

### 4. Check for Server Errors
Look for:
```
ERROR - TOPdesk server error (status 500)
```
These are TOPdesk issues, not connector issues.

---

## Log Levels

**DEBUG**: Shows all details including request/response bodies
```bash
export LOG_LEVEL=DEBUG
```

**INFO**: Shows request URLs and success/failure messages (recommended)
```bash
export LOG_LEVEL=INFO
```

**ERROR**: Only shows errors (minimal)
```bash
export LOG_LEVEL=ERROR
```

---

## Saving Logs to File

```bash
export LOG_FILE=/tmp/topdesk-mcp.log
topdesk-mcp
```

Then view:
```bash
tail -f /tmp/topdesk-mcp.log
```

Or in the web interface (HTTP mode):
```
http://localhost:3030/logging
```
