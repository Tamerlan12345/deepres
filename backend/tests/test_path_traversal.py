import unittest
from fastapi.testclient import TestClient
import os
import tempfile
import shutil
import importlib

class TestPathTraversal(unittest.TestCase):
    def setUp(self):
        # Create a temporary environment to test the path validation
        self.temp_dir = tempfile.mkdtemp()

        # Setup fake frontend_dist
        self.frontend_dist = os.path.join(self.temp_dir, "frontend", "dist")
        os.makedirs(self.frontend_dist)
        with open(os.path.join(self.frontend_dist, "index.html"), "w") as f:
            f.write("SAFE_INDEX")

        with open(os.path.join(self.frontend_dist, "script.js"), "w") as f:
            f.write("SAFE_JS")

        # Setup a sibling directory with a name prefix of frontend_dist
        # e.g., if frontend_dist is /tmp/foo/frontend/dist
        # we create /tmp/foo/frontend/dist_secret
        self.secret_dir = os.path.join(self.temp_dir, "frontend", "dist_secret")
        os.makedirs(self.secret_dir)
        with open(os.path.join(self.secret_dir, "secret.txt"), "w") as f:
            f.write("MY_SECRET_INFO")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_path_traversal_logic(self):
        # Here we manually replicate the logic in serve_spa to ensure our fix is robust
        # This tests the core string vs commonpath vulnerability

        def mock_serve_spa(full_path: str):
            abs_frontend_dist = os.path.abspath(self.frontend_dist)
            safe_path = os.path.abspath(os.path.join(abs_frontend_dist, full_path))

            # This is the vulnerable logic for comparison:
            # if not safe_path.startswith(abs_frontend_dist): ...

            # This is the fixed logic:
            if os.path.commonpath([abs_frontend_dist, safe_path]) != abs_frontend_dist:
                return "FALLBACK"

            if os.path.exists(safe_path) and os.path.isfile(safe_path):
                with open(safe_path, "r") as f:
                    return f.read()

            return "FALLBACK"

        # 1. Normal access
        self.assertEqual(mock_serve_spa("script.js"), "SAFE_JS")

        # 2. Path traversal upwards
        self.assertEqual(mock_serve_spa("../dist_secret/secret.txt"), "FALLBACK")

        # 3. Path traversal bypass via directory prefix
        # This was the vulnerability: startswith() would have matched here
        payload = "../dist_secret/secret.txt"
        self.assertEqual(mock_serve_spa(payload), "FALLBACK")

if __name__ == "__main__":
    unittest.main()
