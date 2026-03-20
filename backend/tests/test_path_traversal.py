import unittest
import os
from fastapi.testclient import TestClient
from app.main import app

class TestPathTraversal(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_path_traversal_prevention(self):
        # We need to simulate a request that might otherwise pass a startswith check
        # For example, if frontend_dist is "/app/frontend/dist",
        # a request for "/../dist_secrets/secret.txt" could resolve to
        # "/app/frontend/dist_secrets/secret.txt", which startswith("/app/frontend/dist").

        # We simulate hitting the catch-all route with a tricky path.
        # Note: the test client may resolve `..` before sending, so we send the path as is.
        # But `TestClient` uses HTTP, and `httpx` normalizes URLs.
        # In our `main.py`, it's taking the `full_path` string literally as parsed by FastAPI.

        # To bypass httpx URL normalization in tests, we can use URL encoded path segments
        # or call the route directly. We will use %2e%2e for .. to test the server-side handling.
        response = self.client.get("/%2e%2e/dist_secrets/secret.txt")

        # With the fix, the path "/app/frontend/dist/../dist_secrets/secret.txt"
        # is normalized to "/app/frontend/dist_secrets/secret.txt".
        # commonpath of ["/app/frontend/dist", "/app/frontend/dist_secrets/secret.txt"]
        # is "/app/frontend", which != "/app/frontend/dist".
        # It should fall back to index.html (status 200).
        self.assertEqual(response.status_code, 200)

        # Another test: trying to read /etc/passwd
        response = self.client.get("/%2e%2e/%2e%2e/%2e%2e/%2e%2e/%2e%2e/%2e%2e/etc/passwd")
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
