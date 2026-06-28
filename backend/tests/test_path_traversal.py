import pytest
import os
import asyncio
from unittest.mock import patch
from app.main import app

def test_path_traversal_prevention_spa(tmp_path):
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    (dist_dir / "index.html").write_text("index")

    dist_secret_dir = tmp_path / "dist_secret"
    dist_secret_dir.mkdir()
    (dist_secret_dir / "secret.txt").write_text("super secret")

    endpoint = next(r for r in app.routes if hasattr(r, 'path') and r.path == '/{full_path:path}').endpoint

    with patch('app.main.frontend_dist', str(dist_dir)), patch('app.main.FileResponse') as MockFileResponse:
        response = asyncio.run(endpoint(full_path="../dist_secret/secret.txt"))

        args, kwargs = MockFileResponse.call_args
        returned_path = args[0]

        assert "index.html" in returned_path, f"Path traversal succeeded! Returned path: {returned_path}"
        assert "secret.txt" not in returned_path
