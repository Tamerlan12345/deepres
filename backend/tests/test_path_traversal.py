import pytest
import os
from fastapi.responses import FileResponse
from app.main import app

@pytest.mark.asyncio
async def test_path_traversal():
    endpoint = next(r for r in app.routes if getattr(r, "path", "") == '/{full_path:path}').endpoint

    # Expected behavior is to fallback to index.html if the resolved path is outside the dist directory
    response = await endpoint("../dist_secret/secret.txt")

    assert response.path.endswith("index.html")
