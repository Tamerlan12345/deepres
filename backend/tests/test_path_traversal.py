import pytest
import os
from unittest.mock import patch
from app.main import app
from fastapi.responses import FileResponse

@pytest.fixture
def mock_frontend_env(tmp_path):
    # Dynamically create test directories to avoid touching actual files
    frontend_dist = tmp_path / "frontend" / "dist"
    frontend_dist.mkdir(parents=True)

    # Create an index.html file that FileResponse will serve when falling back
    index_file = frontend_dist / "index.html"
    index_file.write_text("dummy content")

    # We also mock os.path.exists and os.path.isfile for the specific test case
    # to avoid needing a real file inside a parallel 'dist_secret' directory.

    # Temporarily set app's frontend_dist to our mock directory
    with patch("app.main.frontend_dist", str(frontend_dist)):
        yield str(frontend_dist)


@pytest.mark.asyncio
async def test_path_traversal_prevention(mock_frontend_env):
    """
    Test that path traversal attempts like '../dist_secret/file.txt'
    are properly prevented by the catch-all SPA route.
    """

    # Find the SPA catch-all route function
    # It mounts /{full_path:path}
    route_func = None
    for route in app.routes:
        if hasattr(route, "path") and route.path == "/{full_path:path}":
            route_func = route.endpoint
            break

    assert route_func is not None, "Could not find SPA catch-all route"

    frontend_dist = mock_frontend_env

    # Our malicious traversal path
    malicious_path = "../dist_secret/secret.txt"

    # Mock FileResponse so it doesn't actually try to read the file
    # and fail due to missing mime types or file not found in test env
    with patch("app.main.FileResponse") as MockFileResponse:
        await route_func(malicious_path)

        # Verify that FileResponse was called with the fallback index.html,
        # meaning the path traversal attempt was rejected
        expected_fallback = os.path.join(frontend_dist, "index.html")
        MockFileResponse.assert_called_with(expected_fallback)


@pytest.mark.asyncio
async def test_safe_path_allowed(mock_frontend_env):
    """
    Test that safe paths within the frontend dist are allowed.
    """
    route_func = None
    for route in app.routes:
        if hasattr(route, "path") and route.path == "/{full_path:path}":
            route_func = route.endpoint
            break

    assert route_func is not None, "Could not find SPA catch-all route"

    frontend_dist = mock_frontend_env

    safe_path = "assets/app.js"
    full_safe_path = os.path.normpath(os.path.join(frontend_dist, safe_path))

    with patch("app.main.os.path.exists", return_value=True), \
         patch("app.main.os.path.isfile", return_value=True), \
         patch("app.main.FileResponse") as MockFileResponse:

        await route_func(safe_path)

        # Verify that FileResponse was called with the safe path,
        # not the fallback
        MockFileResponse.assert_called_with(full_safe_path)
