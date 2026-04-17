import unittest
import os
from unittest.mock import patch, MagicMock
import sys

# Add backend to path if not running with pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# We need to bypass the standard FastApi test client which automatically normalizes paths
import pytest
from app.main import app

class TestPathTraversalSecurity(unittest.IsolatedAsyncioTestCase):

    @patch('app.main.FileResponse')
    @patch('app.main.os.path.exists')
    @patch('app.main.os.path.isfile')
    async def test_startswith_path_traversal_prevention(self, mock_isfile, mock_exists, mock_fileresponse):
        # Setup mocks
        mock_exists.return_value = True
        mock_isfile.return_value = True

        # Get the actual endpoint function
        serve_spa = next(r for r in app.routes if r.path == '/{full_path:path}').endpoint

        # Attack payload: navigating out of dist but still starting with dist (e.g. dist.txt)
        malicious_path = "../dist.txt"

        # Call the endpoint directly
        await serve_spa(full_path=malicious_path)

        # Verify it fell back to index.html instead of returning the malicious path
        mock_fileresponse.assert_called_with(os.path.join(app.routes[-1].endpoint.__globals__['frontend_dist'], "index.html"))

    @patch('app.main.FileResponse')
    @patch('app.main.os.path.exists')
    @patch('app.main.os.path.isfile')
    async def test_normal_file_access(self, mock_isfile, mock_exists, mock_fileresponse):
        # Setup mocks
        mock_exists.return_value = True
        mock_isfile.return_value = True

        serve_spa = next(r for r in app.routes if r.path == '/{full_path:path}').endpoint

        normal_path = "assets/index.js"

        await serve_spa(full_path=normal_path)

        expected_path = os.path.normpath(os.path.join(app.routes[-1].endpoint.__globals__['frontend_dist'], normal_path))
        mock_fileresponse.assert_called_with(expected_path)

if __name__ == '__main__':
    unittest.main()
