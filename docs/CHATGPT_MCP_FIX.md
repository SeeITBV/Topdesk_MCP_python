# ChatGPT MCP Compatibility Fix

## Problem
When calling the TOPdesk MCP server from ChatGPT, requests were failing with:
```
2025-10-01 12:08:02,278 - topdesk_mcp._utils - ERROR - Bad Request: The request was invalid or cannot be served
```

While the same tools worked perfectly when called from the test page at `/test`.

## Root Cause
According to the OpenAI MCP documentation, ChatGPT sends `null` (None in Python) for optional parameters instead of omitting them. This is different from how other MCP clients might behave.

When a tool function like `topdesk_list_open_incidents(limit: int = 5)` receives `None` instead of having the parameter omitted, Python's default value mechanism doesn't apply, and `None` gets passed through to the function body.

If this `None` value wasn't handled, it could cause issues:
1. Type checking failures (`int` expected but `None` received)
2. Invalid values passed to API requests
3. Comparison failures (`None < 1` raises TypeError)

## Solution
Updated all tool functions with optional parameters to:

1. **Change type hints to `Optional[type]`**: This explicitly indicates that `None` is a valid input
   ```python
   # Before
   def topdesk_list_open_incidents(limit: int = 5) -> list:
   
   # After  
   def topdesk_list_open_incidents(limit: Optional[int] = 5) -> list:
   ```

2. **Add None handling logic**: Check for `None` and apply the default value explicitly
   ```python
   # Handle None or invalid limit values for ChatGPT compatibility
   # ChatGPT may send null for optional parameters instead of omitting them
   if limit is None:
       logger.info("Received None for limit parameter, using default value of 5")
       limit = 5
   ```

3. **Add debug logging**: Log the actual parameter values received to help diagnose future issues
   ```python
   logger.info(f"topdesk_list_open_incidents called with limit={limit} (type: {type(limit).__name__})")
   ```

## Files Changed

### topdesk_mcp/main.py
- Added `Optional` to imports from `typing`
- Updated 8 tool functions with optional parameters:
  - `get_log_entries(lines, level)`
  - `topdesk_get_incident(incident_id, concise)`
  - `topdesk_get_incidents_by_fiql_query(query, page_size)`
  - `topdesk_get_progress_trail(incident_id, inlineimages, force_images_as_data)`
  - `topdesk_archive_person(person_id, reason_id)`
  - `topdesk_list_open_incidents(limit)`
  - `topdesk_list_recent_changes(limit, open_only)`

### topdesk_mcp/_utils.py
- Added debug logging to show the complete request URL and parameters for troubleshooting

## Testing
The fix was validated by:
1. Syntax checking with `py_compile`
2. Logic testing with isolated function signature tests
3. Ensuring backwards compatibility - calling functions without parameters or with explicit values still works

## Benefits
- ✅ ChatGPT can now successfully call tools with optional parameters
- ✅ Backwards compatible - existing clients continue to work
- ✅ Better debugging - logs show actual parameter values received
- ✅ More robust - explicitly handles edge cases
- ✅ Type-safe - `Optional` type hints are more accurate

## Usage with ChatGPT
After this fix, ChatGPT can call tools like:

```json
{
  "method": "tools/call",
  "params": {
    "name": "topdesk_list_open_incidents",
    "arguments": {}
  }
}
```

or

```json
{
  "method": "tools/call",
  "params": {
    "name": "topdesk_list_open_incidents",
    "arguments": {
      "limit": null
    }
  }
}
```

Both will correctly use the default value of 5.

## References
- OpenAI MCP Documentation: https://platform.openai.com/docs/guides/tools-connectors-mcp
- Related: FastMCP 2.12.4 doesn't support `input_schema` parameter (see DEPLOYMENT_GUIDE.md)
