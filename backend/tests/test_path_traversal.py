import pytest
import os
import asyncio
from unittest.mock import patch

# Mock settings to avoid printing warnings
os.environ["SECRET_KEY"] = "dummy_secret_for_test"

# Because the static route code is evaluated ON IMPORT,
# we need to make sure the target directory exists before importing,
# otherwise it won't add the route!

@pytest.fixture(scope="session", autouse=True)
def setup_frontend_dist():
    os.makedirs("/app/frontend/dist", exist_ok=True)
    yield

from app.main import app

@pytest.mark.asyncio
async def test_path_traversal_prevention(tmp_path):
    # We will test the inner endpoint function directly.
    # The route should be available now.
    try:
        serve_spa_endpoint = next(r for r in app.routes if r.path == "/{full_path:path}").endpoint
    except StopIteration:
        pytest.fail("serve_spa route not found. Make sure frontend_dist exists when main.py is imported.")

    # Setup mock frontend dist and a hacked dist alongside it
    mock_frontend_dist = tmp_path / "frontend" / "dist"
    mock_hacked_dist = tmp_path / "frontend" / "dist_hacked"

    os.makedirs(mock_frontend_dist, exist_ok=True)
    os.makedirs(mock_hacked_dist, exist_ok=True)

    # Create legitimate file
    with open(mock_frontend_dist / "index.html", "w") as f:
        f.write("Legit index")

    # Create "secret" file outside the intended dist
    with open(mock_hacked_dist / "secret.txt", "w") as f:
        f.write("Secret data")

    # We need to mock frontend_dist globally in the endpoint module for testing
    with patch("app.main.frontend_dist", str(mock_frontend_dist)):
        # Also need to mock FileResponse to prevent mimetypes guess_type error on mock paths
        with patch("app.main.FileResponse") as mock_file_response:
            # 1. Test legitimate access
            await serve_spa_endpoint("index.html")
            mock_file_response.assert_called_with(os.path.normpath(str(mock_frontend_dist / "index.html")))

            # 2. Test traversal attempt that starts with the same string but escapes
            mock_file_response.reset_mock()
            await serve_spa_endpoint("../dist_hacked/secret.txt")
            # Should fallback to index.html because of commonpath check failing
            mock_file_response.assert_called_with(os.path.normpath(str(mock_frontend_dist / "index.html")))

            # 3. Test absolute path traversal attempt
            mock_file_response.reset_mock()
            await serve_spa_endpoint("/etc/passwd")
            mock_file_response.assert_called_with(os.path.normpath(str(mock_frontend_dist / "index.html")))
