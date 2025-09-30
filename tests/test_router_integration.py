"""Integration tests for the query router."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.router import QueryRouter
from app.schemas import QueryRequest, NormalizedIncident


class TestQueryRouterIntegration:
    """Test the QueryRouter end-to-end processing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.router = QueryRouter()
    
    @pytest.mark.asyncio
    @patch('app.tools.topdesk_client.TopdeskMCPClient')
    async def test_simple_search_query(self, mock_client_class):
        """Test processing a simple search query."""
        # Mock the client
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock search response
        mock_client.call_tool.return_value = {
            "incidents": [
                {
                    "id": "123",
                    "number": "I-240101-001",
                    "briefDescription": "Email not working",
                    "status": {"name": "Open"},
                    "creationDate": "2024-01-01T10:00:00Z",
                    "priority": {"name": "Medium"},
                    "caller": {"firstName": "John", "surname": "Doe"}
                }
            ]
        }
        
        request = QueryRequest(query="email problem", max_results=5)
        response = await self.router.process_query(request, "192.168.1.1")
        
        assert response.plan.intent == "Search for: email problem"
        assert len(response.results) == 1
        assert response.results[0].title == "Email not working"
        assert "email problem" in response.summary.lower() or "1" in response.summary
        assert response.execution_time > 0
    
    @pytest.mark.asyncio
    @patch('app.tools.topdesk_client.TopdeskMCPClient')
    async def test_person_query_two_steps(self, mock_client_class):
        """Test processing a person query that requires two steps."""
        # Mock the client
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock person lookup response
        person_response = {
            "persons": [
                {
                    "id": "person-123",
                    "firstName": "John",
                    "surname": "Doe",
                    "email": "john.doe@example.com"
                }
            ]
        }
        
        # Mock incidents response
        incidents_response = {
            "incidents": [
                {
                    "id": "inc-456",
                    "number": "I-240101-002",
                    "briefDescription": "Password reset",
                    "status": {"name": "Open"},
                    "creationDate": "2024-01-01T11:00:00Z",
                    "caller": {"id": "person-123", "firstName": "John", "surname": "Doe"}
                }
            ]
        }
        
        # Configure mock to return different responses for different calls
        mock_client.call_tool.side_effect = [person_response, incidents_response]
        
        request = QueryRequest(query="tickets for John Doe", max_results=5)
        response = await self.router.process_query(request, "192.168.1.1")
        
        assert "person" in response.plan.intent.lower()
        assert len(response.tool_calls) == 2
        assert response.tool_calls[0].name == "topdesk_get_person_by_query"
        assert response.tool_calls[1].name == "topdesk_get_incidents_by_fiql_query"
        assert len(response.results) == 1
        assert "john doe" in response.summary.lower() or "john" in response.summary.lower()
    
    @pytest.mark.asyncio
    @patch('app.tools.topdesk_client.TopdeskMCPClient')
    async def test_complete_incident_query(self, mock_client_class):
        """Test processing a complete incident overview query."""
        # Mock the client
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock complete incident response
        mock_client.call_tool.return_value = {
            "id": "inc-789",
            "number": "I-240101-003",
            "briefDescription": "Server down",
            "status": {"name": "In Progress"},
            "creationDate": "2024-01-01T12:00:00Z",
            "priority": {"name": "High"},
            "caller": {"firstName": "Jane", "surname": "Smith"},
            "operator": {"firstName": "Admin", "surname": "User"}
        }
        
        request = QueryRequest(query="show complete details for incident I-240101-003")
        response = await self.router.process_query(request, "192.168.1.1")
        
        assert "complete details" in response.plan.intent.lower()
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].name == "topdesk_get_complete_incident_overview"
        assert response.tool_calls[0].payload["incident_id"] == "I-240101-003"
        assert len(response.results) == 1
        assert response.results[0].number == "I-240101-003"
    
    @pytest.mark.asyncio
    async def test_clarification_needed(self):
        """Test when query needs clarification."""
        request = QueryRequest(query="tickets for Sander")
        response = await self.router.process_query(request, "192.168.1.1")
        
        assert response.plan.clarify is not None
        assert len(response.tool_calls) == 0
        assert len(response.results) == 0
        assert "clarification" in response.plan.clarify.lower() or "specify" in response.plan.clarify.lower()
    
    @pytest.mark.asyncio
    @patch('app.tools.topdesk_client.TopdeskMCPClient')
    async def test_mcp_error_handling(self, mock_client_class):
        """Test handling of MCP client errors."""
        # Mock the client to raise an error
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.call_tool.side_effect = Exception("MCP server timeout")
        
        request = QueryRequest(query="email problem", max_results=5)
        response = await self.router.process_query(request, "192.168.1.1")
        
        # Should return error response but not crash
        assert "error" in response.summary.lower() or "timeout" in response.summary.lower()
        assert len(response.warnings) > 0
        assert response.execution_time > 0
    
    @pytest.mark.asyncio
    @patch('app.tools.topdesk_client.TopdeskMCPClient')
    async def test_empty_results(self, mock_client_class):
        """Test handling when no results are found."""
        # Mock the client
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.call_tool.return_value = {"incidents": []}
        
        request = QueryRequest(query="nonexistent problem", max_results=5)
        response = await self.router.process_query(request, "192.168.1.1")
        
        assert len(response.results) == 0
        assert "no incidents found" in response.summary.lower()
    
    @pytest.mark.asyncio
    @patch('app.tools.topdesk_client.TopdeskMCPClient')
    async def test_placeholder_resolution(self, mock_client_class):
        """Test that placeholders in FIQL queries are resolved correctly."""
        # Mock the client
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # First call returns person, second call should have resolved placeholder
        person_response = {
            "persons": [{"id": "person-123", "firstName": "John", "surname": "Doe"}]
        }
        incidents_response = {"incidents": []}
        
        mock_client.call_tool.side_effect = [person_response, incidents_response]
        
        request = QueryRequest(query="tickets for John Doe")
        response = await self.router.process_query(request, "192.168.1.1")
        
        # Verify that the second call had the placeholder resolved
        assert len(mock_client.call_tool.call_args_list) == 2
        second_call_payload = mock_client.call_tool.call_args_list[1][0][1]
        fiql_query = second_call_payload["fiql_query"]
        
        # Should have person-123 instead of PLACEHOLDER
        assert "person-123" in fiql_query
        assert "PLACEHOLDER" not in fiql_query


class TestQueryRouterNormalization:
    """Test result normalization in the router."""
    
    def setup_method(self):
        self.router = QueryRouter()
    
    @pytest.mark.asyncio
    async def test_normalize_incidents_response(self):
        """Test incident normalization from raw MCP response."""
        raw_responses = {
            "step_1_search": {
                "incidents": [
                    {
                        "id": "123",
                        "number": "I-240101-001",
                        "briefDescription": "Test incident",
                        "status": {"name": "Open"},
                        "creationDate": "2024-01-01T10:00:00Z",
                        "priority": {"name": "High"},
                        "caller": {"firstName": "John", "surname": "Doe"}
                    }
                ]
            }
        }
        
        plan = MagicMock()
        plan.intent = "test"
        
        incidents, extra_info = await self.router._normalize_results(plan, raw_responses)
        
        assert len(incidents) == 1
        assert incidents[0].id == "123"
        assert incidents[0].number == "I-240101-001"
        assert incidents[0].title == "Test incident"
        assert incidents[0].status == "Open"
        assert incidents[0].priority == "High"
    
    @pytest.mark.asyncio
    async def test_normalize_with_person_info(self):
        """Test normalization that includes person information."""
        raw_responses = {
            "step_1_topdesk_get_person_by_query": {
                "persons": [
                    {
                        "id": "person-123",
                        "firstName": "John", 
                        "surname": "Doe",
                        "email": "john.doe@example.com"
                    }
                ]
            },
            "step_2_topdesk_get_incidents_by_fiql_query": {
                "incidents": []
            }
        }
        
        plan = MagicMock()
        incidents, extra_info = await self.router._normalize_results(plan, raw_responses)
        
        assert "person" in extra_info
        assert extra_info["person"]["id"] == "person-123"
        assert extra_info["person"]["name"] == "John Doe"
        assert extra_info["person"]["email"] == "john.doe@example.com"