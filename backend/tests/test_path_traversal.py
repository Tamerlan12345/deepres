import pytest
import os
from unittest.mock import patch

@pytest.mark.asyncio
async def test_serve_spa_path_traversal(tmp_path):
    """Test that serve_spa correctly prevents path traversal using commonpath."""

    frontend_dist = tmp_path / "frontend" / "dist"
    frontend_dist.mkdir(parents=True)

    # Create the index.html fallback
    (frontend_dist / "index.html").write_text("index")

    # Create an out-of-bounds directory sharing a prefix
    dist_secret = tmp_path / "frontend" / "dist-secret"
    dist_secret.mkdir(parents=True)
    (dist_secret / "passwords.txt").write_text("secret")

    # Create a valid file inside the dist
    assets_dir = frontend_dist / "assets"
    assets_dir.mkdir()
    (assets_dir / "main.css").write_text("css")

    frontend_dist_str = str(frontend_dist)

    import app.main
    with patch("os.path.exists", return_value=True):
        # Even though we patched exists to return true so serve_spa is defined,
        # we need to make sure the inner function uses our frontend_dist_str

        # Reloading main won't work well with tmp_path if we don't mock the top-level
        # frontend_dist correctly before the module runs.
        # Let's just patch it on the already imported module.
        pass

    with patch("app.main.frontend_dist", frontend_dist_str):
        from app.main import serve_spa

        # Test 1: Valid path inside frontend_dist
        response = await serve_spa("assets/main.css")
        assert response.path == str(assets_dir / "main.css")

        # Test 2: Path traversal bypass attempt via sharing prefix
        # Attacker requests something like ../dist-secret/passwords.txt
        response = await serve_spa("../dist-secret/passwords.txt")
        # Should return index.html fallback, not the out-of-bounds file
        assert response.path == str(frontend_dist / "index.html")

        # Test 3: Standard path traversal out of the frontend directory
        response = await serve_spa("../../../etc/passwd")
        # Should return index.html fallback
        assert response.path == str(frontend_dist / "index.html")
