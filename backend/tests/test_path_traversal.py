import pytest
import os
import sys
from unittest.mock import patch

@pytest.mark.asyncio
async def test_path_traversal():
    from app.main import app, frontend_dist

    endpoint = next(r for r in app.routes if getattr(r, "path", None) == '/{full_path:path}').endpoint
    with patch("app.main.FileResponse") as mock_file_response:
        # Should detect traversal and fallback to index.html
        response = await endpoint("../dist-secret/file.txt")
        mock_file_response.assert_called()
        # The argument should end with index.html since it rejected the path
        assert mock_file_response.call_args[0][0].endswith("index.html")

@pytest.mark.asyncio
async def test_safe_path():
    from app.main import app, frontend_dist

    endpoint = next(r for r in app.routes if getattr(r, "path", None) == '/{full_path:path}').endpoint
    with patch("app.main.FileResponse") as mock_file_response:
        with patch("os.path.exists", return_value=True):
            with patch("os.path.isfile", return_value=True):
                # Should accept safe path
                response = await endpoint("assets/index.css")
                mock_file_response.assert_called()
                assert mock_file_response.call_args[0][0].endswith("assets/index.css")
