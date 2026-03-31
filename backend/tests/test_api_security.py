import unittest
import uuid
import asyncio
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import Base, get_db
from app.models import User, Report, ReportStatus
from app.auth import get_password_hash
from datetime import datetime, timezone

class TestApiSecurity(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db_url = f"sqlite+aiosqlite:///:memory:?cache=shared&v={uuid.uuid4().hex}"
        self.engine = create_async_engine(
            self.db_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine, class_=AsyncSession)

        async def override_get_db():
            async with self.TestingSessionLocal() as session:
                yield session

        app.dependency_overrides[get_db] = override_get_db

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self.client = TestClient(app)

        # Create users
        async with self.TestingSessionLocal() as db:
            # Victim user
            victim_user = User(username="victim", hashed_password=get_password_hash("password"), admin="no")
            db.add(victim_user)

            # Attacker user
            attacker_user = User(username="attacker", hashed_password=get_password_hash("password"), admin="no")
            db.add(attacker_user)

            # Admin user
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
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        app.dependency_overrides.clear()
        await self.engine.dispose()

    def get_token(self, username, password):
        # The login endpoint expects JSON body because it uses Pydantic model UserLogin
        response = self.client.post("/api/login", json={"username": username, "password": password})
        if response.status_code != 200:
            raise Exception(f"Login failed: {response.text}")
        return response.json()["access_token"]

    def test_export_pdf_unauthenticated(self):
        # Without auth, it should fail (currently passes/200, so this test will fail until fixed)
        with patch("app.api.HTML") as mock_html:
            mock_html.return_value.write_pdf.return_value = b"%PDF-1.4..."
            response = self.client.get(f"/api/reports/{self.report_id}/pdf")
            self.assertEqual(response.status_code, 401)

    def test_export_pdf_unauthorized(self):
        # Attacker tries to access victim's report
        token = self.get_token("attacker", "password")
        with patch("app.api.HTML") as mock_html:
            mock_html.return_value.write_pdf.return_value = b"%PDF-1.4..."
            response = self.client.get(
                f"/api/reports/{self.report_id}/pdf",
                headers={"Authorization": f"Bearer {token}"}
            )
            self.assertEqual(response.status_code, 403)

    def test_export_pdf_authorized_owner(self):
        # Victim accesses their own report
        token = self.get_token("victim", "password")
        with patch("app.api.HTML") as mock_html:
            mock_html.return_value.write_pdf.return_value = b"%PDF-1.4..."
            response = self.client.get(
                f"/api/reports/{self.report_id}/pdf",
                headers={"Authorization": f"Bearer {token}"}
            )
            self.assertEqual(response.status_code, 200)

    def test_export_pdf_authorized_admin(self):
        # Admin accesses any report
        token = self.get_token("admin_user", "password")
        with patch("app.api.HTML") as mock_html:
            mock_html.return_value.write_pdf.return_value = b"%PDF-1.4..."
            response = self.client.get(
                f"/api/reports/{self.report_id}/pdf",
                headers={"Authorization": f"Bearer {token}"}
            )
            self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()
