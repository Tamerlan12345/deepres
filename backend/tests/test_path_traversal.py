import pytest
import os
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_path_traversal_serve_spa(tmp_path):
    safe_dir = tmp_path / "dist"
    safe_dir.mkdir(parents=True, exist_ok=True)
    (safe_dir / "index.html").write_text("dummy index")
    (safe_dir / "app.js").write_text("dummy js")

    secret_dir = tmp_path / "dist_secret"
    secret_dir.mkdir(parents=True, exist_ok=True)
    (secret_dir / "secret.txt").write_text("this is a secret")

    # Mock os.path.exists and os.path.isfile temporarily to force the route registration
    # during import if it checks statically, but actually main.py just checks at module level

    with patch("os.path.isdir", return_value=True), patch("os.path.exists", return_value=True), patch("os.path.isfile", return_value=True):
        from app.main import app, frontend_dist

    serve_spa = next(r for r in app.routes if getattr(r, 'path', '') == '/{full_path:path}').endpoint

    # Now we patch the endpoint variables to use our tmp paths
    with patch("app.main.frontend_dist", str(safe_dir)):
        # Also patch FileResponse so it doesn't try to guess mimetypes or raise errors
        with patch("app.main.FileResponse") as mock_fr:
            # 1. Normal file
            await serve_spa("app.js")
            assert "app.js" in mock_fr.call_args[0][0]

            # 2. Traversal attempt
            await serve_spa("../dist_secret/secret.txt")
            assert mock_fr.call_args[0][0].endswith("index.html")
