import pytest
import os
from fastapi.testclient import TestClient
from app.main import app, frontend_dist

client = TestClient(app)

@pytest.fixture(autouse=True, scope="session")
def setup_frontend_dist():
    os.makedirs(frontend_dist, exist_ok=True)
    index_path = os.path.join(frontend_dist, "index.html")
    with open(index_path, "w") as f:
        f.write("<html>index</html>")

    test_file_path = os.path.join(frontend_dist, "testfile.txt")
    with open(test_file_path, "w") as f:
        f.write("testcontent")

    attack_dir = frontend_dist + "_attack"
    os.makedirs(attack_dir, exist_ok=True)
    attack_file = os.path.join(attack_dir, "malicious.txt")
    with open(attack_file, "w") as f:
        f.write("secretcontent")

def test_path_traversal_prevention():
    endpoint = next(r for r in app.routes if r.path == '/{full_path:path}').endpoint

    import asyncio

    async def run_test():
        # Valid file inside frontend_dist
        res = await endpoint("testfile.txt")
        assert res.path.endswith(os.path.join(frontend_dist, "testfile.txt"))

        # Attack file in frontend_dist_attack
        # The frontend_dist check would incorrectly pass with `startswith`
        # Because `frontend_dist_attack` starts with `frontend_dist`
        # Since our code now uses os.path.commonpath, it should return index.html
        res2 = await endpoint("../frontend/dist_attack/malicious.txt")
        assert res2.path.endswith(os.path.join(frontend_dist, "index.html"))

        # Test standard traversal trying to break out
        res3 = await endpoint("../../etc/passwd")
        assert res3.path.endswith(os.path.join(frontend_dist, "index.html"))

    asyncio.run(run_test())
