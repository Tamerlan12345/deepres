import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

@pytest.fixture(autouse=True)
def setup_frontend_dist(tmp_path):
    # Ensure directory exists before importing app
    frontend_dist = tmp_path / "frontend" / "dist"
    frontend_dist.mkdir(parents=True)
    (frontend_dist / "index.html").write_text("mock index")

    with patch("app.main.frontend_dist", str(frontend_dist)):
        yield str(frontend_dist)

@pytest.mark.asyncio
async def test_serve_spa_path_traversal(setup_frontend_dist):
    from app.main import app
    from fastapi.responses import FileResponse

    # Extract endpoint
    endpoint = next(r for r in app.routes if r.path == '/{full_path:path}').endpoint

    frontend_dist = setup_frontend_dist
    secret_dir = os.path.dirname(frontend_dist) + "/dist-secrets"
    os.makedirs(secret_dir, exist_ok=True)
    secret_file = os.path.join(secret_dir, "secret.txt")
    with open(secret_file, "w") as f:
        f.write("secret")

    # Path traversal string that uses startswith weakness
    # If full_path is "../dist-secrets/secret.txt", os.path.join(frontend_dist, full_path)
    # resolves to /path/to/frontend/dist/../dist-secrets/secret.txt
    # normpath makes it /path/to/frontend/dist-secrets/secret.txt
    # Which startswith /path/to/frontend/dist (as a string) but not as a path!

    full_path = "../dist-secrets/secret.txt"

    with patch('app.main.FileResponse') as mock_file_response:
        response = await endpoint(full_path=full_path)

        # Expecting index.html to be returned because path traversal should be blocked
        args, kwargs = mock_file_response.call_args
        assert args[0] == os.path.join(frontend_dist, "index.html")
