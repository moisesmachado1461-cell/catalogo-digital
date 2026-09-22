from __future__ import annotations

import logging
import re
import time
import uuid
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .config import settings

logger = logging.getLogger("catalogo.requests")
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        sensitive_api = (
            request.headers.get("authorization") is not None
            or request.url.path.startswith((
                "/api/auth",
                "/api/customer",
                "/api/admin",
                "/api/super-admin",
                "/api/billing",
                "/api/subscriptions",
            ))
        )
        response.headers["Cache-Control"] = (
            "no-store, max-age=0"
            if sensitive_api
            else response.headers.get("Cache-Control", "no-cache")
        )
        if sensitive_api:
            response.headers["Pragma"] = "no-cache"
        if settings.environment.lower() == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        candidate = (request.headers.get("X-Request-ID") or "").strip()
        request_id = candidate if REQUEST_ID_RE.fullmatch(candidate) else str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (time.perf_counter() - started) * 1000
            logger.exception(
                "request_failed method=%s path=%s duration_ms=%.1f request_id=%s",
                request.method,
                request.url.path,
                elapsed_ms,
                getattr(request.state, "request_id", "-"),
            )
            raise

        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "request method=%s path=%s status=%s duration_ms=%.1f request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            getattr(request.state, "request_id", "-"),
        )
        return response


class AuthRateLimitMiddleware(BaseHTTPMiddleware):
    """Limite simples por IP para endpoints de login.

    É adequado para a instância única atual. Quando houver múltiplas instâncias,
    o contador deve migrar para Redis ou outro armazenamento compartilhado.
    """

    def __init__(self, app):
        super().__init__(app)
        self.window_seconds = 60
        self.limit = max(1, settings.login_rate_limit_per_minute)
        self.hits: dict[str, deque[float]] = defaultdict(deque)
        self._requests_seen = 0
        self._max_buckets = 10000

    def _cleanup(self, now: float) -> None:
        cutoff = now - self.window_seconds
        stale = []
        for key, bucket in self.hits.items():
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if not bucket:
                stale.append(key)
        for key in stale:
            self.hits.pop(key, None)
        if len(self.hits) > self._max_buckets:
            # Defesa de memória: remove os buckets mais antigos primeiro.
            oldest = sorted(self.hits.items(), key=lambda item: item[1][0] if item[1] else 0)
            for key, _ in oldest[: len(self.hits) - self._max_buckets]:
                self.hits.pop(key, None)

    async def dispatch(self, request, call_next):
        if request.method == "POST" and request.url.path in {"/api/auth/login", "/api/auth/token", "/api/customer/login", "/api/customer/register"}:
            forwarded = request.headers.get("x-forwarded-for", "")
            client_ip = forwarded.split(",")[0].strip() if forwarded else ""
            if not client_ip and request.client:
                client_ip = request.client.host
            client_ip = client_ip or "unknown"

            now = time.monotonic()
            self._requests_seen += 1
            if self._requests_seen % 250 == 0:
                self._cleanup(now)
            client_ip = client_ip[:128]
            bucket = self.hits[client_ip]
            cutoff = now - self.window_seconds
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= self.limit:
                retry_after = max(1, int(self.window_seconds - (now - bucket[0])))
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Muitas tentativas. Aguarde um pouco e tente novamente."},
                    headers={"Retry-After": str(retry_after)},
                )

            bucket.append(now)

        return await call_next(request)
