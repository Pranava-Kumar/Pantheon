"""
Rate limiter instances for Project Pantheon API.

Centralized rate limiter definitions to avoid circular imports
and ensure proper cleanup task management.
"""

from pantheon.api.rate_limiter import RateLimiter

# Global rate limiter for general endpoints (60 requests per minute)
global_rate_limiter = RateLimiter(requests_limit=60, window_seconds=60)

# Stricter rate limiter for authentication endpoints (5 requests per minute)
# Prevents brute-force attacks on login
auth_rate_limiter = RateLimiter(requests_limit=5, window_seconds=60)

# Rate limiter for expensive analysis trigger endpoint (5 requests per hour)
# Prevents API budget exhaustion from excessive analysis runs
trigger_rate_limiter = RateLimiter(requests_limit=5, window_seconds=3600)
