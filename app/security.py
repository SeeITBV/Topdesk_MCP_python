"""Security utilities including rate limiting and circuit breaker."""

import asyncio
import time
from collections import defaultdict, deque
from typing import Dict, Optional
from enum import Enum
from dataclasses import dataclass
from .config import settings


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Circuit breaker tripped, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service is back up


@dataclass
class TokenBucket:
    """Token bucket for rate limiting."""
    capacity: int
    tokens: float
    last_refill: float
    refill_rate: float  # tokens per second
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False if not available
        """
        now = time.time()
        
        # Refill tokens based on time elapsed
        time_passed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + time_passed * self.refill_rate)
        self.last_refill = now
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False


class RateLimiter:
    """Token bucket based rate limiter."""
    
    def __init__(self):
        self._buckets: Dict[str, TokenBucket] = {}
        self._lock = asyncio.Lock()
    
    async def is_allowed(self, key: str, tokens: int = 1) -> bool:
        """Check if request is allowed under rate limit.
        
        Args:
            key: Identifier for the rate limit (e.g., IP address)
            tokens: Number of tokens to consume
            
        Returns:
            True if request is allowed, False if rate limited
        """
        async with self._lock:
            if key not in self._buckets:
                # Create new bucket for this key
                refill_rate = settings.rate_limit_requests / settings.rate_limit_window
                self._buckets[key] = TokenBucket(
                    capacity=settings.rate_limit_requests,
                    tokens=settings.rate_limit_requests,
                    last_refill=time.time(),
                    refill_rate=refill_rate
                )
            
            return self._buckets[key].consume(tokens)
    
    async def get_remaining(self, key: str) -> int:
        """Get remaining requests for a key.
        
        Args:
            key: Identifier for the rate limit
            
        Returns:
            Number of remaining requests
        """
        async with self._lock:
            if key not in self._buckets:
                return settings.rate_limit_requests
            
            bucket = self._buckets[key]
            # Update tokens first
            now = time.time()
            time_passed = now - bucket.last_refill
            bucket.tokens = min(bucket.capacity, bucket.tokens + time_passed * bucket.refill_rate)
            bucket.last_refill = now
            
            return int(bucket.tokens)


@dataclass
class CircuitBreakerState:
    """Circuit breaker state tracking."""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0
    last_success_time: float = 0
    next_attempt_time: float = 0


class CircuitBreaker:
    """Simple circuit breaker implementation."""
    
    def __init__(self, service_name: str = "mcp"):
        self.service_name = service_name
        self._state = CircuitBreakerState()
        self._lock = asyncio.Lock()
    
    async def is_request_allowed(self) -> bool:
        """Check if request should be allowed through circuit breaker.
        
        Returns:
            True if request is allowed, False if circuit is open
        """
        async with self._lock:
            now = time.time()
            
            if self._state.state == CircuitState.CLOSED:
                return True
            elif self._state.state == CircuitState.OPEN:
                # Check if we should move to half-open
                if now >= self._state.next_attempt_time:
                    self._state.state = CircuitState.HALF_OPEN
                    return True
                return False
            else:  # HALF_OPEN
                return True
    
    async def record_success(self):
        """Record a successful request."""
        async with self._lock:
            self._state.failure_count = 0
            self._state.last_success_time = time.time()
            if self._state.state == CircuitState.HALF_OPEN:
                self._state.state = CircuitState.CLOSED
    
    async def record_failure(self):
        """Record a failed request."""
        async with self._lock:
            self._state.failure_count += 1
            self._state.last_failure_time = time.time()
            
            if self._state.failure_count >= settings.circuit_breaker_failure_threshold:
                self._state.state = CircuitState.OPEN
                self._state.next_attempt_time = (
                    time.time() + settings.circuit_breaker_recovery_timeout
                )
    
    async def get_state(self) -> dict:
        """Get current circuit breaker state.
        
        Returns:
            Dictionary with current state information
        """
        async with self._lock:
            return {
                "service": self.service_name,
                "state": self._state.state.value,
                "failure_count": self._state.failure_count,
                "last_failure_time": self._state.last_failure_time,
                "last_success_time": self._state.last_success_time,
                "next_attempt_time": self._state.next_attempt_time if self._state.state == CircuitState.OPEN else None
            }


class SecurityManager:
    """Central security manager for rate limiting and circuit breaking."""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.circuit_breaker = CircuitBreaker("mcp")
    
    async def check_rate_limit(self, client_ip: str) -> bool:
        """Check if request is within rate limits.
        
        Args:
            client_ip: Client IP address
            
        Returns:
            True if allowed, False if rate limited
        """
        return await self.rate_limiter.is_allowed(client_ip)
    
    async def get_rate_limit_remaining(self, client_ip: str) -> int:
        """Get remaining requests for client.
        
        Args:
            client_ip: Client IP address
            
        Returns:
            Number of remaining requests
        """
        return await self.rate_limiter.get_remaining(client_ip)
    
    async def check_circuit_breaker(self) -> bool:
        """Check if circuit breaker allows request.
        
        Returns:
            True if allowed, False if circuit is open
        """
        return await self.circuit_breaker.is_request_allowed()
    
    async def record_mcp_success(self):
        """Record successful MCP call."""
        await self.circuit_breaker.record_success()
    
    async def record_mcp_failure(self):
        """Record failed MCP call."""
        await self.circuit_breaker.record_failure()
    
    async def get_status(self) -> dict:
        """Get overall security status.
        
        Returns:
            Dictionary with security status information
        """
        circuit_state = await self.circuit_breaker.get_state()
        
        return {
            "rate_limiting": {
                "enabled": True,
                "max_requests": settings.rate_limit_requests,
                "window_seconds": settings.rate_limit_window
            },
            "circuit_breaker": circuit_state
        }


# Global security manager instance
security_manager = SecurityManager()


def get_client_ip(request) -> str:
    """Extract client IP from request, handling proxies.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Client IP address
    """
    # Check for forwarded headers (when behind proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # Fallback to direct connection IP
    return request.client.host if request.client else "unknown"