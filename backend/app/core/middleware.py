import logging
import time

from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RequestLimitsMiddleware:
    def __init__(self, app, max_bytes: int):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        started = time.perf_counter()
        max_bytes = min(self.max_bytes, 1024 * 1024) if scope["path"].endswith("/export") else self.max_bytes
        headers = dict(scope.get("headers", []))
        try:
            length = int(headers.get(b"content-length", b"0"))
            if length < 0:
                raise ValueError
        except ValueError:
            return await JSONResponse({"detail": "Invalid content length."}, status_code=400)(scope, receive, send)
        if length > max_bytes:
            return await JSONResponse({"detail": "Upload exceeds the total request limit."}, status_code=413)(scope, receive, send)
        received = 0

        async def limited_receive():
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > max_bytes:
                    raise HTTPException(413, "Upload exceeds the total request limit.")
            return message

        async def safe_send(message):
            if message["type"] == "http.response.start":
                message["headers"] = list(message.get("headers", [])) + [
                    (b"cache-control", b"no-store"),
                    (b"x-content-type-options", b"nosniff"),
                    (b"referrer-policy", b"no-referrer"),
                ]
                logger.info("request_finished method=%s status=%d duration_ms=%.2f",
                            scope["method"], message["status"], (time.perf_counter() - started) * 1000)
            await send(message)

        return await self.app(scope, limited_receive, safe_send)
