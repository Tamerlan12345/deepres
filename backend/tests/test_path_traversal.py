import pytest
import os
from unittest.mock import patch
import asyncio

@pytest.fixture(scope="session", autouse=True)
def setup_frontend_dir(tmp_path_factory):
    # Ensure frontend/dist exists before app initialization
    # Because app.main checks os.path.exists(frontend_dist) at module load level
    # We shouldn't create it in the real project, but app.main gets it dynamically.
    # To be safe, we just make sure there's NO destructive write.
    # We will use patch to change frontend_dist inside the test.
    # BUT app.main evaluates frontend_dist at module load time.
    yield

@pytest.mark.asyncio
async def test_path_traversal_prevention(tmp_path):
    import app.main
    from app.main import app as fastapi_app

    # We need to test the logic without destroying real files.
    # We can patch the frontend_dist variable inside the endpoint.

    # Extract the serve_spa endpoint
    endpoint = None
    for r in fastapi_app.routes:
        if hasattr(r, 'path') and r.path == '/{full_path:path}':
            endpoint = r.endpoint
            break

    assert endpoint is not None, "serve_spa endpoint not found"

    # Create a safe temporary directory to act as frontend_dist
    mock_dist = tmp_path / "dist"
    mock_dist.mkdir()
    (mock_dist / "index.html").write_text("mock index")
    (mock_dist / "valid.txt").write_text("valid")

    # Patch the global variable in app.main
    with patch('app.main.frontend_dist', str(mock_dist)):
        with patch('app.main.FileResponse') as mock_file_response:
            # mock FileResponse so it just returns the path it was called with
            mock_file_response.side_effect = lambda path: path

            # Test 1: Valid file inside dist
            result = await endpoint(full_path="valid.txt")
            assert result == os.path.join(str(mock_dist), "valid.txt")

            # Test 2: Path traversal attempt
            result = await endpoint(full_path="../secret.txt")
            assert result == os.path.join(str(mock_dist), "index.html")

            # Test 3: Absolute path traversal
            result = await endpoint(full_path="/etc/passwd")
            assert result == os.path.join(str(mock_dist), "index.html")
