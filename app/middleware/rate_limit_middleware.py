from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.utils.redis_helper import rate_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.max_requests = 60
        self.window_seconds = 60
        self.ignored_paths = {"/health"}

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS" or request.url.path in self.ignored_paths:
            return await call_next(request)
        xff = request.headers.get("x-forwarded-for")
        if xff:
            client_ip = xff.split(",")[0].strip()
        else:
            client_ip = request.headers.get("x-real-ip") or (request.client.host if request.client else "unknown")
        key = f"api:{client_ip}"
        if not rate_limiter.is_allowed(key, self.max_requests, self.window_seconds):
            return Response(content="Too Many Requests", status_code=429, media_type="text/plain")
        return await call_next(request)
