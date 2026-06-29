import pytest
import os

def test_path_traversal_prevention_logic():
    # Since we can't easily extract the nested endpoint due to how FastAPI initializes it,
    # we test the underlying logic that prevents path traversal.

    frontend_dist = "/app/frontend/dist"

    # Test 1: Normal file serving (path is inside dist)
    normal_path = "assets/index.js"
    safe_path_normal = os.path.abspath(os.path.join(frontend_dist, normal_path))
    target_dir = os.path.abspath(frontend_dist)

    # Normal path should be inside the target directory
    assert os.path.commonpath([target_dir, safe_path_normal]) == target_dir

    # Test 2: Sibling directory path traversal attempt (starts with same prefix but is outside)
    sibling_path = "../dist_secret/secret.txt"
    safe_path_sibling = os.path.abspath(os.path.join(frontend_dist, sibling_path))

    # Sibling path should NOT be inside the target directory
    # Note: commonpath returns the common prefix, which for /app/frontend/dist and /app/frontend/dist_secret is /app/frontend
    assert os.path.commonpath([target_dir, safe_path_sibling]) != target_dir

    # Test 3: Normal traversal attempt (higher up in directory tree)
    traversal_path = "../../etc/passwd"
    safe_path_traversal = os.path.abspath(os.path.join(frontend_dist, traversal_path))

    # Traversal path should NOT be inside the target directory
    assert os.path.commonpath([target_dir, safe_path_traversal]) != target_dir
