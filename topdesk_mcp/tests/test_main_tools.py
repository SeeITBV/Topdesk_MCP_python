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

    results = module.search("Printer", max_results=1)

    mock_client.incident.get_list.assert_called_once_with(query="briefDescription==*Printer*")
    assert results == [
        {
            "id": "123",
            "number": "I-0001",
            "title": "Printer offline",
            "processingStatus": "In Progress",
        }
    ]


def test_search_normalises_and_escapes_title(main_module):
    module, mock_client = main_module
    mock_client.incident.get_list.return_value = []

    module.search('  "Test"   incident  ')

    expected_query = 'briefDescription==*\\"Test\\" incident*'
    mock_client.incident.get_list.assert_called_once_with(query=expected_query)


def test_search_rejects_empty_title(main_module):
    module, _ = main_module

    with pytest.raises(ValueError):
        module.search("   ")


def test_fetch_returns_concise_by_default(main_module):
    module, mock_client = main_module
    mock_client.incident.get_concise.return_value = {"id": "abc"}

    result = module.fetch("abc")

    mock_client.incident.get_concise.assert_called_once_with(incident="abc")
    assert result == {"id": "abc"}


def test_fetch_can_return_full_incident(main_module):
    module, mock_client = main_module
    mock_client.incident.get.return_value = {"id": "abc", "details": "full"}

    result = module.fetch("abc", concise=False)

    mock_client.incident.get.assert_called_once_with(incident="abc")
    assert result == {"id": "abc", "details": "full"}


def test_fetch_requires_identifier(main_module):
    module, _ = main_module

    with pytest.raises(ValueError):
        module.fetch(" ")
