import pytest
from fastapi.testclient import TestClient
from app.main import app
import asyncio
import os

client = TestClient(app)

@pytest.mark.asyncio
async def test_path_traversal_blocked():
    response = client.get("/../secret.txt")
    assert response.status_code == 200 # Should return index.html

    # Check bypass TestClient normalization by calling endpoint directly
    serve_spa = next(r for r in app.routes if hasattr(r, 'path') and r.path == '/{full_path:path}').endpoint

    response = await serve_spa("../../secret.txt")

    assert response.path.endswith("index.html")
