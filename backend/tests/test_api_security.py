import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.models import User, Report, ReportStatus
from app.auth import get_password_hash
from datetime import datetime, timezone
import uuid

# Provide unique db URL for each test file per memories
SQLALCHEMY_DATABASE_URL = f"sqlite+aiosqlite:///:memory:?cache=shared&v={uuid.uuid4().hex}"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

import app.database
app.database.engine = engine
app.database.AsyncSessionLocal = TestingSessionLocal

from app.main import app
app.dependency_overrides[get_db] = lambda: TestingSessionLocal()

class TestApiSecurity(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Create users
        async with TestingSessionLocal() as db:
            victim_user = User(username="victim", hashed_password=get_password_hash("password"), admin="no")
            db.add(victim_user)

            attacker_user = User(username="attacker", hashed_password=get_password_hash("password"), admin="no")
            db.add(attacker_user)

            admin_user = User(username="admin_user", hashed_password=get_password_hash("password"), admin="yes")
            db.add(admin_user)

            await db.commit()

            await db.refresh(victim_user)
            self.victim_id = victim_user.id

            report = Report(
                query="test query",
                status=ReportStatus.COMPLETED,
                id_users=self.victim_id,
                result_json={"summary": "Secret Summary", "detailed_analysis": "Secret Analysis"},
                created_at=datetime.now(timezone.utc)
            )
            db.add(report)
            await db.commit()
            await db.refresh(report)
            self.report_id = report.id

    async def asyncTearDown(self):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def get_token(self, username, password):
        from httpx import AsyncClient, ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/login", json={"username": username, "password": password})
            if response.status_code != 200:
                raise Exception(f"Login failed: {response.text}")
            return response.json()["access_token"]

    async def test_export_pdf_unauthenticated(self):
        from httpx import AsyncClient, ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with patch("app.api.HTML") as mock_html:
                mock_html.return_value.write_pdf.return_value = b"%PDF-1.4..."
                response = await client.get(f"/api/reports/{self.report_id}/pdf")
                self.assertEqual(response.status_code, 401)

    async def test_export_pdf_unauthorized(self):
        token = await self.get_token("attacker", "password")
        from httpx import AsyncClient, ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with patch("app.api.HTML") as mock_html:
                mock_html.return_value.write_pdf.return_value = b"%PDF-1.4..."
                response = await client.get(
                    f"/api/reports/{self.report_id}/pdf",
                    headers={"Authorization": f"Bearer {token}"}
                )
                self.assertEqual(response.status_code, 403)

    async def test_export_pdf_authorized_owner(self):
        token = await self.get_token("victim", "password")
        from httpx import AsyncClient, ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with patch("app.api.HTML") as mock_html:
                mock_html.return_value.write_pdf.return_value = b"%PDF-1.4..."
                response = await client.get(
                    f"/api/reports/{self.report_id}/pdf",
                    headers={"Authorization": f"Bearer {token}"}
                )
                self.assertEqual(response.status_code, 200)

    async def test_export_pdf_authorized_admin(self):
        token = await self.get_token("admin_user", "password")
        from httpx import AsyncClient, ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with patch("app.api.HTML") as mock_html:
                mock_html.return_value.write_pdf.return_value = b"%PDF-1.4..."
                response = await client.get(
                    f"/api/reports/{self.report_id}/pdf",
                    headers={"Authorization": f"Bearer {token}"}
                )
                self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()
