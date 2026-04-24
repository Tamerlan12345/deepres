import pytest
import os
import uuid
from httpx import AsyncClient, ASGITransport

@pytest.fixture(autouse=True)
def setup_frontend_dist():
    """Ensure the frontend/dist directory exists so the StaticFiles mount doesn't fail."""
    dist_dir = "/app/frontend/dist"
    os.makedirs(dist_dir, exist_ok=True)
    index_file = os.path.join(dist_dir, "index.html")
    if not os.path.exists(index_file):
        with open(index_file, "w") as f:
            f.write("<html><body>Mock Index</body></html>")

@pytest.mark.anyio
async def test_path_traversal_prevention():
    """Test that path traversal attempts fallback to index.html securely."""
    # Ensure dist-secrets exists
    secrets_dir = "/app/frontend/dist-secrets"
    os.makedirs(secrets_dir, exist_ok=True)
    secret_file = os.path.join(secrets_dir, "secret.txt")
    with open(secret_file, "w") as f:
        f.write("SUPER SECRET DATA")

    from app.main import serve_spa

    # Simulate a path traversal attack that matches the 'dist' prefix
    response = await serve_spa(full_path="../dist-secrets/secret.txt")

    # Read the file response content
    with open(response.path, "r") as f:
        content = f.read()

    # The response should be index.html, NOT the secret file
    assert "Mock Index" in content
    assert "SUPER SECRET DATA" not in content
