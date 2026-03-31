import pytest
import os
import shutil
from unittest.mock import patch

@pytest.fixture
def test_env(tmp_path):
    # Setup test directory structure
    frontend_dist = tmp_path / "frontend" / "dist"
    frontend_dist.mkdir(parents=True)
    index_file = frontend_dist / "index.html"
    index_file.write_text("index")

    # The file we are allowed to access
    safe_file = frontend_dist / "safe.txt"
    safe_file.write_text("safe")

    # A sibling directory designed to bypass `.startswith`
    dist_secret = tmp_path / "frontend" / "dist-secret"
    dist_secret.mkdir(parents=True)
    secret_file = dist_secret / "secret.txt"
    secret_file.write_text("secret")

    # A completely outside directory
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir(parents=True)
    outside_file = outside_dir / "outside.txt"
    outside_file.write_text("outside")

    return {
        "dist": str(frontend_dist),
        "dist_secret": str(dist_secret),
        "index_file": str(index_file),
        "safe_file": str(safe_file),
        "secret_file": str(secret_file),
        "outside_file": str(outside_file),
    }

def get_serve_spa_route():
    from app.main import app
    for route in app.routes:
        if getattr(route, 'path', '') == '/{full_path:path}':
            return route.endpoint
    return None

@pytest.mark.asyncio
async def test_serve_spa_path_traversal_sibling(test_env):
    """
    Test that a path traversal attempt targeting a sibling directory
    that shares the same prefix (e.g., `dist-secret`) is blocked.
    """
    serve_spa_route = get_serve_spa_route()

    with patch("app.main.frontend_dist", test_env["dist"]):
        # The payload to access dist-secret/secret.txt
        payload = "../dist-secret/secret.txt"

        response = await serve_spa_route(payload)

        # Should fallback to index.html
        assert response.path == os.path.join(os.path.abspath(test_env["dist"]), "index.html")

@pytest.mark.asyncio
async def test_serve_spa_path_traversal_outside(test_env):
    """
    Test that a path traversal attempt targeting a completely outside directory is blocked.
    """
    serve_spa_route = get_serve_spa_route()
    with patch("app.main.frontend_dist", test_env["dist"]):
        payload = "../../outside/outside.txt"

        response = await serve_spa_route(payload)

        assert response.path == os.path.join(os.path.abspath(test_env["dist"]), "index.html")

@pytest.mark.asyncio
async def test_serve_spa_valid_file(test_env):
    """
    Test that valid files inside the dist directory are served correctly.
    """
    serve_spa_route = get_serve_spa_route()
    with patch("app.main.frontend_dist", test_env["dist"]):
        payload = "safe.txt"

        response = await serve_spa_route(payload)

        assert response.path == os.path.abspath(test_env["safe_file"])

@pytest.mark.asyncio
async def test_serve_spa_nonexistent_file(test_env):
    """
    Test that requests for nonexistent files fall back to index.html.
    """
    serve_spa_route = get_serve_spa_route()
    with patch("app.main.frontend_dist", test_env["dist"]):
        payload = "does_not_exist.txt"

        response = await serve_spa_route(payload)

        assert response.path == os.path.join(os.path.abspath(test_env["dist"]), "index.html")
