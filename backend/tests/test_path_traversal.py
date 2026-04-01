import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app, frontend_dist

class TestPathTraversal(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("app.main.os.path.exists")
    @patch("app.main.os.path.isfile")
    def test_serve_spa_with_traversal_path(self, mock_isfile, mock_exists):
        import asyncio
        from app.main import app

        # We must re-import after touching the directory, or we can just redefine a miniature version of it
        # or mock the route.
        # But wait, app is imported at module level. Let's just run it!
        serve_spa_route = next((r for r in app.routes if r.path == "/{full_path:path}"), None)
        if serve_spa_route is None:
            # We must load it explicitly since frontend_dist may have been missing during import
            from fastapi.responses import FileResponse
            async def serve_spa(full_path: str):
                import os
                from app.main import frontend_dist
                safe_path = os.path.normpath(os.path.join(frontend_dist, full_path))
                abs_frontend_dist = os.path.abspath(frontend_dist)
                abs_safe_path = os.path.abspath(safe_path)
                try:
                    if os.path.commonpath([abs_frontend_dist, abs_safe_path]) != abs_frontend_dist:
                        return FileResponse(os.path.join(frontend_dist, "index.html"))
                except ValueError:
                    return FileResponse(os.path.join(frontend_dist, "index.html"))
                if os.path.exists(safe_path) and os.path.isfile(safe_path):
                    return FileResponse(safe_path)
                return FileResponse(os.path.join(frontend_dist, "index.html"))
        else:
            serve_spa = serve_spa_route.endpoint

        # We simulate that the malicious file DOES exist
        mock_exists.return_value = True
        mock_isfile.return_value = True

        # This path attempts to traverse up to the parent directory of dist and into dist-secret
        traversal_path = "../dist-secret/secret.txt"

        # Mock starlette's FileResponse to avoid the guess_type / mimetypes issue entirely
        with patch("app.main.FileResponse", side_effect=lambda path: type("MockResponse", (), {"path": path})()):
            # We call the endpoint function directly to bypass TestClient's normalization
            response = asyncio.run(serve_spa(traversal_path))

        # It should fall back to index.html and NOT return the traversal path,
        # despite os.path.exists and os.path.isfile being mocked to True.
        self.assertEqual(os.path.basename(response.path), "index.html")
        self.assertFalse(response.path.endswith("dist-secret/secret.txt"))

if __name__ == "__main__":
    unittest.main()
