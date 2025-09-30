"""Main router for natural language queries."""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional

from .schemas import QueryRequest, QueryResponse, QueryPlan, ToolCall, NormalizedIncident
from .planning import QueryPlanner
from .tools.topdesk_client import TopdeskMCPClient
from .normalize import (
    normalize_incidents_response, normalize_person_response, 
    normalize_operator_response, sanitize_for_logging
)
from .summarize import (
    summarize_incidents, summarize_person_lookup, 
    summarize_operator_lookup, generate_error_summary
)
from .validators import ValidationError
from .security import security_manager
from .fiql import and_join


logger = logging.getLogger(__name__)


class QueryRouter:
    """Routes natural language queries to appropriate MCP tools."""
    
    def __init__(self):
        self.planner = QueryPlanner()
    
    async def process_query(self, request: QueryRequest, client_ip: str) -> QueryResponse:
        """Process a natural language query end-to-end.
        
        Args:
            request: Query request from user
            client_ip: Client IP for rate limiting
            
        Returns:
            Complete query response
        """
        start_time = time.time()
        warnings = []
        
        try:
            # Plan the query
            plan = self.planner.plan_query(request.query, request.max_results)
            
            # If clarification needed, return early
            if plan.clarify:
                return QueryResponse(
                    plan=plan,
                    tool_calls=[],
                    raw={},
                    results=[],
                    summary=plan.clarify,
                    execution_time=time.time() - start_time,
                    warnings=[]
                )
            
            # Execute the plan
            raw_responses, executed_tools = await self._execute_plan(plan)
            
            # Normalize results
            incidents, extra_info = await self._normalize_results(plan, raw_responses)
            
            # Generate summary
            summary = await self._generate_summary(plan, incidents, extra_info, request.query)
            
            # Collect all warnings
            all_warnings = plan.warnings + warnings
            
            execution_time = time.time() - start_time
            
            # Log successful query (sanitized)
            logger.info(f"Query processed successfully", extra={
                "query_intent": plan.intent,
                "tools_used": [tool.name for tool in executed_tools],
                "results_count": len(incidents),
                "execution_time": execution_time,
                "client_ip": client_ip[:8] + "***"  # Partial IP for privacy
            })
            
            return QueryResponse(
                plan=plan,
                tool_calls=executed_tools,
                raw=sanitize_for_logging(raw_responses),
                results=incidents,
                summary=summary,
                execution_time=execution_time,
                warnings=all_warnings
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            error_summary = generate_error_summary(str(e), request.query)
            
            logger.error(f"Query processing failed", extra={
                "error": str(e),
                "query_sanitized": request.query[:50] + "..." if len(request.query) > 50 else request.query,
                "execution_time": execution_time,
                "client_ip": client_ip[:8] + "***"
            })
            
            # Return error response in expected format
            return QueryResponse(
                plan=QueryPlan(intent="Error", steps=[], tool_calls=[]),
                tool_calls=[],
                raw={"error": str(e)},
                results=[],
                summary=error_summary,
                execution_time=execution_time,
                warnings=[f"Error: {str(e)}"]
            )
    
    async def _execute_plan(self, plan: QueryPlan) -> tuple[Dict[str, Any], List[ToolCall]]:
        """Execute the planned tool calls.
        
        Args:
            plan: Query execution plan
            
        Returns:
            Tuple of (raw_responses, executed_tools)
        """
        raw_responses = {}
        executed_tools = []
        
        async with TopdeskMCPClient() as client:
            for i, tool_call in enumerate(plan.tool_calls):
                try:
                    logger.debug(f"Executing tool {tool_call.name} with payload: {sanitize_for_logging(tool_call.payload)}")
                    
                    # Handle multi-step queries that depend on previous results
                    if "PLACEHOLDER" in str(tool_call.payload):
                        tool_call = await self._resolve_placeholder(tool_call, raw_responses)
                    
                    response = await client.call_tool(tool_call.name, tool_call.payload)
                    raw_responses[f"step_{i+1}_{tool_call.name}"] = response
                    executed_tools.append(tool_call)
                    
                    logger.debug(f"Tool {tool_call.name} completed successfully")
                
                except Exception as e:
                    logger.error(f"Tool {tool_call.name} failed: {e}")
                    raw_responses[f"step_{i+1}_{tool_call.name}"] = {"error": str(e)}
                    # Continue with other tools even if one fails
        
        return raw_responses, executed_tools
    
    async def _resolve_placeholder(self, tool_call: ToolCall, previous_responses: Dict[str, Any]) -> ToolCall:
        """Resolve placeholder values in tool calls based on previous responses.
        
        Args:
            tool_call: Tool call with potential placeholders
            previous_responses: Results from previous tool calls
            
        Returns:
            Tool call with placeholders resolved
        """
        payload = tool_call.payload.copy()
        
        # Look for FIQL query with caller.id==PLACEHOLDER
        if "fiql_query" in payload and "caller.id==PLACEHOLDER" in payload["fiql_query"]:
            # Find person ID from previous person lookup
            person_id = None
            for response_key, response in previous_responses.items():
                if "person" in response_key:
                    person_info = normalize_person_response(response)
                    if person_info and person_info.get("id"):
                        person_id = person_info["id"]
                        break
            
            if person_id:
                # Replace placeholder with actual person ID
                fiql_query = payload["fiql_query"]
                fiql_query = fiql_query.replace("caller.id==PLACEHOLDER", f"caller.id=='{person_id}'")
                payload["fiql_query"] = fiql_query
            else:
                # No person ID found, use impossible condition to return no results
                fiql_query = payload["fiql_query"]
                fiql_query = fiql_query.replace("caller.id==PLACEHOLDER", "caller.id=='NOTFOUND'")
                payload["fiql_query"] = fiql_query
        
        # Look for operator.id==PLACEHOLDER
        elif "fiql_query" in payload and "operator.id==PLACEHOLDER" in payload["fiql_query"]:
            # Find operator ID from previous operator lookup
            operator_id = None
            for response_key, response in previous_responses.items():
                if "operator" in response_key:
                    operator_info = normalize_operator_response(response)
                    if operator_info and operator_info.get("id"):
                        operator_id = operator_info["id"]
                        break
            
            if operator_id:
                # Replace placeholder with actual operator ID
                fiql_query = payload["fiql_query"]
                fiql_query = fiql_query.replace("operator.id==PLACEHOLDER", f"operator.id=='{operator_id}'")
                payload["fiql_query"] = fiql_query
            else:
                # No operator ID found, use impossible condition
                fiql_query = payload["fiql_query"]
                fiql_query = fiql_query.replace("operator.id==PLACEHOLDER", "operator.id=='NOTFOUND'")
                payload["fiql_query"] = fiql_query
        
        return ToolCall(name=tool_call.name, payload=payload)
    
    async def _normalize_results(self, plan: QueryPlan, raw_responses: Dict[str, Any]) -> tuple[List[NormalizedIncident], Dict[str, Any]]:
        """Normalize raw MCP responses to structured results.
        
        Args:
            plan: Original query plan
            raw_responses: Raw responses from MCP tools
            
        Returns:
            Tuple of (normalized_incidents, extra_info)
        """
        incidents = []
        extra_info = {}
        
        # Extract person/operator info if available
        for response_key, response in raw_responses.items():
            if "person" in response_key and not response.get("error"):
                person_info = normalize_person_response(response)
                if person_info:
                    extra_info["person"] = person_info
            
            elif "operator" in response_key and not response.get("error"):
                operator_info = normalize_operator_response(response)
                if operator_info:
                    extra_info["operator"] = operator_info
            
            elif any(tool in response_key for tool in ["incidents", "search", "complete"]) and not response.get("error"):
                # This response contains incidents
                if "complete_incident_overview" in response_key:
                    # Single incident from complete overview
                    if isinstance(response, dict) and "id" in response:
                        normalized = normalize_incidents_response([response])
                        incidents.extend(normalized)
                else:
                    # Multiple incidents
                    normalized = normalize_incidents_response(response)
                    incidents.extend(normalized)
        
        return incidents, extra_info
    
    async def _generate_summary(self, plan: QueryPlan, incidents: List[NormalizedIncident], 
                              extra_info: Dict[str, Any], original_query: str) -> str:
        """Generate natural language summary of results.
        
        Args:
            plan: Original query plan
            incidents: Normalized incident results
            extra_info: Additional information (person, operator, etc.)
            original_query: Original user query
            
        Returns:
            Natural language summary
        """
        try:
            # Handle different query types for better summaries
            if "person" in extra_info:
                return summarize_person_lookup(extra_info["person"], incidents, original_query)
            
            elif "operator" in extra_info:
                return summarize_operator_lookup(extra_info["operator"], incidents, original_query)
            
            else:
                return summarize_incidents(incidents, original_query)
        
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            
            # Fallback to basic summary
            count = len(incidents)
            if count == 0:
                return "No incidents found matching your query."
            elif count == 1:
                return "Found 1 incident matching your query."
            else:
                return f"Found {count} incidents matching your query."


# Global router instance
query_router = QueryRouter()