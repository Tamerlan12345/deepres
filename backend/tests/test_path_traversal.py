import pytest
from unittest.mock import patch, MagicMock
import os
import app.main

# We need a fixture to ensure the frontend/dist directory exists
# so that the route gets registered when we import app.main
@pytest.fixture(autouse=True, scope="session")
def create_dummy_dist():
    os.makedirs('frontend/dist', exist_ok=True)
    with open('frontend/dist/index.html', 'w') as f:
        f.write('dummy')

    # Reload the app.main module to pick up the directory
    import importlib
    importlib.reload(app.main)
    yield

    # Optional cleanup, but not strictly necessary for tests

@pytest.mark.asyncio
async def test_path_traversal_prevention(tmp_path):
    from app.main import app, frontend_dist

    # Find the SPA catch-all route endpoint
    serve_spa = next(r for r in app.routes if r.path == '/{full_path:path}').endpoint

    with patch('app.main.FileResponse') as mock_file_response, \
         patch('os.path.exists', return_value=True), \
         patch('os.path.isfile', return_value=True):

        # Test 1: Valid path
        await serve_spa("assets/main.js")
        mock_file_response.assert_called_with(os.path.normpath(os.path.join(frontend_dist, "assets/main.js")))

        # Test 2: Path traversal attack (simulating "dist_secret.txt" being outside but having "dist" prefix)
        mock_file_response.reset_mock()
        await serve_spa("../dist_secret.txt")
        # Under vulnerable startswith logic, it would try to serve it.
        # Once fixed, it should fallback to index.html
        expected_call_fixed = os.path.join(frontend_dist, "index.html")
        mock_file_response.assert_called_with(expected_call_fixed)

@pytest.mark.asyncio
async def test_path_traversal_prevention_explicit_dotdot(tmp_path):
    from app.main import app, frontend_dist

    # Find the SPA catch-all route endpoint
    serve_spa = next(r for r in app.routes if r.path == '/{full_path:path}').endpoint

    with patch('app.main.FileResponse') as mock_file_response, \
         patch('os.path.exists', return_value=True), \
         patch('os.path.isfile', return_value=True):

        # Test 3: Standard path traversal (should always have failed, but good to test)
        mock_file_response.reset_mock()
        await serve_spa("../../etc/passwd")
        expected_call_fixed = os.path.join(frontend_dist, "index.html")
        mock_file_response.assert_called_with(expected_call_fixed)
