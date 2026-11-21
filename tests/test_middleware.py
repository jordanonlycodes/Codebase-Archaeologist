import asyncio

from app.middleware import UploadBoundary


def test_streaming_limit_without_content_length():
    async def scenario():
        called = False
        sent = []
        chunks = iter([b"123", b"456"])
        async def app(scope, receive, send):
            nonlocal called
            called = True
        async def receive():
            return {"type": "http.request", "body": next(chunks), "more_body": True}
        async def send(message):
            sent.append(message)
        boundary = UploadBoundary(app, max_bytes=5)
        await boundary({"type": "http", "method": "POST", "path": "/api/analyze", "headers": []}, receive, send)
        assert sent[0]["status"] == 413
        assert not called
        assert boundary.active == 0
    asyncio.run(scenario())


def test_busy_requests_rejected():
    async def scenario():
        sent = []
        async def app(scope, receive, send):
            raise AssertionError("Busy request reached parser")
        async def receive():
            raise AssertionError("Busy request body was read")
        async def send(message):
            sent.append(message)
        boundary = UploadBoundary(app)
        boundary.active = 2
        await boundary({"type": "http", "method": "POST", "path": "/api/analyze", "headers": []}, receive, send)
        assert sent[0]["status"] == 429
        assert boundary.active == 2
    asyncio.run(scenario())


def test_body_replay_and_disconnect():
    async def scenario():
        sent = []
        messages = iter([
            {"type": "http.request", "body": b"a" * 70000, "more_body": True},
            {"type": "http.request", "body": b"end", "more_body": False},
            {"type": "http.disconnect"},
        ])
        async def receive():
            return next(messages)
        async def send(message):
            sent.append(message)
        async def app(scope, receive, send):
            body = b""
            while True:
                message = await receive()
                body += message["body"]
                if not message["more_body"]:
                    break
            assert body == b"a" * 70000 + b"end"
            assert await receive() == {"type": "http.disconnect"}
        boundary = UploadBoundary(app)
        await boundary({"type": "http", "method": "POST", "path": "/api/analyze", "headers": []}, receive, send)
        assert boundary.active == 0
    asyncio.run(scenario())
