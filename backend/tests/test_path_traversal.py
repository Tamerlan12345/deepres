import pytest
import os
from fastapi.responses import FileResponse
from unittest.mock import patch

# Create a local frontend/dist directory so the route is registered when app is imported
@pytest.fixture(scope="session", autouse=True)
def setup_frontend_dist():
    dist_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "frontend", "dist")
    os.makedirs(dist_dir, exist_ok=True)
    yield
    # Cleanup not strictly necessary in a temporary run

@pytest.mark.asyncio
async def test_path_traversal_prevention(tmp_path):
    # Now it's safe to import app
    from app.main import app

    dummy_dist = tmp_path / "frontend" / "dist"
    dummy_dist.mkdir(parents=True, exist_ok=True)

    (dummy_dist / "index.html").write_text("dummy index")

    secret_file = tmp_path / "frontend" / "dist_secret.txt"
    secret_file.write_text("secret content")

    spa_endpoint = next(
        route.endpoint for route in app.routes
        if hasattr(route, 'path') and route.path == "/{full_path:path}"
    )

    with patch("app.main.frontend_dist", str(dummy_dist)):
        with patch("app.main.FileResponse") as MockFileResponse:
            await spa_endpoint("../dist_secret.txt")

            MockFileResponse.assert_called_once()
            called_path = MockFileResponse.call_args[0][0]
            assert called_path == os.path.join(str(dummy_dist), "index.html")
