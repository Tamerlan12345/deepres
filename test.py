from fastapi.testclient import TestClient
from app.main import app
import unittest

client = TestClient(app)

# The TestClient urlencodes the path. But `..%2f` might be normalized by httpx inside testclient.
# Instead of using TestClient, we could just call the async function directly to test the logic.

import asyncio
from app.main import serve_spa
from fastapi.responses import FileResponse

async def run_test():
    response = await serve_spa("../dist_secrets/key.txt")
    print(response.path)

if __name__ == "__main__":
    asyncio.run(run_test())
