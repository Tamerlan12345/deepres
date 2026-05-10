import pytest
import os
import asyncio
from fastapi.testclient import TestClient

# We need to ensure the directory exists before importing app, otherwise the route isn't added
os.makedirs("/app/frontend/dist", exist_ok=True)
with open("/app/frontend/dist/index.html", "w") as f:
    f.write("test")

from app.main import app

def test_path_traversal_endpoint():
    serve_spa = next(r for r in app.routes if hasattr(r, 'path') and r.path == '/{full_path:path}').endpoint

    # Test valid path
    response = asyncio.run(serve_spa("index.html"))
    assert hasattr(response, "path")
    assert "index.html" in response.path

    # Test invalid traversal
    response = asyncio.run(serve_spa("../dist_secret/secret.txt"))
    assert hasattr(response, "path")
    assert "index.html" in response.path # Falls back to index.html
