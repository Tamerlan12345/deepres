import unittest
import os
import shutil
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Mock frontend_dist before importing app
with patch('os.path.exists') as mock_exists:
    mock_exists.return_value = True
    from app.main import app, frontend_dist

class TestPathTraversalPrevention(unittest.TestCase):
    def setUp(self):
        # We need a stable test directory structure to test the handler directly.
        # FastAPI's TestClient resolves path components like '..' before the request hits the handler,
        # so we can't test path traversal purely via TestClient requests.
        self.client = TestClient(app)

        # Set up a fake filesystem layout for testing
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_fs"))
        self.frontend_dist_mock = os.path.join(self.base_dir, "dist")
        self.frontend_dist_secret = os.path.join(self.base_dir, "dist-secret")

        os.makedirs(self.frontend_dist_mock, exist_ok=True)
        os.makedirs(self.frontend_dist_secret, exist_ok=True)

        # Create some files
        self.index_file = os.path.join(self.frontend_dist_mock, "index.html")
        self.secret_file = os.path.join(self.frontend_dist_secret, "secret.txt")
        self.asset_file = os.path.join(self.frontend_dist_mock, "app.js")

        with open(self.index_file, "w") as f:
            f.write("mock index")

        with open(self.secret_file, "w") as f:
            f.write("super secret info")

        with open(self.asset_file, "w") as f:
            f.write("console.log('test');")

    def tearDown(self):
        # Cleanup fake filesystem
        if os.path.exists(self.base_dir):
            shutil.rmtree(self.base_dir)

    def test_path_traversal_startswith_bypass(self):
        """
        Tests that an attempt to access `dist-secret` from `dist` is blocked.
        This tests the specific vulnerability where `safe_path.startswith(frontend_dist)`
        would fail if frontend_dist was `/app/dist` and path was `/app/dist-secret/secret.txt`.
        """
        from app.main import serve_spa
        import asyncio

        # Test directly with the function, mocking frontend_dist
        with patch('app.main.frontend_dist', self.frontend_dist_mock):
            # Attempt to access dist-secret by going up one directory
            # If the request was /../dist-secret/secret.txt, full_path would be ../dist-secret/secret.txt

            # Use asyncio to run the async serve_spa function
            loop = asyncio.get_event_loop()

            # The full_path would resolve to something outside of dist but starting with the same prefix
            full_path = "../dist-secret/secret.txt"

            # When calling serve_spa directly, it will return a FileResponse
            response = loop.run_until_complete(serve_spa(full_path))

            # The fix should return index.html instead of secret.txt
            self.assertEqual(response.path, os.path.join(self.frontend_dist_mock, "index.html"))

    def test_valid_file_access(self):
        """
        Tests that accessing a valid file within the dist directory still works.
        """
        from app.main import serve_spa
        import asyncio

        with patch('app.main.frontend_dist', self.frontend_dist_mock):
            loop = asyncio.get_event_loop()

            full_path = "app.js"
            response = loop.run_until_complete(serve_spa(full_path))

            # Should return the requested file
            self.assertEqual(response.path, os.path.join(self.frontend_dist_mock, "app.js"))

if __name__ == "__main__":
    unittest.main()