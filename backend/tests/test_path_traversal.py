import unittest
from unittest.mock import patch
import os
from fastapi.testclient import TestClient
from app.main import app

class TestPathTraversal(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # We don't need a real DB or user for these tests
        self.client = TestClient(app)

    @patch('app.main.FileResponse')
    @patch('os.path.exists')
    @patch('os.path.isfile')
    async def test_path_traversal_prevention(self, mock_isfile, mock_exists, mock_file_response):
        """
        Directly call the catch-all endpoint logic to bypass TestClient path normalization
        and ensure directory traversal attempts are securely rejected.
        """
        # We need to bypass the client because TestClient will normalize `..` before it hits FastAPI

        # Find the serve_spa route
        route = next((r for r in app.routes if hasattr(r, 'path') and r.path == '/{full_path:path}'), None)

        # If the route wasn't mounted (e.g. because frontend/dist didn't exist during app startup), skip test
        if not route:
            self.skipTest("SPA route not mounted (frontend/dist directory likely missing during startup). Skipping path traversal test.")

        endpoint = route.endpoint

        # Test traversal
        mock_exists.return_value = True
        mock_isfile.return_value = True

        # Case 1: Traversal attempt (e.g., /../secret.txt)
        response = await endpoint(full_path="../secret.txt")

        # It should return the fallback index.html, not the traversal path
        # The specific path might vary slightly depending on where the test runs,
        # so let's just check that index.html is in the args
        args, kwargs = mock_file_response.call_args
        self.assertTrue(str(args[0]).endswith('index.html'))

        # Case 2: Safe file (e.g., /css/style.css)
        mock_file_response.reset_mock()

        response = await endpoint(full_path="css/style.css")

        args, kwargs = mock_file_response.call_args
        self.assertTrue(str(args[0]).endswith('css/style.css'))

if __name__ == "__main__":
    unittest.main()
