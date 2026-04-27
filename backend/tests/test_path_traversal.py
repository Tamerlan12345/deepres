import pytest
import os
import sys
from unittest.mock import patch
from fastapi.testclient import TestClient

@pytest.fixture(autouse=True)
def setup_frontend_dist(tmp_path):
    # Setup mock frontend directory structure
    frontend_dist = tmp_path / "frontend" / "dist"
    os.makedirs(frontend_dist, exist_ok=True)

    # Create an index.html file
    index_file = frontend_dist / "index.html"
    index_file.write_text("Mock index.html")

    # Create a legitimate asset
    assets_dir = frontend_dist / "assets"
    os.makedirs(assets_dir, exist_ok=True)
    asset_file = assets_dir / "app.js"
    asset_file.write_text("console.log('app');")

    # Create a secret file outside the dist directory
    secrets_dir = tmp_path / "frontend" / "dist-secrets"
    os.makedirs(secrets_dir, exist_ok=True)
    secret_file = secrets_dir / "config.json"
    secret_file.write_text('{"secret": "key"}')

    # Ensure app module gets reloaded
    if 'app.main' in sys.modules:
        del sys.modules['app.main']

    yield str(frontend_dist)

@pytest.mark.asyncio
async def test_path_traversal_prevention(setup_frontend_dist):
    frontend_dist = setup_frontend_dist

    with patch("os.path.exists", side_effect=lambda p: True), \
         patch("os.path.isdir", side_effect=lambda p: True):
        import app.main

    # Set the global frontend_dist inside the module BEFORE running the test
    # This is crucial because the closure might have captured the original string
    app.main.frontend_dist = frontend_dist

    # Let's extract the actual route closure logic
    try:
        # FastAPI might bind the default argument inside the scope
        serve_spa_endpoint = next(r for r in app.main.app.routes if getattr(r, "path", None) == "/{full_path:path}").endpoint
    except StopIteration:
        pytest.fail("Could not find the catch-all route handler (serve_spa).")

    # The problem is that the `serve_spa` function captures `frontend_dist` from the global module scope at import time or execution time.
    # To fix this, we need to test the actual endpoint with mocked `frontend_dist` in `app.main` explicitly
    with patch("app.main.FileResponse") as mock_file_response, patch("app.main.frontend_dist", frontend_dist):
        mock_file_response.side_effect = lambda path: {"path": path}

        # Test 1: Accessing a file that bypasses startswith check
        with patch("os.path.exists", return_value=True), patch("os.path.isfile", return_value=True):
            response1 = await serve_spa_endpoint("../dist-secrets/config.json")
            assert str(response1["path"]).endswith("index.html")
            assert "config.json" not in str(response1["path"])

        # Test 2: Normal path traversal attempt
        with patch("os.path.exists", return_value=True), patch("os.path.isfile", return_value=True):
            response2 = await serve_spa_endpoint("../../../etc/passwd")
            assert str(response2["path"]).endswith("index.html")

        # Test 3: Legitimate access (file doesn't exist so it returns index.html)
        with patch("os.path.exists", return_value=False):
            response3 = await serve_spa_endpoint("missing.js")
            assert str(response3["path"]).endswith("index.html")

        # Test 4: Legitimate access to existing file
        with patch("os.path.exists", return_value=True), patch("os.path.isfile", return_value=True):
            response4 = await serve_spa_endpoint("assets/app.js")
            assert str(response4["path"]).endswith("assets/app.js")
