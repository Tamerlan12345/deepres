import unittest
from unittest.mock import patch
import os
import sys

sys.path.append(os.getcwd())

class TestPathTraversal(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Create a dummy dist directory so the route is registered
        os.makedirs("frontend/dist", exist_ok=True)
        # Import app here so the route registration sees the directory
        from app.main import app
        self.app = app

        # We need to find the catch-all route.
        # Ensure it exists before testing.
        self.serve_spa_endpoint = None
        for r in app.routes:
            if hasattr(r, 'path') and r.path == '/{full_path:path}':
                self.serve_spa_endpoint = r.endpoint
                break

    async def test_path_traversal_prevention(self):
        """Test that the catch-all route prevents path traversal using commonpath"""

        if not self.serve_spa_endpoint:
            self.skipTest("Catch-all route not registered, skipping test.")

        serve_spa_endpoint = self.serve_spa_endpoint

        # Test 1: Normal path
        with patch('app.main.os.path.exists', return_value=True), \
             patch('app.main.os.path.isfile', return_value=True), \
             patch('app.main.FileResponse') as mock_file_response:

             await serve_spa_endpoint("assets/main.js")

             # The path should end with assets/main.js
             args, _ = mock_file_response.call_args
             self.assertTrue(args[0].endswith(os.path.normpath("assets/main.js")))

        # Test 2: Path traversal attempt
        with patch('app.main.os.path.exists', return_value=True), \
             patch('app.main.os.path.isfile', return_value=True), \
             patch('app.main.FileResponse') as mock_file_response:

             # Attempt to traverse up to a sensitive file
             await serve_spa_endpoint("../../../../etc/passwd")

             # Because of traversal, it should fall back to index.html
             args, _ = mock_file_response.call_args
             self.assertTrue(args[0].endswith("index.html"), "Path traversal was not prevented!")

        # Test 3: Tricky path traversal (same prefix)
        with patch('app.main.os.path.exists', return_value=True), \
             patch('app.main.os.path.isfile', return_value=True), \
             patch('app.main.FileResponse') as mock_file_response:

             # This is why startswith is dangerous (e.g., dist_hacked vs dist)
             await serve_spa_endpoint("../dist_hacked/secret.txt")

             args, _ = mock_file_response.call_args
             self.assertTrue(args[0].endswith("index.html"), "startswith vulnerability was not prevented!")

if __name__ == "__main__":
    unittest.main()
