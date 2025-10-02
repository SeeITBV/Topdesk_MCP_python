import importlib
import sys
from unittest.mock import Mock, patch

import pytest


@pytest.fixture
def main_module(monkeypatch):
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


def test_search_uses_title_in_fiql(main_module):
    module, mock_client = main_module
    mock_client.incident.get_list.return_value = [
        {
            "id": "123",
            "number": "I-0001",
            "briefDescription": "Printer offline",
            "processingStatus": {"name": "In Progress"},
        },
        {
            "id": "456",
            "number": "I-0002",
            "briefDescription": "Printer out of ink",
            "processingStatus": None,
        },
    ]

    results = module.search(query="Printer", max_results=1)

    mock_client.incident.get_list.assert_called_once_with(query="briefDescription==*Printer*")
    
    # Check MCP format
    assert "content" in results
    assert isinstance(results["content"], list)
    assert len(results["content"]) == 1
    assert results["content"][0]["type"] == "text"
    
    # Parse the JSON results
    import json
    parsed_results = json.loads(results["content"][0]["text"])
    assert "results" in parsed_results
    assert len(parsed_results["results"]) == 1
    
    expected_result = {
        "id": "123",
        "title": "Printer offline",
        "url": "https://example.topdesk.net/tas/secure/incident?unid=123",
    }
    assert parsed_results["results"][0] == expected_result


def test_search_normalises_and_escapes_title(main_module):
    module, mock_client = main_module
    mock_client.incident.get_list.return_value = []

    result = module.search(query='  "Test"   incident  ')

    expected_query = 'briefDescription==*\\"Test\\" incident*'
    mock_client.incident.get_list.assert_called_once_with(query=expected_query)
    
    # Check MCP format with empty results
    assert "content" in result
    assert isinstance(result["content"], list)
    assert len(result["content"]) == 1
    assert result["content"][0]["type"] == "text"
    
    import json
    parsed_results = json.loads(result["content"][0]["text"])
    assert "results" in parsed_results
    assert parsed_results["results"] == []


def test_search_rejects_empty_title(main_module):
    module, _ = main_module

    with pytest.raises(Exception):  # MCPError should be wrapped by handle_mcp_error decorator
        module.search(query="   ")


def test_search_handles_api_error_string(main_module):
    """Test that search properly handles when API returns an error string instead of a list."""
    module, mock_client = main_module
    # Simulate API returning an error string (what happens when handle_topdesk_response gets a 400/500 error)
    mock_client.incident.get_list.return_value = "Bad Request: The request was invalid or cannot be served."

    # Should raise MCPError instead of AttributeError
    with pytest.raises(module.MCPError) as exc_info:
        module.search(query="test")
    
    # Check that the error message contains the API error
    assert "TOPdesk API error" in str(exc_info.value)
    assert "Bad Request" in str(exc_info.value)


def test_fetch_handles_api_error_string(main_module):
    """Test that fetch properly handles when API returns an error string instead of a dict."""
    module, mock_client = main_module
    # Simulate API returning an error string
    mock_client.incident.get_concise.return_value = "Not Found: The URI requested is invalid or the resource does not exist."

    # Should raise MCPError instead of AttributeError
    with pytest.raises(module.MCPError) as exc_info:
        module.fetch(id="nonexistent-id")
    
    # Check that the error message contains the API error
    assert "TOPdesk API error" in str(exc_info.value)
    assert "Not Found" in str(exc_info.value)


def test_fetch_returns_concise_by_default(main_module):
    module, mock_client = main_module
    mock_client.incident.get_concise.return_value = {
        "id": "abc",
        "briefDescription": "Test incident",
        "number": "I-001"
    }

    result = module.fetch("abc")

    mock_client.incident.get_concise.assert_called_once_with(incident="abc")
    
    # Check MCP format
    assert "content" in result
    assert isinstance(result["content"], list)
    assert len(result["content"]) == 1
    assert result["content"][0]["type"] == "text"
    
    import json
    parsed_result = json.loads(result["content"][0]["text"])
    assert "id" in parsed_result
    assert "title" in parsed_result
    assert "text" in parsed_result
    assert "url" in parsed_result
    assert parsed_result["id"] == "abc"
    assert parsed_result["title"] == "Test incident"


def test_fetch_can_return_full_incident(main_module):
    module, mock_client = main_module
    mock_client.incident.get.return_value = {
        "id": "abc",
        "briefDescription": "Test incident with details",
        "details": "full"
    }

    result = module.fetch("abc", concise=False)

    mock_client.incident.get.assert_called_once_with(incident="abc")
    
    # Check MCP format
    assert "content" in result
    assert isinstance(result["content"], list)
    assert len(result["content"]) == 1
    assert result["content"][0]["type"] == "text"
    
    import json
    parsed_result = json.loads(result["content"][0]["text"])
    assert "id" in parsed_result
    assert "title" in parsed_result
    assert "text" in parsed_result
    assert "url" in parsed_result
    assert "metadata" in parsed_result
    assert parsed_result["id"] == "abc"
    assert parsed_result["title"] == "Test incident with details"


def test_fetch_requires_identifier(main_module):
    module, _ = main_module

    with pytest.raises(Exception):  # MCPError should be wrapped by handle_mcp_error decorator
        module.fetch(" ")


def test_topdesk_get_incidents_by_fiql_query_handles_api_error_string(main_module):
    """Test that topdesk_get_incidents_by_fiql_query properly handles when API returns an error string."""
    module, mock_client = main_module
    # Simulate API returning an error string
    mock_client.incident.get_list.return_value = "Bad Request: query contains unknown field: 'archived'"

    # Should raise MCPError instead of trying to iterate over the string
    with pytest.raises(module.MCPError) as exc_info:
        module.topdesk_get_incidents_by_fiql_query(query="archived==True")
    
    # Check that the error message contains the API error
    assert "TOPdesk API error" in str(exc_info.value)
    assert "Bad Request" in str(exc_info.value)


