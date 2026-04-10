import os
import unittest
from fastapi.testclient import TestClient

# Bypass testclient path normalization by calling endpoint directly
import asyncio
from app.main import app

class TestPathTraversal(unittest.IsolatedAsyncioTestCase):
    async def test_path_traversal(self):
        # find the endpoint
        endpoint = next(r for r in app.routes if r.path == '/{full_path:path}').endpoint

        # In a vulnerable version, it will try to access the file
        # In a secure version, it should return index.html for outside paths
        resp = await endpoint(full_path="../test-secrets/secret.txt")
        self.assertTrue(resp.path.endswith("index.html"), f"Expected index.html, got {resp.path}")

if __name__ == '__main__':
    unittest.main()
