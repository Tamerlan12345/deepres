import pytest
import os
from fastapi.testclient import TestClient

# Mock the directory so the route gets registered
os.makedirs("frontend/dist", exist_ok=True)
with open("frontend/dist/index.html", "w") as f:
    f.write("<html><body>Mock Index</body></html>")

from app.main import app

def test_path_traversal():
    # Bypass TestClient path normalization by grabbing the endpoint directly
    route = next(r for r in app.routes if getattr(r, 'path', None) == '/{full_path:path}').endpoint
    import asyncio

    async def run_test():
        response = await route("../../secret.txt")
        # Ensure it returns the index.html FileResponse as a fallback
        assert getattr(response, "path", "").endswith("index.html")

    asyncio.run(run_test())
