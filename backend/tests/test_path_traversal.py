import pytest
from unittest.mock import patch, MagicMock
from app.main import app
import os
from fastapi.responses import FileResponse

# A dummy frontend_dist path for testing
TEST_FRONTEND_DIST = os.path.abspath("/tmp/mock_frontend_dist")

@pytest.fixture(autouse=True)
def setup_frontend_dir(tmp_path):
    # Ensure frontend directory exists so the route is actually registered when app is imported
    # Note: app.main has initialization code at module level:
    # if os.path.exists(frontend_dist): ...
    # This might already have evaluated to False if the dir didn't exist during initial import.
    # We will test the inner logic directly to avoid module load order issues.
    pass

@pytest.mark.asyncio
async def test_serve_spa_path_traversal_prevention():
    # We need to extract the actual endpoint function from the app's routes
    # since TestClient normalizes paths (removes ../) before hitting the endpoint.
    serve_spa_endpoint = None
    for route in app.routes:
        if getattr(route, "path", None) == "/{full_path:path}":
            serve_spa_endpoint = route.endpoint
            break

    if not serve_spa_endpoint:
        pytest.skip("Catch-all route not registered, skipping path traversal test.")

    # We need to patch the global `frontend_dist` in app.main inside the endpoint context
    with patch("app.main.frontend_dist", TEST_FRONTEND_DIST), \
         patch("app.main.os.path.exists", return_value=True), \
         patch("app.main.os.path.isfile", return_value=True), \
         patch("app.main.FileResponse") as mock_file_response:

        # Test 1: Legitimate file request
        await serve_spa_endpoint("assets/app.js")
        mock_file_response.assert_called_with(os.path.join(TEST_FRONTEND_DIST, "assets/app.js"))

        # Test 2: Basic Path Traversal attempt
        await serve_spa_endpoint("../../../etc/passwd")
        # Should fall back to index.html
        mock_file_response.assert_called_with(os.path.join(TEST_FRONTEND_DIST, "index.html"))

        # Test 3: Prefix evasion attempt (e.g., if /tmp/mock_frontend_dist_secret existed)
        # full_path = "../mock_frontend_dist_secret/secret.txt"
        # path inside: /tmp/mock_frontend_dist/../mock_frontend_dist_secret/secret.txt -> /tmp/mock_frontend_dist_secret/secret.txt
        await serve_spa_endpoint("../mock_frontend_dist_secret/secret.txt")
        mock_file_response.assert_called_with(os.path.join(TEST_FRONTEND_DIST, "index.html"))
