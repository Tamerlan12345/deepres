import os
import unittest
from unittest.mock import patch
import asyncio

class TestPathTraversal(unittest.TestCase):
    def test_path_traversal_blocked(self):
        # Ensure the frontend/dist directory exists so the route is registered
        if not os.path.exists("frontend/dist"):
            os.makedirs("frontend/dist", exist_ok=True)
            with open("frontend/dist/index.html", "w") as f:
                f.write("test")

        # Import after creating directory so route is registered
        from app.main import app

        # Find the catch-all route endpoint
        endpoint = next(r for r in app.routes if hasattr(r, 'path') and r.path == '/{full_path:path}').endpoint

        full_path = "../dist-secret/secret.txt"

        # Need to create event loop properly
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        with patch('os.path.exists') as mock_exists, patch('os.path.isfile') as mock_isfile, patch('app.main.FileResponse') as mock_file_response:
            mock_exists.return_value = True
            mock_isfile.return_value = True

            response = loop.run_until_complete(endpoint(full_path=full_path))

            called_path = mock_file_response.call_args[0][0]

            # The path traversal is blocked, so it should return the fallback index.html
            self.assertTrue(called_path.endswith("index.html"), f"Path traversal allowed! Returned: {called_path}")

if __name__ == "__main__":
    unittest.main()
