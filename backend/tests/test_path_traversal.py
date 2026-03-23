import unittest
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app, frontend_dist

class TestPathTraversal(unittest.TestCase):
    def setUp(self):
        # Create dummy frontend_dist and index.html if it doesn't exist
        os.makedirs(frontend_dist, exist_ok=True)
        self.index_path = os.path.join(frontend_dist, "index.html")
        with open(self.index_path, "w") as f:
            f.write("<html><body>Mock SPA</body></html>")

        # Create a directory that shares the prefix 'dist' but is outside
        self.dist_secrets_path = os.path.join(os.path.dirname(frontend_dist), "dist_secrets")
        os.makedirs(self.dist_secrets_path, exist_ok=True)
        self.secret_file_path = os.path.join(self.dist_secrets_path, "secret.txt")
        with open(self.secret_file_path, "w") as f:
            f.write("SUPER_SECRET_DATA")

        self.client = TestClient(app)

    def tearDown(self):
        # Clean up created files
        try:
            os.remove(self.secret_file_path)
            os.rmdir(self.dist_secrets_path)
        except OSError:
            pass

    def test_prefix_path_traversal(self):
        # Attempt to access ../dist_secrets/secret.txt which normalizes to /app/frontend/dist_secrets/secret.txt
        # If vulnerable, startswith("/app/frontend/dist") will pass.

        # Use url encoding for path traversal to bypass testclient normalization
        response = self.client.get("/%2e%2e/dist_secrets/secret.txt")

        # Should return the fallback SPA index.html, not the secret content
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("SUPER_SECRET_DATA", response.text)
        self.assertIn("Mock SPA", response.text)

    def test_standard_path_traversal(self):
        # Attempt to go up and read backend config
        response = self.client.get("/%2e%2e/%2e%2e/backend/app/config.py")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("class Settings", response.text)
        self.assertIn("Mock SPA", response.text)

if __name__ == "__main__":
    unittest.main()
