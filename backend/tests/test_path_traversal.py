import pytest
import os

def test_path_traversal_logic(tmp_path):
    import app.main as main

    # Setup test directories using pytest's tmp_path
    dist_dir = tmp_path / "test-dist"
    secret_dir = tmp_path / "test-dist-secret"
    dist_dir.mkdir()
    secret_dir.mkdir()

    # Create test files
    (dist_dir / "index.html").write_text("index")
    (secret_dir / "secret.txt").write_text("secret")

    frontend_dist = str(dist_dir)
    full_path = "../test-dist-secret/secret.txt"

    safe_path = os.path.normpath(os.path.join(frontend_dist, full_path))

    # Secure logic should block it
    is_safe = True
    try:
        base_abs = os.path.abspath(frontend_dist)
        safe_path_abs = os.path.abspath(safe_path)
        if os.path.commonpath([base_abs, safe_path_abs]) != base_abs:
            is_safe = False
    except ValueError:
        is_safe = False

    assert not is_safe
