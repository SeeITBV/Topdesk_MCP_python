# Debugging ChatGPT MCP Integration Issue

## Problem Summary
The MCP test page (`/test`) works correctly when accessing the TOPdesk API, but ChatGPT integration via the standard MCP protocol fails with "Bad Request" errors.

## Changes Made for Diagnosis

### 1. Enhanced API Request Logging (`_utils.py`)
Added comprehensive logging in `request_topdesk()` function:
- Info-level logging of complete request URLs (previously debug-level)
- Response status code logging
- Error response body logging (first 500 chars) for 4xx errors
- This will show the exact API call being made and TOPdesk's response

### 2. Enhanced Tool Function Logging (`main.py`)
Added robust parameter handling in `topdesk_list_open_incidents()`:
- Type validation and conversion for `limit` parameter
- Logging of type conversion attempts
- More detailed error messages
- Handles ChatGPT potentially sending `null` for optional parameters

### 3. Enhanced MCP Tool Call Logging (Decorator)
Added comprehensive logging to `@handle_mcp_error` decorator:
- Logs EVERY MCP tool call with function name, args, and kwargs
- Logs success/failure status
- Logs full exception details
- **This will reveal which tool ChatGPT is actually calling**

## How to Use the Enhanced Logging

### Step 1: Deploy the Changes
Deploy the updated code to your server (Render.com or wherever it's hosted).

### Step 2: Test with ChatGPT
Ask ChatGPT to retrieve incidents using a natural language prompt like:
```
Haal me de laatste 5 incidenten op
```
or
```
Get me the last 5 incidents
```

### Step 3: Check the Logs
Look for these log entries in order:

1. **Tool Call Entry:**
   ```
   INFO - MCP tool called: <function_name> with args=(...) kwargs={...}
   ```
   This shows which tool ChatGPT is calling and with what parameters.

2. **Function Entry:**
   ```
   INFO - topdesk_list_open_incidents called with limit=X (type: int)
   ```
   This confirms the function was entered.

3. **API Request:**
   ```
   INFO - TOPdesk API request: GET <BASE_URL>/tas/api/incidents?...
   INFO - TOPdesk API response: <status_code>
   ```
   This shows the exact API call and response.

4. **Error Details (if any):**
   ```
   ERROR - Error response body: <error_message>
   ```
   This shows what TOPdesk said was wrong.

5. **Tool Result:**
   ```
   INFO - MCP tool <function_name> completed successfully
   ```
   or
   ```
   ERROR - MCP tool <function_name> failed with exception: ...
   ```

### Step 4: Analyze the Logs
Based on the logs, you can identify:
- Which tool is being called incorrectly
- What parameters are being passed
- What API request is being generated
- Why TOPdesk is rejecting it

## Common Issues to Look For

### Issue 1: Wrong Tool Being Called
If the logs show ChatGPT is calling a different tool than expected (e.g., `topdesk_get_incidents_by_fiql_query` instead of `topdesk_list_open_incidents`), the tool descriptions might need adjustment.

### Issue 2: Invalid Parameters
If parameters like `limit=null` or non-integer values are being passed, the enhanced type conversion should handle it. If not, we may need more robust validation.

### Issue 3: Malformed API Request
If the API request URL looks wrong (wrong parameters, wrong encoding), we'll need to fix the URL construction in `request_topdesk()`.

### Issue 4: Missing/Invalid Headers
If the request is being made but auth is failing, check the Authorization header construction.

## Expected Log Pattern (Working)

```
INFO - MCP tool called: topdesk_list_open_incidents with args=() kwargs={'limit': 5}
INFO - topdesk_list_open_incidents called with limit=5 (type: int)
INFO - Fetching open incidents: GET <BASE_URL>/tas/api/incidents?pageSize=5&closed=false&sort=modificationDate:desc
INFO - TOPdesk API request: GET <BASE_URL>/tas/api/incidents?pageSize=5&closed=false&sort=modificationDate%3Adesc
INFO - TOPdesk API response: 200
INFO - Successfully retrieved 68 incidents
INFO - MCP tool topdesk_list_open_incidents completed successfully
```

## Expected Log Pattern (Failing)

```
INFO - MCP tool called: <some_tool> with args=(...) kwargs={...}
INFO - TOPdesk API request: GET <BASE_URL>/tas/api/incidents?<bad_params>
INFO - TOPdesk API response: 400
ERROR - Error response body: <error_details>
ERROR - MCP tool <some_tool> failed with exception: ...
```

## Next Steps After Getting Logs

1. **Share the complete log sequence** showing the tool call → API request → error
2. **Note any patterns** in the failing requests
3. **Compare** with the working test page logs
4. **Identify the root cause** from the differences
5. **Apply the appropriate fix**

## Contact
If you need help analyzing the logs, please share:
- The complete log sequence from tool call to error
- The working test page log sequence for comparison
- The exact ChatGPT prompt you used

This will help identify the issue quickly and apply the right fix.
