"""Tests for MCP HTTP endpoints."""
import importlib
import sys
from unittest.mock import Mock, patch, AsyncMock
import json
import pytest


@pytest.fixture
def main_module(monkeypatch):
    """Load main module with mocked dependencies."""
    monkeypatch.setenv("TOPDESK_URL", "https://example.topdesk.net")
    monkeypatch.setenv("TOPDESK_USERNAME", "user")
    monkeypatch.setenv("TOPDESK_PASSWORD", "token")

    module_name = "topdesk_mcp.main"
    if module_name in sys.modules:
        del sys.modules[module_name]

    mock_client = Mock()
    with patch("topdesk_mcp._topdesk_sdk.connect", return_value=mock_client):
        module = importlib.import_module(module_name)

    yield module, mock_client

    if module_name in sys.modules:
        del sys.modules[module_name]


@pytest.mark.asyncio
async def test_mcp_list_tools_returns_search_and_fetch(main_module):
    """Test that /mcp/list_tools returns search and fetch tools with proper schema."""
    module, mock_client = main_module
    
    # Create a mock request
    mock_request = Mock()
    
    # Call the endpoint
    response = await module.mcp_list_tools(mock_request)
    
    # Parse response
    assert response.status_code == 200
    content = json.loads(response.body.decode())
    
    # Verify structure
    assert "tools" in content
    assert len(content["tools"]) == 2
    
    # Find search tool
    search_tool = next((t for t in content["tools"] if t["name"] == "search"), None)
    assert search_tool is not None
    assert "inputSchema" in search_tool
    assert "entity" in search_tool["inputSchema"]["properties"]
    assert search_tool["inputSchema"]["properties"]["entity"]["enum"] == ["incidents", "changes", "requests"]
    assert "limit" in search_tool["inputSchema"]["properties"]
    
    # Find fetch tool
    fetch_tool = next((t for t in content["tools"] if t["name"] == "fetch"), None)
    assert fetch_tool is not None
    assert "inputSchema" in fetch_tool
    assert "entity" in fetch_tool["inputSchema"]["properties"]
    assert "id" in fetch_tool["inputSchema"]["properties"]


@pytest.mark.asyncio
async def test_mcp_call_tool_search_incidents(main_module):
    """Test calling search tool for incidents."""
    module, mock_client = main_module
    
    # Mock the topdesk_list_open_incidents function
    module.topdesk_list_open_incidents.fn = Mock(return_value=[
        {
            "id": "123",
            "key": "I-0001",
            "title": "Test incident",
            "status": "Open",
            "requester": "John Doe",
            "createdAt": "2024-01-01T10:00:00Z",
            "updatedAt": "2024-01-01T11:00:00Z"
        }
    ])
    
    # Create mock request with search payload
    mock_request = Mock()
    mock_request.json = AsyncMock(return_value={
        "name": "search",
        "arguments": {
            "entity": "incidents",
            "limit": 1
        }
    })
    
    # Call the endpoint
    response = await module.mcp_call_tool(mock_request)
    
    # Verify response
    assert response.status_code == 200
    content = json.loads(response.body.decode())
    
    assert "content" in content
    assert "isError" in content
    assert content["isError"] is False
    assert len(content["content"]) == 1
    assert content["content"][0]["type"] == "text"
    assert "structured" in content["content"][0]
    assert "results" in content["content"][0]["structured"]
    assert len(content["content"][0]["structured"]["results"]) == 1


@pytest.mark.asyncio
async def test_mcp_call_tool_nl_fallback_laatste_incidents(main_module):
    """Test natural language fallback: 'laatste 5 incidenten'."""
    module, mock_client = main_module
    
    # Mock the topdesk_list_open_incidents function
    module.topdesk_list_open_incidents.fn = Mock(return_value=[
        {
            "id": "123",
            "key": "I-0001",
            "title": "Test incident",
            "status": "Open",
            "requester": "John Doe",
            "createdAt": "2024-01-01T10:00:00Z",
            "updatedAt": "2024-01-01T11:00:00Z"
        }
    ])
    
    # Create mock request with NL prompt (as dict without name/arguments)
    mock_request = Mock()
    mock_request.json = AsyncMock(return_value={
        "prompt": "laatste 5 incidenten"
    })
    
    # Call the endpoint
    response = await module.mcp_call_tool(mock_request)
    
    # Verify response
    assert response.status_code == 200
    content = json.loads(response.body.decode())
    
    assert "content" in content
    assert content["isError"] is False
    assert "results" in content["content"][0]["structured"]


@pytest.mark.asyncio
async def test_mcp_call_tool_nl_fallback_haal_changes(main_module):
    """Test natural language fallback: 'haal de laatste 3 changes'."""
    module, mock_client = main_module
    
    # Mock the topdesk_list_recent_changes function
    module.topdesk_list_recent_changes.fn = Mock(return_value={
        "changes": [
            {
                "id": "456",
                "key": "C-0001",
                "title": "Test change",
                "status": "Open",
                "requester": "Jane Doe",
                "createdAt": "2024-01-01T10:00:00Z",
                "updatedAt": "2024-01-01T11:00:00Z"
            }
        ],
        "metadata": {"endpoint_used": "changes"}
    })
    
    # Create mock request with NL prompt
    mock_request = Mock()
    mock_request.json = AsyncMock(return_value={
        "prompt": "haal de laatste 3 changes"
    })
    
    # Call the endpoint
    response = await module.mcp_call_tool(mock_request)
    
    # Verify response
    assert response.status_code == 200
    content = json.loads(response.body.decode())
    
    assert "content" in content
    assert content["isError"] is False


@pytest.mark.asyncio
async def test_mcp_call_tool_fetch_incident(main_module):
    """Test calling fetch tool for an incident."""
    module, mock_client = main_module
    
    # Mock the utils.is_valid_uuid function
    mock_client.utils.is_valid_uuid = Mock(return_value=False)
    
    # Mock the incident.get_by_number function
    mock_client.incident.get_by_number = Mock(return_value={
        "id": "123",
        "number": "I-0001",
        "briefDescription": "Test incident",
        "processingStatus": {"name": "Open"},
        "caller": {"dynamicName": "John Doe"},
        "creationDate": "2024-01-01T10:00:00Z",
        "modificationDate": "2024-01-01T11:00:00Z",
        "closed": False
    })
    
    # Update the module's topdesk_client reference
    module.topdesk_client = mock_client
    
    # Create mock request with fetch payload
    mock_request = Mock()
    mock_request.json = AsyncMock(return_value={
        "name": "fetch",
        "arguments": {
            "entity": "incidents",
            "id": "I-0001"
        }
    })
    
    # Call the endpoint
    response = await module.mcp_call_tool(mock_request)
    
    # Verify response
    assert response.status_code == 200
    content = json.loads(response.body.decode())
    
    assert "content" in content
    assert content["isError"] is False
    assert "structured" in content["content"][0]
    assert content["content"][0]["structured"]["number"] == "I-0001"


@pytest.mark.asyncio
async def test_mcp_call_tool_invalid_entity(main_module):
    """Test calling search with invalid entity returns 400."""
    module, mock_client = main_module
    
    # Create mock request with invalid entity
    mock_request = Mock()
    mock_request.json = AsyncMock(return_value={
        "name": "search",
        "arguments": {
            "entity": "invalid",
            "limit": 5
        }
    })
    
    # Call the endpoint
    response = await module.mcp_call_tool(mock_request)
    
    # Verify error response
    assert response.status_code == 400
    content = json.loads(response.body.decode())
    
    assert content["isError"] is True
    assert "Invalid entity" in content["content"][0]["text"]


@pytest.mark.asyncio
async def test_mcp_call_tool_missing_arguments(main_module):
    """Test calling tool with missing arguments returns 400."""
    module, mock_client = main_module
    
    # Create mock request missing required argument
    mock_request = Mock()
    mock_request.json = AsyncMock(return_value={
        "name": "fetch",
        "arguments": {
            "entity": "incidents"
            # Missing "id"
        }
    })
    
    # Call the endpoint
    response = await module.mcp_call_tool(mock_request)
    
    # Verify error response
    assert response.status_code == 400
    content = json.loads(response.body.decode())
    
    assert content["isError"] is True
    assert "Missing required argument: id" in content["content"][0]["text"]


@pytest.mark.asyncio
async def test_mcp_call_tool_unknown_tool(main_module):
    """Test calling unknown tool returns 400."""
    module, mock_client = main_module
    
    # Create mock request with unknown tool
    mock_request = Mock()
    mock_request.json = AsyncMock(return_value={
        "name": "unknown_tool",
        "arguments": {}
    })
    
    # Call the endpoint
    response = await module.mcp_call_tool(mock_request)
    
    # Verify error response
    assert response.status_code == 400
    content = json.loads(response.body.decode())
    
    assert content["isError"] is True
    assert "Unknown tool" in content["content"][0]["text"]
