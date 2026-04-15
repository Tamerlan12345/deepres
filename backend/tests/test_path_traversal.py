import pytest
import os
from unittest.mock import patch
from fastapi.testclient import TestClient

@pytest.fixture
def temp_frontend_dist(tmp_path):
    """Create a temporary directory for frontend dist."""
    dist_dir = tmp_path / "frontend" / "dist"
    dist_dir.mkdir(parents=True)

    # Create a dummy index.html
    index_file = dist_dir / "index.html"
    index_file.write_text("<html><body>Test SPA</body></html>")

    return str(dist_dir)

def test_path_traversal_prevention(temp_frontend_dist):
    """Test that path traversal attempts fallback to index.html"""
    # Mock the frontend_dist variable in main.py to use our temporary directory
    with patch('app.main.frontend_dist', temp_frontend_dist):
        from app.main import app

        # Need to extract the endpoint directly because TestClient normalizes paths automatically
        route = next(r for r in app.routes if r.path == '/{full_path:path}')
        endpoint = route.endpoint

        # 1. Test normal file access
        with patch('app.main.FileResponse') as mock_file_response:
            import asyncio
            asyncio.run(endpoint("index.html"))
            # It should try to serve index.html
            args, _ = mock_file_response.call_args
            assert "index.html" in args[0]

        # 2. Test path traversal access (e.g. going up one dir to find an unexpected file)
        with patch('app.main.FileResponse') as mock_file_response:
            import asyncio
            # Imagine a file like 'app/main.py' is outside 'frontend/dist'
            asyncio.run(endpoint("../../../backend/app/main.py"))

            # It should NOT serve the traversed file, it should fallback to index.html
            args, _ = mock_file_response.call_args
            assert args[0].endswith("index.html")
            assert "main.py" not in args[0]

        # 3. Test path traversal access mimicking startswith bypass
        with patch('app.main.FileResponse') as mock_file_response:
            import asyncio
            # E.g., if frontend_dist is '/app/frontend/dist'
            # A file in '/app/frontend/dist-secret/passwords.txt' would pass `startswith('/app/frontend/dist')`
            # But should be blocked by `commonpath`
            asyncio.run(endpoint("../dist-secret/passwords.txt"))

            args, _ = mock_file_response.call_args
            assert args[0].endswith("index.html")
            assert "passwords.txt" not in args[0]
