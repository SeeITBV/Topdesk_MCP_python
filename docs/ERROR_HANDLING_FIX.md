# Error Handling Fix for TOPdesk API String Errors

## Problem

When the TOPdesk API returns an error response (e.g., 400 Bad Request, 404 Not Found, 500 Internal Server Error), the `handle_topdesk_response()` method in `_utils.py` returns an **error string** instead of raising an exception or returning an empty collection.

This causes downstream functions that expect structured data (lists or dictionaries) to fail with confusing error messages like:

```
AttributeError: 'str' object has no attribute 'get'
```

### Example Error from Logs

```
2025-10-01 15:04:32,428 - topdesk_mcp._utils - INFO - TOPdesk API response: 400
2025-10-01 15:04:32,428 - topdesk_mcp._utils - ERROR - Error response body: [{"message":"Error parsing one of the query parameters. query contains unknown field: 'archived'"}]
2025-10-01 15:04:32,428 - topdesk_mcp._utils - ERROR - Bad Request: The request was invalid or cannot be served.
2025-10-01 15:04:32,430 - __main__ - ERROR - MCP tool search failed with exception: 'str' object has no attribute 'get'
Traceback (most recent call last):
  File "/app/topdesk_mcp/main.py", line 69, in wrapper
    result = func(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^
  File "/app/topdesk_mcp/main.py", line 447, in search
    incident_id = incident.get("id")
                  ^^^^^^^^^^^^
AttributeError: 'str' object has no attribute 'get'
```

## Root Cause

The flow is:
1. User calls a function like `search()` with a query
2. Function calls `topdesk_client.incident.get_list(query=fiql_query)`
3. `get_list()` internally calls `utils.request_topdesk()` and `utils.handle_topdesk_response()`
4. When API returns a 400/500 error, `handle_topdesk_response()` calls `_handle_client_error()` or `_handle_server_error()`
5. These error handlers return a **string** with the error message (e.g., "Bad Request: The request was invalid")
6. This error string is returned to the calling function
7. The calling function tries to iterate/access the result as if it were a list/dict, causing the AttributeError

## Solution

Add explicit error checking after calling TOPdesk API methods to detect when an error string is returned instead of the expected data structure. When an error string is detected, raise an appropriate `MCPError` exception.

### Code Pattern

```python
# Before (vulnerable to error)
incidents = topdesk_client.incident.get_list(query=fiql_query)
for incident in incidents[:max_results]:
    incident_id = incident.get("id")  # Fails if incidents is a string!

# After (with error handling)
incidents = topdesk_client.incident.get_list(query=fiql_query)

# Check if API returned an error (string) instead of a list
if isinstance(incidents, str):
    raise MCPError(f"TOPdesk API error: {incidents}", error_code=-32603)

for incident in incidents[:max_results]:
    incident_id = incident.get("id")  # Safe - incidents is guaranteed to be a list
```

## Functions Fixed

The following functions were updated with error string checking:

1. **`search()`** - Checks if `incidents` is a string after calling `get_list()`
2. **`topdesk_get_incident()`** - Checks if `result` is a string after calling `get_concise()` or `get()`
3. **`topdesk_get_incidents_by_fiql_query()`** - Checks if `result` is a string after calling `get_list()`
4. **`fetch()`** - Checks if `incident` is a string after calling `get_concise()` or `get()`
5. **`topdesk_get_progress_trail()`** - Checks if `result` is a string after calling `get_progress_trail()`
6. **`topdesk_get_incident_attachments_as_markdown()`** - Checks if `result` is a string after calling `download_attachments_as_markdown()`
7. **`topdesk_get_complete_incident_overview()`** - Checks each API call result for error strings

## Error Code

All error checks raise `MCPError` with error code **-32603** (Internal error), which is appropriate for unexpected API errors.

## Testing

Added unit tests to verify the error handling:

- `test_search_handles_api_error_string()` - Verifies `search()` raises MCPError when API returns error string
- `test_fetch_handles_api_error_string()` - Verifies `fetch()` raises MCPError when API returns error string
- `test_topdesk_get_incidents_by_fiql_query_handles_api_error_string()` - Verifies FIQL query function raises MCPError

## Impact

### Before Fix
- Confusing `AttributeError: 'str' object has no attribute 'get'` errors
- Stack traces pointing to iteration code instead of the actual API error
- Difficult to diagnose what went wrong with the API call

### After Fix
- Clear error messages: "TOPdesk API error: Bad Request: The request was invalid"
- Proper error propagation through the MCP error handling decorator
- Easy to understand what API error occurred

## Future Improvements

Consider one of these approaches for a more comprehensive fix:

1. **Option A**: Modify `_handle_client_error()` and `_handle_server_error()` in `_utils.py` to raise exceptions instead of returning error strings
2. **Option B**: Modify `handle_topdesk_response()` to always return structured data (e.g., `{"error": "message"}` dict) instead of strings
3. **Option C**: Create a custom exception class that `handle_topdesk_response()` can raise, which would be caught and handled by calling code

Any of these would eliminate the need for error string checking in every calling function. However, the current fix is minimal, targeted, and doesn't change the behavior of the core SDK functions.
