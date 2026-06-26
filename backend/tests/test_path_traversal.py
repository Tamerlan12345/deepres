import pytest
import os
import shutil
from unittest.mock import patch

@pytest.fixture(scope="function", autouse=True)
def setup_tmp_frontend(tmp_path):
    # We dynamically mock main's frontend_dist to tmp_path
    import app.main

    test_dist = tmp_path / "test-dist"
    test_dist.mkdir()

    (test_dist / "index.html").write_text("Dummy index")

    # Override the module variable for the duration of the test
    original_dist = app.main.frontend_dist
    app.main.frontend_dist = str(test_dist)

    yield str(test_dist)

    # Restore
    app.main.frontend_dist = original_dist

@pytest.mark.asyncio
async def test_path_traversal_prevention(setup_tmp_frontend):
    from app.main import app
    test_dist = setup_tmp_frontend

    # Find the SPA route endpoint directly
    serve_spa_endpoint = next(
        r.endpoint for r in app.routes
        if hasattr(r, 'path') and r.path == '/{full_path:path}'
    )

    with patch('app.main.FileResponse') as mock_file_response:
        # Test normal file access (file doesn't exist, so falls back to index.html)
        await serve_spa_endpoint(full_path="assets/index.js")
        mock_file_response.assert_called_with(os.path.join(test_dist, "index.html"))

        # Test sibling directory traversal attempt
        await serve_spa_endpoint(full_path="../dist_secret/secret.txt")

        # Assert that it falls back to index.html due to commonpath check
        mock_file_response.assert_called_with(os.path.join(test_dist, "index.html"))

@pytest.mark.asyncio
async def test_path_traversal_legit(setup_tmp_frontend):
    from app.main import app
    test_dist = setup_tmp_frontend

    serve_spa_endpoint = next(
        r.endpoint for r in app.routes
        if hasattr(r, 'path') and r.path == '/{full_path:path}'
    )

    legit_file = os.path.join(test_dist, "legit.txt")
    with open(legit_file, "w") as f:
        f.write("legit")

    with patch('app.main.FileResponse') as mock_file_response:
        await serve_spa_endpoint(full_path="legit.txt")
        mock_file_response.assert_called_with(legit_file)
