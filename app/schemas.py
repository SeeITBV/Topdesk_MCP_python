"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from datetime import datetime


class QueryRequest(BaseModel):
    """Request schema for natural language queries."""
    
    query: str = Field(..., min_length=1, max_length=1000, description="Natural language query")
    max_results: int = Field(5, ge=1, le=25, description="Maximum number of results to return")
    
    @validator('query')
    def validate_query(cls, v):
        """Validate query is not empty after stripping."""
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


class ToolCall(BaseModel):
    """Schema for MCP tool calls."""
    
    name: str = Field(..., description="Name of the MCP tool")
    payload: Dict[str, Any] = Field(..., description="Payload for the tool call")


class PlanStep(BaseModel):
    """Schema for individual plan steps."""
    
    step: int = Field(..., description="Step number")
    action: str = Field(..., description="Description of the action")
    tool_name: Optional[str] = Field(None, description="MCP tool to be called")
    reasoning: str = Field(..., description="Reasoning for this step")


class QueryPlan(BaseModel):
    """Schema for query execution plan."""
    
    intent: str = Field(..., description="Detected intent from the query")
    steps: List[PlanStep] = Field(..., description="Planned execution steps")
    tool_calls: List[ToolCall] = Field(..., description="Tool calls to be executed")
    clarify: Optional[str] = Field(None, description="Clarification needed from user")
    warnings: List[str] = Field(default_factory=list, description="Warnings about the plan")


class NormalizedIncident(BaseModel):
    """Normalized incident structure."""
    
    id: str = Field(..., description="Incident ID")
    number: str = Field(..., description="Incident number")
    title: str = Field(..., description="Incident title/brief description")
    status: str = Field(..., description="Current status")
    created_at: str = Field(..., description="Creation timestamp")
    priority: Optional[str] = Field(None, description="Priority level")
    caller: Optional[str] = Field(None, description="Caller name")
    operator: Optional[str] = Field(None, description="Assigned operator")
    operator_group: Optional[str] = Field(None, description="Operator group")


class QueryResponse(BaseModel):
    """Response schema for natural language queries."""
    
    plan: QueryPlan = Field(..., description="Execution plan for the query")
    tool_calls: List[ToolCall] = Field(..., description="Actual tool calls made")
    raw: Dict[str, Any] = Field(..., description="Raw MCP responses (sanitized)")
    results: List[NormalizedIncident] = Field(..., description="Normalized results")
    summary: str = Field(..., description="Natural language summary of results")
    execution_time: float = Field(..., description="Total execution time in seconds")
    warnings: List[str] = Field(default_factory=list, description="Any warnings or issues")


class ErrorResponse(BaseModel):
    """Error response schema."""
    
    error: str = Field(..., description="Error message")
    code: int = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class HealthResponse(BaseModel):
    """Health check response schema."""
    
    status: str = Field(..., description="Service status")
    mcp_connection: str = Field(..., description="MCP server connection status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    version: str = Field(..., description="Service version")