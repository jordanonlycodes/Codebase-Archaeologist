"""Limit request bytes before multipart parsing and bound concurrent analyses."""

import asyncio
from starlette.responses import JSONResponse

from app.config import LIMITS, GITHUB_LIMITS


class UploadBoundary:
    def __init__(self, app, max_bytes: int = LIMITS.upload_bytes + 1024 * 1024,
                 max_active: int = 2):
        self.app = app
        self.max_bytes = max_bytes
        self.max_active = max_active
        self.active = 0

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "POST" or scope["path"].rstrip("/") not in {"/api/analyze", "/api/analyze/github"}:
            return await self.app(scope, receive, send)

        async def reject(status, code, message):
            await JSONResponse({"error": {"code": code, "message": message}}, status_code=status)(scope, receive, send)

        github = scope["path"].rstrip("/") == "/api/analyze/github"
        maximum = GITHUB_LIMITS.request_bytes if github else self.max_bytes
        limit_message = "GitHub request exceeds 4 KiB." if github else "Request exceeds the 26 MiB transport limit. ZIP files must be at most 25 MiB."
        headers = dict(scope["headers"])
        try:
            length = int(headers.get(b"content-length", b"0"))
        except ValueError:
            return await reject(400, "invalid_request", "Invalid Content-Length header.")
        if length < 0:
            return await reject(400, "invalid_request", "Invalid Content-Length header.")
        if length > maximum:
            return await reject(413, "upload_limit", limit_message)
        if self.active >= self.max_active:
            return await reject(429, "busy", "Two analyses are already running. Please try again shortly.")
        self.active += 1
        try:
            # At most two bounded bodies per process. Check actual streamed bytes,
            # including when Content-Length is absent or deliberately incorrect.
            body = bytearray()
            deadline = asyncio.get_running_loop().time() + 120
            while True:
                remaining = deadline - asyncio.get_running_loop().time()
                if remaining <= 0:
                    return await reject(408, "upload_timeout", "Upload timed out. Please try again.")
                try:
                    message = await asyncio.wait_for(receive(), timeout=remaining)
                except asyncio.TimeoutError:
                    return await reject(408, "upload_timeout", "Upload timed out. Please try again.")
                if message["type"] == "http.disconnect":
                    return
                chunk = message.get("body", b"")
                if len(body) + len(chunk) > maximum:
                    return await reject(413, "upload_limit", limit_message)
                body.extend(chunk)
                if not message.get("more_body", False):
                    break

            offset = 0
            replay_complete = False

            async def replay():
                nonlocal offset, replay_complete
                if replay_complete:
                    return await receive()  # Preserve disconnect semantics.
                chunk = bytes(body[offset:offset + 64 * 1024])
                offset += len(chunk)
                more = offset < len(body)
                if not more:
                    body.clear()
                    replay_complete = True
                return {"type": "http.request", "body": chunk, "more_body": more}

            await self.app(scope, replay, send)
        finally:
            self.active -= 1
