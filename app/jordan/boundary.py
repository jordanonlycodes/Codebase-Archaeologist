"""Bound bytes before JSON parsing, reads and concurrent cloud work before providers."""
import asyncio
from starlette.responses import JSONResponse


class JordanBoundary:
    def __init__(self, app):
        self.app, self.active = app, 0

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope['method'] != 'POST' or scope['path'].rstrip('/') != '/api/jordan/explain':
            return await self.app(scope, receive, send)

        async def reject(status, code, message):
            await JSONResponse({'error': {'code': code, 'message': message}}, status_code=status)(scope, receive, send)

        headers = dict(scope['headers'])
        if headers.get(b'content-type', b'').split(b';')[0].lower() != b'application/json':
            return await reject(415, 'invalid_request', 'Jordan requires application/json.')
        if self.active >= 2:
            return await reject(429, 'jordan_busy', 'Jordan is busy. Local intelligence remains available.')
        self.active += 1
        try:
            async def collect():
                body = bytearray()
                while True:
                    part = await receive()
                    if part['type'] == 'http.disconnect':
                        return None
                    if len(body) + len(part.get('body', b'')) > 32768:
                        return False
                    body.extend(part.get('body', b''))
                    if not part.get('more_body'):
                        return body

            try:
                body = await asyncio.wait_for(collect(), timeout=10)
            except asyncio.TimeoutError:
                return await reject(408, 'request_timeout', 'Jordan request upload timed out.')
            if body is None:
                return
            if body is False:
                return await reject(413, 'request_limit', 'Jordan requests are limited to 32 KiB.')
            replayed = False

            async def replay():
                nonlocal replayed
                if replayed:
                    return await receive()
                replayed = True
                return {'type': 'http.request', 'body': bytes(body), 'more_body': False}

            await self.app(scope, replay, send)
        finally:
            self.active -= 1
