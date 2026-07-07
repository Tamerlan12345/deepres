import os
import pytest
from unittest.mock import patch, MagicMock
import app.main

@pytest.fixture(autouse=True)
def setup_routes(tmp_path):
    # Ensure frontend_dist is valid during import of app.main
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir(exist_ok=True)

    with patch('app.main.frontend_dist', str(dist_dir)):
        yield

@pytest.mark.asyncio
@patch('app.main.FileResponse')
async def test_path_traversal_prevention(mock_file_response, tmp_path):
    # Setup dummy frontend dist structure
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir(exist_ok=True)
    index_file = dist_dir / "index.html"
    index_file.write_text("index")

    # Setup dummy secret outside dist
    secret_dir = tmp_path / "dist_secrets"
    secret_dir.mkdir()
    secret_file = secret_dir / "secret.txt"
    secret_file.write_text("secret")

    # Mock the frontend_dist variable inside app.main
    with patch('app.main.frontend_dist', str(dist_dir)):
        # Get the endpoint
        serve_spa_endpoint = next(
            r.endpoint for r in app.main.app.routes if hasattr(r, 'path') and r.path == '/{full_path:path}'
        )

        # Simulate accessing the malicious path
        # Traversal payload designed to escape the frontend_dist directory
        malicious_path = "../dist_secrets/secret.txt"

        await serve_spa_endpoint(full_path=malicious_path)

        # Verify that FileResponse was called with index.html, not the secret file
        mock_file_response.assert_called_with(os.path.join(str(dist_dir), "index.html"))

@pytest.mark.asyncio
@patch('app.main.FileResponse')
async def test_path_traversal_valid_file(mock_file_response, tmp_path):
    # Setup dummy frontend dist structure
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir(exist_ok=True)

    valid_file = dist_dir / "valid.txt"
    valid_file.write_text("valid")

    # Mock the frontend_dist variable inside app.main
    with patch('app.main.frontend_dist', str(dist_dir)):
        # Get the endpoint
        serve_spa_endpoint = next(
            r.endpoint for r in app.main.app.routes if hasattr(r, 'path') and r.path == '/{full_path:path}'
        )
        # Simulate accessing a valid path
        valid_path = "valid.txt"

        await serve_spa_endpoint(full_path=valid_path)

        # Verify that FileResponse was called with the valid file
        mock_file_response.assert_called_with(str(valid_file))
