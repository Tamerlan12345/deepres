import pytest
from app.main import app
import os
import asyncio

@pytest.mark.asyncio
async def test_path_traversal_serve_spa(tmp_path):
    # Mock frontend_dist
    mock_dist = tmp_path / "dist"
    mock_dist.mkdir(parents=True, exist_ok=True)
    index_file = mock_dist / "index.html"
    index_file.write_text("index content")

    # Mock another directory that shares prefix
    mock_dist_secret = tmp_path / "dist_secret"
    mock_dist_secret.mkdir(parents=True, exist_ok=True)
    secret_file = mock_dist_secret / "passwd"
    secret_file.write_text("secret content")

    # Find the SPA serve route
    spa_route = next((r for r in app.routes if getattr(r, 'path', '') == '/{full_path:path}'), None)
    assert spa_route is not None, "Catch-all route not found"
    endpoint = spa_route.endpoint

    # Temporarily patch main.frontend_dist
    import app.main as main
    original_dist = main.frontend_dist
    main.frontend_dist = str(mock_dist)

    try:
        # Test valid path
        response_valid = await endpoint(full_path="index.html")
        assert response_valid.path == str(index_file)

        # Test classical path traversal
        response_traversal = await endpoint(full_path="../dist/index.html")
        # Should fallback to index.html due to not matching commonpath or correctly navigating out
        assert response_traversal.path == str(index_file)

        # Test prefix bypass (e.g. dist_secret starting with dist)
        response_bypass = await endpoint(full_path="../dist_secret/passwd")
        # Ensure the response is serving index.html (fallback) instead of the secret file
        assert response_bypass.path == str(index_file)
        assert response_bypass.path != str(secret_file)

    finally:
        main.frontend_dist = original_dist
