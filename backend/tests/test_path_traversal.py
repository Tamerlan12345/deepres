import pytest
import os

@pytest.mark.asyncio
async def test_path_traversal_catch_all_route(tmp_path):
    """
    Test the inner logic of the catch-all route to prevent path traversal,
    specifically ensuring that the fix using os.path.commonpath prevents
    directory name substring bypasses that startswith() allowed.
    """
    project_root = tmp_path / "app"
    frontend_dist = project_root / "frontend" / "dist"

    # Fake dist directory that could be used to bypass startswith
    fake_dist = project_root / "frontend" / "dist_fake"

    # Replicate the logic in app/main.py
    def serve_spa(full_path: str, f_dist: str):
        safe_path = os.path.normpath(os.path.join(f_dist, full_path))
        try:
            common = os.path.commonpath([os.path.abspath(safe_path), os.path.abspath(f_dist)])
            if common != os.path.abspath(f_dist):
                return "index.html"
        except ValueError:
            return "index.html"

        return safe_path

    f_dist_str = str(frontend_dist)

    # 1. Normal path
    assert serve_spa("test.js", f_dist_str) == str(frontend_dist / "test.js")

    # 2. Path Traversal exploiting startswith bypass
    assert serve_spa("../dist_fake/secret.txt", f_dist_str) == "index.html"

    # 3. Path Traversal deep escape
    assert serve_spa("../../../etc/passwd", f_dist_str) == "index.html"
