import unittest
import os
import asyncio
from unittest.mock import patch, MagicMock
from app.main import app

class TestPathTraversal(unittest.IsolatedAsyncioTestCase):
    async def test_path_traversal_prevention(self):
        # Create a dummy index.html to ensure the route is registered
        dummy_dist = os.path.join(os.path.dirname(__file__), '../../frontend/dist')
        os.makedirs(dummy_dist, exist_ok=True)
        with open(os.path.join(dummy_dist, 'index.html'), 'w') as f:
            f.write('dummy')

        # Find the route endpoint directly to bypass TestClient URL normalization
        serve_spa_endpoint = next(r for r in app.routes if getattr(r, 'path', None) == '/{full_path:path}').endpoint

        with patch('app.main.FileResponse') as MockFileResponse:
            # We want to test that traversing UP and into a differently named directory
            # (which shares a prefix) doesn't work.
            # Assume base_dir is /app/frontend/dist
            # Attacker tries to access: ../dist-secrets/config.json
            # Previous logic (startswith) would allow this because:
            # /app/frontend/dist-secrets/config.json startswith /app/frontend/dist

            # The full_path input from path parameter
            malicious_path = "../dist-secrets/config.json"

            # Call the endpoint directly
            await serve_spa_endpoint(full_path=malicious_path)

            # Verify FileResponse was called with index.html, NOT the malicious path
            MockFileResponse.assert_called_once()
            called_path = MockFileResponse.call_args[0][0]

            self.assertTrue(called_path.endswith("index.html"))
            self.assertNotIn("dist-secrets", called_path)

if __name__ == '__main__':
    unittest.main()
