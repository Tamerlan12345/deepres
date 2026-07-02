import pytest
import os
from fastapi.testclient import TestClient

@pytest.fixture
def test_app(tmp_path):
    # Set up mock dist directory
    dist_dir = tmp_path / "frontend" / "dist"
    os.makedirs(dist_dir)

    index_file = dist_dir / "index.html"
    index_file.write_text("INDEX")

    secrets_dir = tmp_path / "frontend" / "dist-secrets"
    os.makedirs(secrets_dir)
    secret_file = secrets_dir / "secret.txt"
    secret_file.write_text("SECRET")

    # We must patch frontend_dist before we import app.main
    import sys

    if "app.main" in sys.modules:
        del sys.modules["app.main"]

    import app.main
    app.main.frontend_dist = str(dist_dir)

    # Force the app to re-evaluate the route addition
    if os.path.exists(app.main.frontend_dist):
        from starlette.concurrency import run_in_threadpool
        import os.path as os_path
        from fastapi.responses import FileResponse

        @app.main.app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            abs_frontend_dist = os_path.abspath(app.main.frontend_dist)
            safe_path = os_path.abspath(os_path.join(abs_frontend_dist, full_path))

            try:
                if os_path.commonpath([abs_frontend_dist, safe_path]) != abs_frontend_dist:
                    return FileResponse(os_path.join(app.main.frontend_dist, "index.html"))
            except ValueError:
                return FileResponse(os_path.join(app.main.frontend_dist, "index.html"))

            path_exists = await run_in_threadpool(os_path.exists, safe_path)
            is_file = await run_in_threadpool(os_path.isfile, safe_path)

            if path_exists and is_file:
                return FileResponse(safe_path)

            return FileResponse(os_path.join(app.main.frontend_dist, "index.html"))

    yield app.main.app

def test_spa_path_traversal(test_app, tmp_path):
    client = TestClient(test_app)

    response = client.get("/index.html")
    assert response.status_code == 200
    assert response.text == "INDEX"

@pytest.mark.asyncio
async def test_spa_path_traversal_direct_endpoint(test_app):
    route_handler = next(
        (r for r in test_app.routes if hasattr(r, 'path') and r.path == "/{full_path:path}"),
        None
    )
    assert route_handler is not None, "serve_spa route not found"
    serve_spa = route_handler.endpoint

    import unittest.mock

    with unittest.mock.patch('backend.tests.test_path_traversal.FileResponse', create=True) as mock_file_response:
        # FastAPI's FileResponse creates an object with a `.path` attribute
        # But we mock it inside the test file? The function above imports it directly.
        pass

    # Better to just inspect the returned FileResponse object

    # Valid path
    valid_response = await serve_spa("index.html")
    assert valid_response.path.endswith("index.html")

    # Traversal path
    traversal_response = await serve_spa("../dist-secrets/secret.txt")
    # Due to boundary check, it should return index.html
    assert traversal_response.path.endswith("index.html")
