import unittest
import os
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import Base, get_db

# Setup in-memory database
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

class TestPathTraversal(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self.client = TestClient(app)

        # Ensure a dummy index.html exists so we don't get 500s when fallback happens
        os.makedirs("frontend/dist", exist_ok=True)
        if not os.path.exists("frontend/dist/index.html"):
            with open("frontend/dist/index.html", "w") as f:
                f.write("<html><body>Dummy Index</body></html>")

        # Create a dummy secret file outside the dist dir
        os.makedirs("frontend/dist_secrets", exist_ok=True)
        with open("frontend/dist_secrets/secret.txt", "w") as f:
            f.write("SUPER_SECRET_DATA")

    async def asyncTearDown(self):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        # Cleanup dummy files
        if os.path.exists("frontend/dist_secrets/secret.txt"):
            os.remove("frontend/dist_secrets/secret.txt")
        if os.path.exists("frontend/dist_secrets"):
            os.rmdir("frontend/dist_secrets")

    def test_path_traversal_using_url_encoding(self):
        # We use %2e%2e%2f to bypass TestClient/httpx normalization of ..
        # Requesting /%2e%2e/dist_secrets/secret.txt
        # Translates to ../dist_secrets/secret.txt relative to frontend_dist
        response = self.client.get("/%2e%2e/dist_secrets/secret.txt")

        # The request should fallback to index.html and NOT return the secret content
        self.assertEqual(response.status_code, 200)

        # Verify the secret was not leaked
        self.assertNotIn("SUPER_SECRET_DATA", response.text)

if __name__ == "__main__":
    unittest.main()
