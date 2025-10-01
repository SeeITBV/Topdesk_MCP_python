# Environment-Based Configuration Changes

## Overview
This document describes the improvements made to the TOPdesk MCP Python connector to use environment variables for configuration and improve robustness.

## Changes Implemented

### 1. Environment Variable Support

The connector now reads SSL verification settings from the `SSL_VERIFY` environment variable:

```python
# In _topdesk_sdk.py connect class
ssl_env = os.getenv("SSL_VERIFY", "true").lower()
self._ssl_verify = ssl_env not in ("false", "0", "no", "off")
```

**Supported values:**
- `true`, `TRUE`, `yes`, `1` (or any other value) → SSL verification **enabled** (default)
- `false`, `FALSE`, `0`, `no`, `off` → SSL verification **disabled**

### 2. Security Improvements

**Credential Logging Removed:**
- Removed all debug logging of usernames, passwords, and base64-encoded credentials
- Only the TOPdesk URL is now logged at the debug level
- SSL verification warnings are logged when disabled

**Before:**
```python
self._logger.debug("TOPdesk username: " + topdesk_username)
self._logger.debug("TOPdesk password: " + topdesk_password)
self._logger.debug("TOPdesk credpair: " + self._credpair)
```

**After:**
```python
self._logger.debug("TOPdesk URL: " + self._topdesk_url)
# No credential logging
if not self._ssl_verify:
    self._logger.warning("SSL verification is disabled")
```

### 3. Centralized Header Building

Added a `build_headers()` function in `_utils.py` for consistent header construction:

```python
def build_headers(basic_token, *, json_response=True, json_body=False):
    """
    Build HTTP headers for TOPdesk API requests.
    
    Args:
        basic_token: Base64-encoded Basic Auth token
        json_response: If True, add Accept: application/json header
        json_body: If True, add Content-Type: application/json header
    
    Returns:
        Dictionary of headers
    """
    headers = {"Authorization": f"Basic {basic_token}"}
    if json_response:
        headers["Accept"] = "application/json"
    if json_body:
        headers["Content-Type"] = "application/json"
    return headers
```

**Benefits:**
- Single source of truth for header construction
- No duplicate `Accept` headers
- Consistent authentication across all endpoints
- `Content-Type` only set when needed (POST/PUT/PATCH with body)

### 4. Network Robustness

**Default Timeout:**
- All HTTP requests now have a 30-second timeout
- Defined as `DEFAULT_TIMEOUT = 30` constant

**Error Handling:**
- All network calls wrapped in try/except for `requests.exceptions.RequestException`
- Network errors return a mock response object with status 503
- Errors logged without exposing sensitive information

```python
try:
    return requests.get(url, headers=headers, verify=self._ssl_verify, timeout=DEFAULT_TIMEOUT)
except requests.exceptions.RequestException as e:
    self._logger.error(f"Network error calling Topdesk API: {e.__class__.__name__}")
    # Return mock error response
```

### 5. Bug Fixes

**Budgetholder Create Endpoint:**
- **Before:** Used `/tas/api/branches` (incorrect)
- **After:** Uses `/tas/api/budgetholders` (correct)

**Incident Request Subresource:**
- **Before:** Used `/tas/api/incidents/{id}/actions/{request_id}` (incorrect)
- **After:** Uses `/tas/api/incidents/{id}/requests/{request_id}` (correct)

## Backward Compatibility

All changes maintain full backward compatibility:

✅ **Public API unchanged:** All class constructors, method signatures, and return types remain the same
✅ **Environment variables are optional:** Default behavior is unchanged (SSL verification enabled)
✅ **All existing tests pass:** No breaking changes to existing functionality

## Usage Examples

### Basic Usage (No Changes Required)
```python
from topdesk_mcp._topdesk_sdk import connect

# This still works exactly as before
client = connect(
    topdesk_url='https://your-instance.topdesk.net',
    topdesk_username='your_username',
    topdesk_password='your_password'
)
```

### With Environment Variables
```bash
# Set environment variables
export SSL_VERIFY=false  # For testing environments only
export TOPDESK_URL=https://your-instance.topdesk.net
export TOPDESK_USERNAME=your_username
export TOPDESK_PASSWORD=your_password
```

```python
import os
from topdesk_mcp._topdesk_sdk import connect

# Read from environment
client = connect(
    topdesk_url=os.getenv('TOPDESK_URL'),
    topdesk_username=os.getenv('TOPDESK_USERNAME'),
    topdesk_password=os.getenv('TOPDESK_PASSWORD')
)
```

### On Render or Other Platforms
Set these environment variables in your platform's configuration:
- `TOPDESK_URL`
- `TOPDESK_USERNAME`
- `TOPDESK_PASSWORD`
- `SSL_VERIFY` (optional, defaults to `true`)

## Testing

All changes have been tested with:
1. **Unit tests:** Backward compatibility verification
2. **Integration tests:** HTTP call behavior verification
3. **Manual tests:** Endpoint and header validation

Test results: ✅ All tests passed

## Migration Guide

No migration needed! All existing code continues to work without changes.

If you want to use environment variables:
1. Set the environment variables in your deployment platform
2. Update your code to read from `os.getenv()` instead of hardcoding values
3. Optionally set `SSL_VERIFY=false` for development/testing (not recommended for production)

## Security Notes

⚠️ **Important:**
- Never commit credentials to source control
- Use environment variables or secrets management for credentials
- Only disable SSL verification (`SSL_VERIFY=false`) in controlled test environments
- The connector logs a warning when SSL verification is disabled
