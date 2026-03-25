import unittest
import string
import random
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import Base, get_db
from app.api import get_current_user
from app.models import User

SQLALCHEMY_DATABASE_URL = f"sqlite+aiosqlite:///:memory:?cache=shared&v={''.join(random.choices(string.ascii_letters, k=10))}"

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

class TestDoSPrevention(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.client = TestClient(app)

    async def asyncTearDown(self):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    def test_login_length_validation(self):
        response = self.client.post("/api/login", json={"username": "a" * 100, "password": "password"})
        self.assertEqual(response.status_code, 422)

    def test_report_create_length_validation(self):
        mock_user = User(id=1, username="testuser", admin="no")
        app.dependency_overrides[get_current_user] = lambda: mock_user

        response = self.client.post("/api/reports", json={"query": "a" * 2000})
        self.assertEqual(response.status_code, 422)

        del app.dependency_overrides[get_current_user]

if __name__ == "__main__":
    unittest.main()
