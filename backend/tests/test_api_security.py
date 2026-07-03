import unittest
import uuid
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import app.main
from app.database import Base, get_db
from app.models import User, Report, ReportStatus
from app.auth import get_password_hash
from datetime import datetime, timezone

class TestApiSecurity(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        db_url = f"sqlite+aiosqlite:///:memory:?cache=shared&v={uuid.uuid4().hex}"
        self.engine = create_async_engine(
            db_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine, class_=AsyncSession)

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async def override_get_db():
            async with self.TestingSessionLocal() as session:
                yield session

        app.main.app.dependency_overrides[get_db] = override_get_db

        import app.database
        self.original_engine = app.database.engine
        self.original_sessionmaker = app.database.AsyncSessionLocal
        app.database.engine = self.engine
        app.database.AsyncSessionLocal = self.TestingSessionLocal

        self.client = TestClient(app.main.app)

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

            # Refresh victim user
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

        import app.database
        app.database.engine = self.original_engine
        app.database.AsyncSessionLocal = self.original_sessionmaker
        app.main.app.dependency_overrides.clear()

    def get_token(self, username, password):
        response = self.client.post("/api/login", json={"username": username, "password": password})
        if response.status_code != 200:
            raise Exception(f"Login failed: {response.text}")
        return response.json()["access_token"]

    def test_export_pdf_unauthenticated(self):
        with patch("app.api.HTML") as mock_html:
            mock_html.return_value.write_pdf.return_value = b"%PDF-1.4..."
            response = self.client.get(f"/api/reports/{self.report_id}/pdf")
            self.assertEqual(response.status_code, 401)

    def test_export_pdf_unauthorized(self):
        token = self.get_token("attacker", "password")
        with patch("app.api.HTML") as mock_html:
            mock_html.return_value.write_pdf.return_value = b"%PDF-1.4..."
            response = self.client.get(
                f"/api/reports/{self.report_id}/pdf",
                headers={"Authorization": f"Bearer {token}"}
            )
            self.assertEqual(response.status_code, 403)

    def test_export_pdf_authorized_owner(self):
        token = self.get_token("victim", "password")
        with patch("app.api.HTML") as mock_html:
            mock_html.return_value.write_pdf.return_value = b"%PDF-1.4..."
            response = self.client.get(
                f"/api/reports/{self.report_id}/pdf",
                headers={"Authorization": f"Bearer {token}"}
            )
            self.assertEqual(response.status_code, 200)

    def test_export_pdf_authorized_admin(self):
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
