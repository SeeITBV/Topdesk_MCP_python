"""FastAPI application for Natural Language → TOPdesk MCP Router."""

import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .schemas import QueryRequest, QueryResponse, ErrorResponse, HealthResponse
from .router import query_router
from .security import security_manager, get_client_ip
from .validators import ValidationError, validate_query_text, ensure_limit


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Natural Language → TOPdesk MCP Router")
    logger.info(f"MCP Base URL: {settings.mcp_base_url}")
    logger.info(f"Log Level: {settings.log_level}")
    
    yield
    
    logger.info("Shutting down Natural Language → TOPdesk MCP Router")


# Create FastAPI app
app = FastAPI(
    title="Natural Language → TOPdesk MCP Router",
    description="FastAPI service that converts natural language queries to TOPdesk MCP tool calls",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# Rate limiting dependency
async def check_rate_limit(request: Request):
    """Check rate limiting for incoming requests."""
    client_ip = get_client_ip(request)
    
    if not await security_manager.check_rate_limit(client_ip):
        remaining = await security_manager.get_rate_limit_remaining(client_ip)
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Limit: {settings.rate_limit_requests} per {settings.rate_limit_window}s",
                "remaining": remaining,
                "retry_after": settings.rate_limit_window
            }
        )
    
    return client_ip


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error="Validation Error",
            code=400,
            details={"message": str(exc)}
        ).dict()
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTP Error",
            code=exc.status_code,
            details=exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            code=500,
            details={"message": "An internal error occurred"}
        ).dict()
    )


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with basic information."""
    return {
        "service": "Natural Language → TOPdesk MCP Router",
        "version": "1.0.0",
        "description": "Convert natural language queries to TOPdesk MCP tool calls",
        "endpoints": {
            "query": "POST /ask",
            "health": "GET /health",
            "status": "GET /status"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Check MCP connectivity
        from .tools.topdesk_client import TopdeskMCPClient
        async with TopdeskMCPClient() as client:
            health_info = await client.health_check()
        
        mcp_status = health_info.get("status", "unknown")
        
        return HealthResponse(
            status="healthy" if mcp_status == "healthy" else "degraded",
            mcp_connection=mcp_status,
            version="1.0.0"
        )
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            mcp_connection="error",
            version="1.0.0"
        )


@app.get("/status", response_model=Dict[str, Any])
async def get_status():
    """Get detailed service status including security status."""
    try:
        security_status = await security_manager.get_status()
        
        # Check MCP connectivity
        from .tools.topdesk_client import TopdeskMCPClient
        async with TopdeskMCPClient() as client:
            mcp_health = await client.health_check()
        
        return {
            "service": {
                "name": "Natural Language → TOPdesk MCP Router",
                "version": "1.0.0",
                "status": "running"
            },
            "mcp_server": {
                "base_url": settings.mcp_base_url,
                "status": mcp_health.get("status", "unknown"),
                "connection": mcp_health.get("mcp_server", "unknown")
            },
            "security": security_status,
            "configuration": {
                "max_results_limit": settings.max_allowed_results,
                "default_time_window_days": settings.default_time_window,
                "request_timeout_seconds": settings.mcp_timeout
            }
        }
    
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return {
            "service": {
                "name": "Natural Language → TOPdesk MCP Router",
                "version": "1.0.0",
                "status": "error"
            },
            "error": str(e)
        }


@app.post("/ask", response_model=QueryResponse)
async def process_natural_language_query(
    request: QueryRequest,
    client_ip: str = Depends(check_rate_limit)
):
    """Process a natural language query and return structured results.
    
    This endpoint:
    1. Validates the input query
    2. Plans the execution using query planning logic
    3. Calls appropriate MCP tools
    4. Normalizes and summarizes the results
    5. Returns structured response with plan, results, and summary
    """
    start_time = time.time()
    
    try:
        # Additional validation beyond Pydantic
        validate_query_text(request.query)
        ensure_limit(request.max_results, settings.max_allowed_results)
        
        logger.info(f"Processing query from {client_ip[:8]}***", extra={
            "query_length": len(request.query),
            "max_results": request.max_results,
            "client_ip": client_ip[:8] + "***"
        })
        
        # Process the query
        response = await query_router.process_query(request, client_ip)
        
        # Add rate limit headers
        remaining = await security_manager.get_rate_limit_remaining(client_ip)
        
        # Create custom response with headers
        json_response = JSONResponse(content=response.dict())
        json_response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests)
        json_response.headers["X-RateLimit-Remaining"] = str(remaining)
        json_response.headers["X-RateLimit-Reset"] = str(int(time.time() + settings.rate_limit_window))
        
        return json_response
    
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Query processing failed: {e}", extra={
            "client_ip": client_ip[:8] + "***",
            "execution_time": time.time() - start_time
        })
        raise HTTPException(status_code=500, detail="Query processing failed")


# Add middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    start_time = time.time()
    client_ip = get_client_ip(request)
    
    # Log request
    logger.debug(f"Request: {request.method} {request.url.path}", extra={
        "client_ip": client_ip[:8] + "***",
        "method": request.method,
        "path": request.url.path
    })
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.debug(f"Response: {response.status_code}", extra={
        "client_ip": client_ip[:8] + "***",
        "status_code": response.status_code,
        "process_time": process_time
    })
    
    # Add timing header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower()
    )