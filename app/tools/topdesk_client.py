"""MCP client for communicating with TOPdesk MCP server."""

import asyncio
import logging
import random
from typing import Dict, Any, Optional, List
import httpx
from ..config import settings
from ..security import security_manager


logger = logging.getLogger(__name__)


class MCPClientError(Exception):
    """Base exception for MCP client errors."""
    pass


class MCPTimeoutError(MCPClientError):
    """Timeout error for MCP calls."""
    pass


class MCPServerError(MCPClientError):
    """Server error from MCP calls."""
    pass


class MCPCircuitOpenError(MCPClientError):
    """Circuit breaker is open, rejecting requests."""
    pass


class TopdeskMCPClient:
    """Async client for communicating with TOPdesk MCP server or directly with TOPdesk."""
    
    def __init__(self):
        # Check if direct TOPDESK mode is enabled
        self.direct_mode = (settings.mcp_base_url == "direct-topdesk-mode" and
                           settings.topdesk_url and 
                           settings.topdesk_username and 
                           settings.topdesk_password)
        
        if self.direct_mode:
            # Direct TOPDESK connection mode
            self.topdesk_url = settings.topdesk_url
            self.topdesk_username = settings.topdesk_username
            self.topdesk_password = settings.topdesk_password
            logger.info("Using direct TOPDESK connection mode")
        else:
            # MCP server mode
            self.base_url = settings.mcp_base_url.rstrip('/')
            
        self.timeout = settings.mcp_timeout
        self.retries = settings.mcp_retries
        
        # Allowed tools for security
        self.allowed_tools = {
            "search",
            "topdesk_get_incidents_by_fiql_query", 
            "topdesk_get_person_by_query",
            "topdesk_get_operators_by_fiql_query",
            "topdesk_get_complete_incident_overview"
        }
        
        self._client: Optional[httpx.AsyncClient] = None
        self._topdesk_client = None  # For direct mode
    
    async def __aenter__(self):
        """Async context manager entry."""
        if self.direct_mode:
            await self._ensure_direct_client()
        else:
            await self._ensure_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def _ensure_direct_client(self):
        """Initialize direct TOPDESK client."""
        if self._topdesk_client is None:
            # Import here to avoid circular dependency
            from topdesk_mcp import _topdesk_sdk as topdesk_sdk
            self._topdesk_client = topdesk_sdk.connect(
                self.topdesk_url, 
                self.topdesk_username, 
                self.topdesk_password
            )
    
    async def _ensure_client(self):
        """Ensure HTTP client is initialized."""
        if self._client is None:
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "TopDesk-NL-Router/1.0"
            }
            
            # Add API key if configured
            if settings.mcp_api_key:
                headers["Authorization"] = f"Bearer {settings.mcp_api_key}"
            
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers=headers
            )
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
        # Note: Direct TOPDESK client doesn't need explicit cleanup
    
    async def call_tool(self, tool_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server or execute directly with TOPDESK.
        
        Args:
            tool_name: Name of the tool to call
            payload: Payload to send to the tool
            
        Returns:
            Response from the MCP server or direct TOPDESK API
            
        Raises:
            MCPClientError: If the tool call fails
            MCPCircuitOpenError: If circuit breaker is open
            MCPTimeoutError: If the request times out
            MCPServerError: If server returns an error
        """
        # Validate tool is allowed
        if tool_name not in self.allowed_tools:
            raise MCPClientError(f"Tool '{tool_name}' is not allowed")
        
        if self.direct_mode:
            return await self._call_tool_direct(tool_name, payload)
        else:
            return await self._call_tool_mcp(tool_name, payload)
    
    async def _call_tool_direct(self, tool_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool directly with TOPDESK API."""
        if not self._topdesk_client:
            raise MCPClientError("Direct TOPDESK client not initialized")
        
        try:
            # Map tool names to direct SDK calls
            if tool_name == "topdesk_get_incidents_by_fiql_query":
                fiql_query = payload.get("fiql_query", "")
                page_size = payload.get("page_size", 10)
                result = self._topdesk_client.incident.get_list(page_size=page_size, query=fiql_query)
            elif tool_name == "topdesk_get_person_by_query":
                fiql_query = payload.get("fiql_query", "")
                result = self._topdesk_client.person.get_list(query=fiql_query)
            elif tool_name == "topdesk_get_operators_by_fiql_query":
                fiql_query = payload.get("fiql_query", "")
                result = self._topdesk_client.operator.get_list(query=fiql_query)
            elif tool_name == "topdesk_get_complete_incident_overview":
                incident_id = payload.get("incident_id", "")
                if self._topdesk_client.utils.is_valid_uuid(incident_id):
                    result = self._topdesk_client.incident.get_by_id(incident_id)
                else:
                    result = self._topdesk_client.incident.get_by_number(incident_id)
            elif tool_name == "search":
                # For search, we'll use incident search as default
                query = payload.get("query", "")
                max_results = payload.get("max_results", 5)
                result = self._topdesk_client.incident.get_list(page_size=max_results, query=query)
            else:
                raise MCPClientError(f"Direct mode not implemented for tool '{tool_name}'")
            
            logger.debug(f"Direct TOPDESK tool {tool_name} succeeded")
            return result
            
        except Exception as e:
            logger.error(f"Direct TOPDESK tool {tool_name} failed: {e}")
            raise MCPClientError(f"Direct TOPDESK call failed: {str(e)}")
    
    async def _call_tool_mcp(self, tool_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool via MCP server."""
        
        # Check circuit breaker
        if not await security_manager.check_circuit_breaker():
            raise MCPCircuitOpenError("MCP circuit breaker is open")
        
        await self._ensure_client()
        
        url = f"{self.base_url}/tools/{tool_name}"
        
        # Retry logic with exponential backoff and jitter
        last_exception = None
        
        for attempt in range(self.retries + 1):
            try:
                logger.debug(f"Calling MCP tool {tool_name}, attempt {attempt + 1}")
                
                response = await self._client.post(url, json=payload)
                
                # Handle different response codes
                if response.status_code == 200:
                    await security_manager.record_mcp_success()
                    result = response.json()
                    logger.debug(f"MCP tool {tool_name} succeeded")
                    return result
                
                elif response.status_code == 404:
                    raise MCPClientError(f"Tool '{tool_name}' not found on MCP server")
                
                elif response.status_code == 429:
                    # Rate limited by MCP server
                    raise MCPClientError("Rate limited by MCP server")
                
                elif 500 <= response.status_code < 600:
                    # Server error - will trigger circuit breaker
                    error_msg = f"MCP server error {response.status_code}"
                    try:
                        error_detail = response.json().get("error", {})
                        error_msg = f"{error_msg}: {error_detail.get('message', 'Unknown error')}"
                    except:
                        pass
                    
                    await security_manager.record_mcp_failure()
                    raise MCPServerError(error_msg)
                
                else:
                    # Other client errors
                    error_msg = f"MCP client error {response.status_code}"
                    try:
                        error_detail = response.json().get("error", {})
                        error_msg = f"{error_msg}: {error_detail.get('message', 'Unknown error')}"
                    except:
                        pass
                    
                    raise MCPClientError(error_msg)
            
            except httpx.TimeoutException as e:
                last_exception = MCPTimeoutError(f"MCP request timed out after {self.timeout}s")
                logger.warning(f"MCP tool {tool_name} timed out, attempt {attempt + 1}")
                await security_manager.record_mcp_failure()
            
            except httpx.RequestError as e:
                last_exception = MCPClientError(f"MCP request failed: {str(e)}")
                logger.warning(f"MCP tool {tool_name} request failed: {e}, attempt {attempt + 1}")
                await security_manager.record_mcp_failure()
            
            except (MCPClientError, MCPServerError, MCPCircuitOpenError):
                # Don't retry these errors
                raise
            
            # Wait before retry with exponential backoff and jitter
            if attempt < self.retries:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                logger.debug(f"Waiting {wait_time:.2f}s before retry")
                await asyncio.sleep(wait_time)
        
        # All retries exhausted
        if last_exception:
            raise last_exception
        else:
            raise MCPClientError(f"Failed to call tool {tool_name} after {self.retries + 1} attempts")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if MCP server or direct TOPDESK connection is healthy.
        
        Returns:
            Health status information
        """
        try:
            if self.direct_mode:
                # For direct mode, check if we can query incidents
                if not self._topdesk_client:
                    await self._ensure_direct_client()
                
                # Try a simple query to check connectivity
                result = self._topdesk_client.incident.get_list(page_size=1)
                return {
                    "status": "healthy",
                    "connection_mode": "direct_topdesk",
                    "topdesk_url": self.topdesk_url
                }
            else:
                # Try to call a simple tool to check MCP connectivity
                result = await self.call_tool("list_registered_tools", {})
                return {
                    "status": "healthy",
                    "connection_mode": "mcp_server",
                    "mcp_server": "connected",
                    "tools_available": len(result) if isinstance(result, list) else "unknown"
                }
        except MCPCircuitOpenError:
            return {
                "status": "unhealthy",
                "connection_mode": "mcp_server" if not self.direct_mode else "direct_topdesk",
                "mcp_server": "circuit_breaker_open",
                "error": "Circuit breaker is open"
            }
        except Exception as e:
            return {
                "status": "unhealthy", 
                "connection_mode": "mcp_server" if not self.direct_mode else "direct_topdesk",
                "error": str(e)
            }
    
    async def list_available_tools(self) -> List[str]:
        """Get list of available tools from MCP server.
        
        Returns:
            List of available tool names
        """
        try:
            result = await self.call_tool("list_registered_tools", {})
            if isinstance(result, list):
                tool_names = []
                for tool in result:
                    if isinstance(tool, dict) and "name" in tool:
                        tool_names.append(tool["name"])
                return tool_names
            return []
        except Exception as e:
            logger.error(f"Failed to list MCP tools: {e}")
            return []


# Helper functions for common MCP calls

async def search_incidents(query: str, max_results: int = 5) -> Dict[str, Any]:
    """Search for incidents using the search tool.
    
    Args:
        query: Search query
        max_results: Maximum number of results
        
    Returns:
        Search results from MCP server
    """
    async with TopdeskMCPClient() as client:
        return await client.call_tool("search", {
            "query": query,
            "max_results": max_results
        })


async def get_incidents_by_fiql(fiql_query: str, page_size: int = 5) -> Dict[str, Any]:
    """Get incidents using FIQL query.
    
    Args:
        fiql_query: FIQL query string
        page_size: Number of results per page
        
    Returns:
        Incidents matching the FIQL query
    """
    async with TopdeskMCPClient() as client:
        return await client.call_tool("topdesk_get_incidents_by_fiql_query", {
            "fiql_query": fiql_query,
            "page_size": page_size
        })


async def get_person_by_query(fiql_query: str) -> Dict[str, Any]:
    """Get person information using FIQL query.
    
    Args:
        fiql_query: FIQL query for person search
        
    Returns:
        Person information from MCP server
    """
    async with TopdeskMCPClient() as client:
        return await client.call_tool("topdesk_get_person_by_query", {
            "fiql_query": fiql_query
        })


async def get_operators_by_fiql(fiql_query: str) -> Dict[str, Any]:
    """Get operators using FIQL query.
    
    Args:
        fiql_query: FIQL query for operator search
        
    Returns:
        Operators matching the query
    """
    async with TopdeskMCPClient() as client:
        return await client.call_tool("topdesk_get_operators_by_fiql_query", {
            "fiql_query": fiql_query
        })


async def get_complete_incident_overview(incident_id: str) -> Dict[str, Any]:
    """Get complete incident information.
    
    Args:
        incident_id: Incident ID or number
        
    Returns:
        Complete incident information
    """
    async with TopdeskMCPClient() as client:
        return await client.call_tool("topdesk_get_complete_incident_overview", {
            "incident_id": incident_id
        })