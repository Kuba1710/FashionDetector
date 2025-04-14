import time
import logging
from typing import Dict, List, Tuple, Optional, Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)

class RateLimiter(BaseHTTPMiddleware):
    """Middleware for rate limiting requests based on client IP address."""
    
    def __init__(
        self, 
        app: ASGIApp, 
        anonymous_limit: int = 10,  # Requests per hour for anonymous users
        authenticated_limit: int = 100,  # Requests per hour for authenticated users
        window_size: int = 3600,  # Window size in seconds (1 hour)
        block_time: int = 3600  # Time to block after exceeding limit (1 hour)
    ):
        """Initialize rate limiter middleware.
        
        Args:
            app: The ASGI application
            anonymous_limit: Maximum requests per hour for anonymous users
            authenticated_limit: Maximum requests per hour for authenticated users
            window_size: Time window for rate limiting in seconds
            block_time: Time to block after exceeding limit in seconds
        """
        super().__init__(app)
        self.anonymous_limit = anonymous_limit
        self.authenticated_limit = authenticated_limit
        self.window_size = window_size
        self.block_time = block_time
        
        # Store request timestamps per client
        self.request_records: Dict[str, List[float]] = defaultdict(list)
        
        # Store blocked clients with unblock time
        self.blocked_clients: Dict[str, float] = {}
        
        # Lock for thread safety
        self.lock = asyncio.Lock()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through middleware.
        
        Args:
            request: The incoming request
            call_next: The next handler in the middleware chain
            
        Returns:
            The response
        """
        # Only apply rate limiting to specific endpoints
        if self._should_rate_limit(request.url.path):
            client_ip = self._get_client_ip(request)
            
            # Check if client is blocked
            is_blocked, retry_after = await self._is_client_blocked(client_ip)
            if is_blocked:
                logger.warning(f"Blocked request from rate-limited client: {client_ip}")
                return self._rate_limit_response(retry_after)
            
            # Check rate limit
            limit_exceeded, retry_after = await self._check_rate_limit(client_ip, request)
            if limit_exceeded:
                logger.warning(f"Rate limit exceeded for client: {client_ip}")
                return self._rate_limit_response(retry_after)
            
            # Record this request
            await self._record_request(client_ip)
        
        # Process the request
        response = await call_next(request)
        
        return response
    
    async def _is_client_blocked(self, client_ip: str) -> Tuple[bool, int]:
        """Check if client is blocked.
        
        Args:
            client_ip: The client's IP address
            
        Returns:
            Tuple of (is_blocked, seconds_until_unblock)
        """
        async with self.lock:
            now = time.time()
            
            if client_ip in self.blocked_clients:
                unblock_time = self.blocked_clients[client_ip]
                
                if now >= unblock_time:
                    # Unblock client
                    del self.blocked_clients[client_ip]
                    return False, 0
                else:
                    # Still blocked
                    return True, int(unblock_time - now)
        
        return False, 0
    
    async def _check_rate_limit(self, client_ip: str, request: Request) -> Tuple[bool, int]:
        """Check if client has exceeded rate limit.
        
        Args:
            client_ip: The client's IP address
            request: The incoming request
            
        Returns:
            Tuple of (limit_exceeded, retry_after_seconds)
        """
        async with self.lock:
            now = time.time()
            window_start = now - self.window_size
            
            # Clean up old records
            if client_ip in self.request_records:
                self.request_records[client_ip] = [
                    timestamp for timestamp in self.request_records[client_ip]
                    if timestamp > window_start
                ]
            
            # Check if authenticated
            is_authenticated = self._is_authenticated(request)
            
            # Apply appropriate limit
            limit = self.authenticated_limit if is_authenticated else self.anonymous_limit
            
            # Count requests in current window
            request_count = len(self.request_records[client_ip])
            
            if request_count >= limit:
                # Block client
                self.blocked_clients[client_ip] = now + self.block_time
                return True, self.block_time
            
            return False, 0
    
    async def _record_request(self, client_ip: str) -> None:
        """Record a request from the client.
        
        Args:
            client_ip: The client's IP address
        """
        async with self.lock:
            now = time.time()
            self.request_records[client_ip].append(now)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request.
        
        Args:
            request: The incoming request
            
        Returns:
            Client IP address
        """
        # Try X-Forwarded-For header first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # The client's IP is the first one in the list
            return forwarded_for.split(",")[0].strip()
        
        # Fall back to request client host
        return request.client.host if request.client else "unknown"
    
    def _is_authenticated(self, request: Request) -> bool:
        """Check if request is from an authenticated user.
        
        Args:
            request: The incoming request
            
        Returns:
            True if authenticated, False otherwise
        """
        # Check for authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # In a real implementation, we would validate the token
            return True
        
        return False
    
    def _should_rate_limit(self, path: str) -> bool:
        """Determine if the path should be rate limited.
        
        Args:
            path: The request path
            
        Returns:
            True if should rate limit, False otherwise
        """
        # Only limit searches endpoint for now
        return path.startswith("/api/searches")
    
    def _rate_limit_response(self, retry_after: int) -> Response:
        """Create rate limit exceeded response.
        
        Args:
            retry_after: Seconds until retry is allowed
            
        Returns:
            Response with 429 status code
        """
        from fastapi.responses import JSONResponse
        
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Rate limit exceeded. Try again later.",
                "retry_after": retry_after
            },
            headers={"Retry-After": str(retry_after)}
        ) 