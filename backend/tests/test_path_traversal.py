import pytest
import os
from fastapi.responses import FileResponse
from unittest.mock import patch
from app.main import app, frontend_dist

@pytest.fixture(autouse=True)
def setup_frontend_dist():
    os.makedirs(frontend_dist, exist_ok=True)
    index_path = os.path.join(frontend_dist, "index.html")
    with open(index_path, "w") as f:
        f.write("<html><body>Test index</body></html>")
    yield
    if os.path.exists(index_path):
        os.remove(index_path)

@pytest.mark.asyncio
async def test_path_traversal_prevention_startswith_vulnerability():
    """
    Tests that a path traversal attempt which creates a prefix match
    (e.g., frontend_dist + "_secrets.txt") is rejected.
    """
    # Create a dummy secret file outside the dist directory
    parent_dir = os.path.dirname(frontend_dist)
    secret_file = os.path.join(parent_dir, "dist_secrets.txt")
    with open(secret_file, "w") as f:
        f.write("SUPER SECRET DATA")

    # Extract the endpoint logic directly to avoid TestClient path normalization
    try:
        endpoint = next(r for r in app.routes if getattr(r, "path", None) == "/{full_path:path}").endpoint
    except StopIteration:
        pytest.fail("Catch-all route not found")

    # The user requests a file that, when joined with frontend_dist, results in the secret file
    # Example: frontend_dist is '/app/frontend/dist'
    # full_path is '../dist_secrets.txt'
    # safe_path becomes '/app/frontend/dist_secrets.txt'
    # 'startswith' check: '/app/frontend/dist_secrets.txt'.startswith('/app/frontend/dist') -> True!
    full_path = "../dist_secrets.txt"

    # We mock FileResponse so we don't actually try to guess the mime type of our secret file
    # and instead just inspect what the endpoint decided to serve.
    with patch("app.main.FileResponse") as mock_file_response:
        mock_file_response.side_effect = lambda path: {"path": path} # Return dict for easy inspection

        response = await endpoint(full_path=full_path)

        # Verify that the endpoint returns the fallback index.html, not the secret file
        assert response["path"] == os.path.join(frontend_dist, "index.html")
        assert response["path"] != secret_file

    os.remove(secret_file)
